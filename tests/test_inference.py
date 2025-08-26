def test_secure_inference_health_basic():
    # Prefer secure engine since it's self-contained and works with JSON configs
    from app.core.ml_engine.secure_inference import get_secure_inference_engine

    # Ensure known model file exists in repo (ml_models/simple_real_model.json)
    engine = get_secure_inference_engine()
    health = engine.health_check()
    assert "status" in health
    assert health["status"] in {"healthy", "degraded", "unhealthy", "failed"}


def test_secure_inference_prediction_with_valid_metrics():
    from app.core.ml_engine.secure_inference import get_secure_inference_engine

    engine = get_secure_inference_engine()
    result = engine.predict_anomaly(
        metrics={
            "cpu_usage": 50.0,
            "memory_usage": 40.0,
            "load_1m": 0.8,
            "disk_usage": 30.0,
        },
        user_id="pytest",
    )

    assert isinstance(result, dict)
    assert "anomaly" in result
    assert "confidence" in result


def test_secure_inference_prediction_handles_bad_input():
    from app.core.ml_engine.secure_inference import get_secure_inference_engine

    engine = get_secure_inference_engine()
    result = engine.predict_anomaly(
        metrics={
            "cpu_usage": "NaN",
            "memory_usage": None,
            "load_1m": float("inf"),
            # disk_usage omitted on purpose
        },
        user_id="pytest",
    )

    assert isinstance(result, dict)
    assert "anomaly" in result
    assert "confidence" in result
