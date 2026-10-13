def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_company_read_and_update_recalculate(client):
    company = client.get("/api/company").json()
    assert company["company_name"] == "DataNova SAS"
    company["preferred_geographies"] = ["Hauts-de-France"]
    for key in ["id", "organization_id", "created_at", "updated_at"]:
        company.pop(key)
    response = client.put(f"/api/company/{client.get('/api/company').json()['id']}", json=company)
    assert response.status_code == 200
    recalculation = client.post("/api/opportunities/recalculate-matches")
    assert recalculation.status_code == 200
    assert recalculation.json()["recalculated"] == 24


def test_company_rejects_inverted_contract_range(client):
    company = client.get("/api/company").json()
    company["preferred_contract_min"] = 200_000
    company["preferred_contract_max"] = 100_000
    for key in ["id", "organization_id", "created_at", "updated_at"]:
        company.pop(key)
    response = client.put(f"/api/company/{client.get('/api/company').json()['id']}", json=company)
    assert response.status_code == 422


def test_listing_filtering_and_pagination(client):
    response = client.get("/api/opportunities?page=1&page_size=5&min_match_score=65")
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) <= 5
    assert all(item["match"]["total_score"] >= 65 for item in body["items"])
    assert all(item["is_demo"] for item in body["items"])
    filtered = client.get("/api/opportunities?source=DEMO&category=Data")
    assert filtered.status_code == 200
    searched = client.get("/api/opportunities?q=knowledge")
    assert searched.status_code == 200
    assert any("knowledge" in item["title"].lower() for item in searched.json()["items"])


def test_opportunity_detail_and_status(client):
    opportunity = client.get("/api/opportunities?page_size=1").json()["items"][0]
    detail = client.get(f"/api/opportunities/{opportunity['id']}")
    assert detail.status_code == 200
    assert detail.json()["match"]["scoring_version"] == "v0.1-deterministic"
    qualification = client.get(f"/api/opportunities/{opportunity['id']}/qualification")
    assert qualification.status_code == 200
    assert qualification.json()["decision"] in {"GO", "CONDITIONAL GO", "REVIEW", "NO-GO"}
    patched = client.patch(
        f"/api/opportunities/{opportunity['id']}/status", json={"status": "reviewing"}
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "reviewing"


def test_dashboard_and_buyers(client):
    summary = client.get("/api/dashboard/summary")
    assert summary.status_code == 200
    assert summary.json()["active_opportunities"] == 24
    buyers = client.get("/api/buyers")
    assert buyers.status_code == 200
    assert len(buyers.json()) == 8
    buyer_id = buyers.json()[0]["id"]
    assert client.get(f"/api/buyers/{buyer_id}/opportunities").status_code == 200


def test_pipeline_add_update_and_activity(client):
    pipeline = client.get("/api/pipeline")
    assert pipeline.status_code == 200
    assert len(pipeline.json()) == 3
    candidate = next(
        item
        for item in client.get("/api/opportunities?page_size=100").json()["items"]
        if item["id"] not in {row["opportunity_id"] for row in pipeline.json()}
    )
    created = client.post(
        "/api/pipeline",
        json={"opportunity_id": candidate["id"], "stage": "review", "probability": 25},
    )
    assert created.status_code == 201
    assert created.json()["value"] is not None
    duplicate = client.post(
        "/api/pipeline", json={"opportunity_id": candidate["id"], "stage": "review"}
    )
    assert duplicate.status_code == 409
    updated = client.patch(
        f"/api/pipeline/{created.json()['id']}",
        json={"stage": "qualified", "next_action": "Confirm bid team"},
    )
    assert updated.status_code == 200
    assert updated.json()["stage"] == "qualified"
    summary = client.get("/api/pipeline/summary")
    assert summary.status_code == 200
    assert summary.json()["item_count"] == 4
    activity = client.get("/api/activity")
    assert any(event["action"] == "pipeline.updated" for event in activity.json())


def test_saved_search_lifecycle_and_notifications(client):
    created = client.post(
        "/api/saved-searches",
        json={"name": "High-value AI", "filters": {"q": "AI", "min_value": 500000}},
    )
    assert created.status_code == 201
    assert (
        client.post(
            "/api/saved-searches",
            json={"name": "High-value AI", "filters": {"q": "AI"}},
        ).status_code
        == 409
    )
    searches = client.get("/api/saved-searches")
    assert searches.status_code == 200
    assert any(search["name"] == "High-value AI" for search in searches.json())
    assert client.delete(f"/api/saved-searches/{created.json()['id']}").status_code == 204
    notifications = client.get("/api/notifications")
    assert notifications.status_code == 200
    assert all("Synthetic" in row["message"] for row in notifications.json())
