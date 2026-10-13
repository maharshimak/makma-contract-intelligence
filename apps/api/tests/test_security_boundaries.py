from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from app.config import Settings
from app.models import (
    CompanyProfile,
    MembershipRole,
    Notification,
    Organization,
    OrganizationMember,
    SavedSearch,
    User,
    UserSession,
)
from conftest import TestingSession
from sqlalchemy import select


def _anonymous(client) -> None:
    client.headers.pop("X-Demo-User", None)
    client.cookies.clear()


def test_production_rejects_demo_and_insecure_cookie_configuration() -> None:
    with pytest.raises(RuntimeError, match="DEMO_MODE"):
        Settings(
            environment="production",
            demo_mode=True,
            session_cookie_secure=True,
            cors_origins="https://app.example.com",
        ).validate_runtime_safety()
    with pytest.raises(RuntimeError, match="SESSION_COOKIE_SECURE"):
        Settings(
            environment="production",
            demo_mode=False,
            session_cookie_secure=False,
            cors_origins="https://app.example.com",
        ).validate_runtime_safety()


def test_invalid_and_expired_sessions_are_rejected(client) -> None:
    _anonymous(client)
    client.cookies.set("pros_session", "invalid-session-token")
    assert client.get("/api/session").status_code == 401
    client.cookies.clear()
    email = f"expired-{uuid4()}@example.com"
    assert (
        client.post(
            "/api/auth/signup",
            json={
                "account_type": "PROFESSIONAL",
                "email": email,
                "password": "ExpiredSession123",
                "display_name": "Expired Session",
            },
        ).status_code
        == 201
    )
    with TestingSession() as db:
        user = db.scalar(select(User).where(User.email == email))
        assert user is not None
        session = db.scalar(select(UserSession).where(UserSession.user_id == user.id))
        assert session is not None
        session.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        db.commit()
    assert client.get("/api/session").status_code == 401


def test_admin_access_matrix_uses_platform_role_only(client) -> None:
    _anonymous(client)
    assert client.get("/api/admin/summary").status_code == 401
    for email in ("user-2e6ef0f9@example.test", "user-5179d8ae@example.test", "user-d9853303@example.test"):
        client.cookies.clear()
        assert client.get("/api/admin/summary", headers={"X-Demo-User": email}).status_code == 403
    allowed = client.get("/api/admin/summary", headers={"X-Demo-User": "user-e3945303@example.test"})
    assert allowed.status_code == 200


def test_signup_rejects_platform_role_payload_and_owner_stays_platform_user(client) -> None:
    _anonymous(client)
    payload = {
        "account_type": "COMPANY",
        "email": f"payload-{uuid4()}@example.com",
        "password": "PayloadSafety123",
        "display_name": "Safe Owner",
        "company_name": "Safe Tenant",
        "platform_role": "SUPERADMIN",
    }
    assert client.post("/api/auth/signup", json=payload).status_code == 422
    payload.pop("platform_role")
    assert client.post("/api/auth/signup", json=payload).status_code == 201
    body = client.get("/api/session").json()
    assert body["active_workspace"]["role"] == "OWNER"
    assert body["platform_role"] == "USER"


