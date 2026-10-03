"""Integration tests covering the browser page and public API contract."""


def test_home_and_health(client):
    assert client.get("/").status_code == 200
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_analysis_and_cache(client):
    first = client.post("/api/v1/analyses", json={"username": "octocat"})
    assert first.status_code == 201
    assert first.json()["data"]["totals"]["stars"] == 12
    assert first.json()["data"]["languages"][0]["name"] == "Python"

    second = client.post("/api/v1/analyses", json={"username": "octocat"})
    assert second.status_code == 201
    assert second.json()["cached"] is True
    assert second.json()["id"] == first.json()["id"]
    assert client.fake_github.calls == 1


def test_history_get_export_and_delete(client):
    created = client.post("/api/v1/analyses", json={"username": "octocat"}).json()
    analysis_id = created["id"]
    assert client.get("/api/v1/history").json()[0]["username"] == "octocat"
    assert client.get(f"/api/v1/analyses/{analysis_id}").status_code == 200
    csv_response = client.get(f"/api/v1/analyses/{analysis_id}/export.csv")
    assert csv_response.status_code == 200
    assert "language_percentage,Python,80.0" in csv_response.text
    assert client.delete(f"/api/v1/history/{analysis_id}").status_code == 204
    assert client.get(f"/api/v1/analyses/{analysis_id}").status_code == 404


def test_username_validation(client):
    response = client.post("/api/v1/analyses", json={"username": "-invalid-"})
    assert response.status_code == 422
