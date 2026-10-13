from app.database import SessionLocal
from app.models import Opportunity, Organization
from sqlalchemy import select


def test_demo_session_and_workspace_switching_are_membership_scoped(client):
    session = client.get("/api/session")
    assert session.status_code == 200
    assert session.json()["active_workspace"]["name"] == "DataNova SAS"
    workspaces = client.get("/api/workspaces").json()
    assert {item["name"] for item in workspaces} == {"DataNova SAS", "MP AI Consulting"}
    forbidden = client.get("/api/session", headers={"X-Workspace-Id": "not-a-membership"})
    assert forbidden.status_code == 403

    professional = client.get(
        "/api/professionals/me", headers={"X-Demo-User": "user-2e6ef0f9@example.test"}
    )
    assert professional.status_code == 200
    assert professional.json()["profile_strength"] == 91


def test_viewer_cannot_create_work_post(client):
    response = client.post(
        "/api/work-posts",
        headers={"X-Demo-User": "user-5179d8ae@example.test"},
        json={
            "post_type": "EXPERT_REQUEST",
            "title": "Restricted manager action",
            "summary": "This valid payload must still be rejected by server-side RBAC.",
        },
    )
    assert response.status_code == 403


def test_professional_marketplace_application_is_private_to_post_owner(client):
    posts = client.get("/api/work-posts", headers={"X-Demo-User": "user-2e6ef0f9@example.test"}).json()
    tender_post = next(item for item in posts if item["contingent_on_award"])
    assert tender_post["opportunity_title"] == "Hospital data platform modernization"
    assert "Matched Cybersecurity" in tender_post["match_reasons"]
    application = client.post(
        f"/api/work-posts/{tender_post['id']}/applications",
        headers={"X-Demo-User": "user-2e6ef0f9@example.test"},
        json={"note": "Interested in the synthetic bid project."},
    )
    assert application.status_code == 201
    assert (
        client.post(
            f"/api/work-posts/{tender_post['id']}/applications",
            headers={"X-Demo-User": "user-2e6ef0f9@example.test"},
            json={},
        ).status_code
        == 409
    )
    own_applicants = client.get(f"/api/work-posts/{tender_post['id']}/applications")
    assert own_applicants.status_code == 200
    assert own_applicants.json()[0]["professional_name"] == "Elena Martin"
    with SessionLocal() as db:
        other_workspace = db.scalar(
            select(Organization).where(Organization.slug == "mp-ai-consulting")
        )
        assert other_workspace is not None
    cross_tenant = client.get(
        f"/api/work-posts/{tender_post['id']}/applications",
        headers={"X-Workspace-Id": other_workspace.id},
    )
    assert cross_tenant.status_code == 404


def test_tender_to_team_recommendations_and_draft(client):
    with SessionLocal() as db:
        opportunity = db.scalar(
            select(Opportunity).where(Opportunity.external_id == "DEMO-2026-003")
        )
        assert opportunity is not None
    gaps = client.get(f"/api/opportunities/{opportunity.id}/capability-gaps")
    assert gaps.status_code == 200
    assert len(gaps.json()) == 4
    recommendations = client.get(f"/api/opportunities/{opportunity.id}/team-recommendations")
    assert recommendations.status_code == 200
    body = recommendations.json()
    assert body["current_coverage"] == 76
    elena = next(item for item in body["candidates"] if item["name"] == "Elena Martin")
    assert any(item["name"] == "CyberSec SAS" for item in body["candidates"])
    created = client.post(
        f"/api/opportunities/{opportunity.id}/bid-team",
        json={
            "name": "Healthcare data platform bid team",
            "members": [
                {
                    "candidate_type": elena["candidate_type"],
                    "candidate_id": elena["candidate_id"],
                }
            ],
        },
    )
    assert created.status_code == 201
    assert created.json()["proposed_coverage"] == 96


def test_admin_route_is_independently_protected(client):
    assert client.get("/api/admin/summary").status_code == 403
    admin = client.get("/api/admin/summary", headers={"X-Demo-User": "user-e3945303@example.test"})
    assert admin.status_code == 200
    assert admin.json()["users"] >= 4
