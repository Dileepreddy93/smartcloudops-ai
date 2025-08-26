def test_prometheus_metrics_endpoint(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert r.headers.get("Content-Type", "").startswith("text/plain; version=0.0.4")
