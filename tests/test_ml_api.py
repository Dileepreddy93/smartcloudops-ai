def test_ml_health_endpoint(client):
    res = client.get("/ml/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert isinstance(data["data"], dict)
    assert "status" in data["data"]


def test_ml_predict_invalid_payload(client):
    res = client.post("/ml/predict", json={"bad": 1})
    assert res.status_code == 400
    data = res.get_json()
    assert data["status"] == "error"


def test_ml_predict_valid_payload(client, monkeypatch):
    # Monkeypatch engine to deterministic output
    class DummyEngine:
        def health_check(self):
            return {"status": "healthy"}

        def predict_anomaly(self, metrics=None, user_id=None):
            return {"anomaly": False, "confidence": 0.9, "metrics": metrics or {}}

    # Patch the function actually used inside the endpoint module
    monkeypatch.setattr("app.api.v1.ml.get_secure_inference_engine", lambda: DummyEngine())

    res = client.post(
        "/ml/predict",
        json={
            "metrics": {
                "cpu_usage": 10.0,
                "memory_usage": 20.0,
                "load_1m": 0.1,
                "disk_usage": 5.0,
            }
        },
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["data"]["anomaly"] is False
    assert "confidence" in data["data"]


def test_ml_metrics_endpoint(client, monkeypatch):
    class DummyEngine:
        def health_check(self):
            return {
                "status": "healthy",
                "metrics": {"prediction_count": 1},
                "model_info": {"type": "iforest"},
            }

    monkeypatch.setattr("app.api.v1.ml.get_secure_inference_engine", lambda: DummyEngine())

    res = client.get("/ml/metrics")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["data"]["status"] == "healthy"
    assert "metrics" in data["data"]
    assert "model_info" in data["data"]
