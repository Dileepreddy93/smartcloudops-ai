def test_home_and_status(client):
    r = client.get("/")
    assert r.status_code == 200
    data = r.get_json()
    assert data["message"] == "SmartCloudOps AI Platform"

    r = client.get("/status")
    assert r.status_code == 200
    payload = r.get_json()
    # Endpoint may return top-level status as "healthy" (compat) or DTO "success"
    assert payload.get("status") in {"success", "healthy"}
    assert payload["data"]["message"] == "OK"


def test_query_validation_and_success(client, monkeypatch):
    # Invalid
    r = client.post("/query", json={"bad": 1})
    assert r.status_code == 400

    # Success via mocking
    from app.services import chatops_service

    monkeypatch.setattr(chatops_service, "chat", lambda q: "Mocked Answer")
    r = client.post("/query", json={"query": "cpu?"})
    assert r.status_code == 200
    assert r.get_json()["response"] == "Mocked Answer"


