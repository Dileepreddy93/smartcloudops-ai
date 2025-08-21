def test_home_route(client):
    res = client.get("/")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["message"] == "SmartCloudOps AI Platform"


def test_status_route(client):
    res = client.get("/status")
    assert res.status_code == 200
    data = res.get_json()
    assert data.get("status") in {"healthy", "unhealthy", "stale"}