def test_removed_membership_and_cross_tenant_private_resources_are_blocked(client) -> None:
    with TestingSession() as db:
        viewer = db.scalar(select(User).where(User.email == "user-5179d8ae@example.test"))
        datanova = db.scalar(select(Organization).where(Organization.slug == "datanova-sas"))
        assert viewer and datanova
        other_user = User(email=f"tenant-b-{uuid4()}@example.com", display_name="Tenant B Owner")
        other_org = Organization(name="Tenant B", slug=f"tenant-b-{uuid4()}")
        db.add_all([other_user, other_org])
        db.flush()
        db.add(
            OrganizationMember(
                organization_id=other_org.id, user_id=other_user.id, role=MembershipRole.owner
            )
        )
        other_company = CompanyProfile(organization_id=other_org.id, company_name="Tenant B")
        db.add(other_company)
        other_search = SavedSearch(
            organization_id=other_org.id, name="Tenant B private", filters={}
        )
        db.add(other_search)
        db.commit()
        other_company_id = other_company.id
        other_search_id = other_search.id
        membership = db.scalar(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == datanova.id,
                OrganizationMember.user_id == viewer.id,
            )
        )
        assert membership is not None
        membership.status = "REMOVED"
        db.commit()
    try:
        assert (
            client.get("/api/company", headers={"X-Demo-User": "user-5179d8ae@example.test"}).status_code
            == 403
        )
        assert (
            client.get(
                f"/api/company/{other_company_id}",
                headers={"X-Demo-User": "user-d9853303@example.test"},
            ).status_code
            == 404
        )
        assert (
            client.delete(
                f"/api/saved-searches/{other_search_id}",
                headers={"X-Demo-User": "user-d9853303@example.test"},
            ).status_code
            == 404
        )
    finally:
        with TestingSession() as db:
            membership = db.scalar(
                select(OrganizationMember)
                .join(User, OrganizationMember.user_id == User.id)
                .where(User.email == "user-5179d8ae@example.test")
            )
            assert membership is not None
            membership.status = "ACTIVE"
            db.commit()


def test_targeted_notifications_are_private_and_org_notifications_are_shared(client) -> None:
    with TestingSession() as db:
        owner = db.scalar(select(User).where(User.email == "user-d9853303@example.test"))
        viewer = db.scalar(select(User).where(User.email == "user-5179d8ae@example.test"))
        org = db.scalar(select(Organization).where(Organization.slug == "datanova-sas"))
        assert owner and viewer and org
        marker = str(uuid4())
        db.add_all(
            [
                Notification(
                    organization_id=org.id,
                    user_id=owner.id,
                    type="SECURITY",
                    title=f"target-{marker}",
                    message="Owner only",
                ),
                Notification(
                    organization_id=org.id,
                    user_id=None,
                    type="WORKSPACE",
                    title=f"org-{marker}",
                    message="Organization wide",
                ),
            ]
        )
        db.commit()
    owner_titles = {
        item["title"]
        for item in client.get(
            "/api/notifications", headers={"X-Demo-User": "user-d9853303@example.test"}
        ).json()
    }
    viewer_titles = {
        item["title"]
        for item in client.get(
            "/api/notifications", headers={"X-Demo-User": "user-5179d8ae@example.test"}
        ).json()
    }
    assert f"target-{marker}" in owner_titles and f"target-{marker}" not in viewer_titles
    assert f"org-{marker}" in owner_titles and f"org-{marker}" in viewer_titles


def test_incomplete_workspace_exposes_onboarding_and_can_be_completed(client) -> None:
    with TestingSession() as db:
        owner = db.scalar(select(User).where(User.email == "user-d9853303@example.test"))
        assert owner
        org = Organization(name="Onboarding Tenant", slug=f"onboarding-{uuid4()}")
        db.add(org)
        db.flush()
        db.add(
            OrganizationMember(organization_id=org.id, user_id=owner.id, role=MembershipRole.owner)
        )
        db.commit()
        org_id = org.id
    session = client.get(
        "/api/session", headers={"X-Demo-User": "user-d9853303@example.test", "X-Workspace-Id": org_id}
    )
    assert session.status_code == 200 and session.json()["onboarding_required"] is True
    completed = client.post(
        "/api/company/onboarding",
        headers={"X-Demo-User": "user-d9853303@example.test", "X-Workspace-Id": org_id},
        json={
            "company_name": "Onboarding Tenant",
            "description": "A legitimate setup record.",
            "service_categories": ["Data"],
        },
    )
    assert completed.status_code == 201


def test_untrusted_origin_is_rejected_on_login_and_signup(client) -> None:
    _anonymous(client)
    headers = {"Origin": "https://evil.example"}
    assert (
        client.post(
            "/api/auth/login",
            headers=headers,
            json={"email": "nobody@example.com", "password": "NotARealPassword1"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/auth/signup",
            headers=headers,
            json={
                "account_type": "PROFESSIONAL",
                "email": f"origin-{uuid4()}@example.com",
                "password": "OriginSafety123",
                "display_name": "Origin Test",
            },
        ).status_code
        == 403
    )
