from uuid import uuid4

from app.config import get_settings


def _without_demo_header(client) -> None:
    client.headers.pop("X-Demo-User", None)


def test_unauthenticated_request_never_defaults_to_demo_user(client, monkeypatch):
    _without_demo_header(client)
    monkeypatch.setenv("DEMO_MODE", "false")
    get_settings.cache_clear()
    try:
        response = client.get("/api/session", headers={"X-Demo-User": "user-d9853303@example.test"})
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "authentication_required"
    finally:
        monkeypatch.setenv("DEMO_MODE", "true")
        get_settings.cache_clear()


def test_company_signup_creates_owner_session_and_requires_csrf(client):
    _without_demo_header(client)
    email = f"owner-{uuid4()}@example.com"
    response = client.post(
        "/api/auth/signup",
        json={
            "account_type": "COMPANY",
            "email": email,
            "password": "PrivatePilot1234",
            "display_name": "Pilot Owner",
            "company_name": "Pilot Company",
        },
    )
    assert response.status_code == 201
    assert client.cookies.get("pros_session")
    session = client.get("/api/session").json()
    assert session["email"] == email
    assert session["active_workspace"]["role"] == "OWNER"
    assert session["platform_role"] == "USER"
    assert session["onboarding_required"] is True
    assert client.post("/api/auth/logout").status_code == 403
    csrf = client.cookies.get("pros_csrf")
    assert client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf}).status_code == 204
    assert client.get("/api/session").status_code == 401


def test_professional_signup_has_no_company_permissions_and_can_login(client):
    _without_demo_header(client)
    email = f"professional-{uuid4()}@example.com"
    password = "Professional1234"
    created = client.post(
        "/api/auth/signup",
        json={"account_type": "PROFESSIONAL", "email": email, "password": password, "display_name": "Pilot Professional"},
    )
    assert created.status_code == 201
    session = client.get("/api/session").json()
    assert session["has_professional_profile"] is True
    assert session["active_workspace"] is None
    assert session["workspaces"] == []
    assert client.get("/api/company").status_code == 403
    csrf = client.cookies.get("pros_csrf")
    client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf})
    assert client.post("/api/auth/login", json={"email": email, "password": "wrong-password"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": email, "password": password}).status_code == 204
    assert client.get("/api/session").status_code == 200


def test_workspace_switch_rejects_non_membership_and_admin_is_independent(client):
    _without_demo_header(client)
    assert client.post("/api/auth/demo-login", json={"persona": "company"}).status_code == 204
    csrf = client.cookies.get("pros_csrf")
    forbidden = client.post(
        "/api/session/workspace?workspace_id=not-a-membership",
        headers={"X-CSRF-Token": csrf},
    )
    assert forbidden.status_code == 403
    assert client.get("/api/admin/summary").status_code == 403


def test_duplicate_email_and_weak_password_are_rejected(client):
    _without_demo_header(client)
    payload = {"account_type": "PROFESSIONAL", "email": f"duplicate-{uuid4()}@example.com", "password": "ValidPassword123", "display_name": "Duplicate User"}
    assert client.post("/api/auth/signup", json=payload).status_code == 201
    assert client.post("/api/auth/signup", json=payload).status_code == 409
    payload["email"] = f"weak-{uuid4()}@example.com"
    payload["password"] = "onlylettersxx"
    assert client.post("/api/auth/signup", json=payload).status_code == 422
