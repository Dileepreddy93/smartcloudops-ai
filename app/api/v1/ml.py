from typing import Any, Dict

from flask import Blueprint, request
from prometheus_client import Counter, REGISTRY

from app.core.ml_engine.secure_inference import (
    SecureMLInferenceEngine,
    get_secure_inference_engine,
)
from app.utils.response import error_response, success_response

bp = Blueprint("ml", __name__)

# Clear any existing metrics to avoid duplication
try:
    REGISTRY.unregister(REGISTRY._names_to_collectors.get("ml_prediction_requests_total"))
except (KeyError, ValueError):
    pass

ML_PREDICTION_REQUESTS = Counter(
    "ml_prediction_requests_total",
    "Total ML prediction requests",
    ["status"],
)


@bp.get("/ml/health")
def ml_health():
    engine = get_secure_inference_engine()
    health = engine.health_check()
    return success_response(data=health)


@bp.post("/ml/predict")
def ml_predict():
    json: Dict[str, Any] = request.get_json(silent=True) or {}
    metrics = json.get("metrics")
    if not isinstance(metrics, dict):
        return error_response(message="Invalid metrics payload", status_code=400)

    user_id = request.headers.get("X-User-Id")
    engine = get_secure_inference_engine()
    # Prefer higher-level API if available
    if hasattr(engine, "predict_anomaly"):
        result = engine.predict_anomaly(metrics=metrics, user_id=user_id)
    else:
        result = engine.predict(metrics=metrics)

    # If engine returns an error structure, treat as 400 to callers
    if isinstance(result, dict) and result.get("error"):
        ML_PREDICTION_REQUESTS.labels(status="error").inc()
        return error_response(message=result.get("error"), status_code=400)

    ML_PREDICTION_REQUESTS.labels(status="success").inc()
    return success_response(data=result)


@bp.get("/ml/metrics")
def ml_metrics():
    engine = get_secure_inference_engine()
    health = engine.health_check()
    data = {
        "status": health.get("status"),
        "metrics": health.get("metrics", {}),
        "model_info": health.get("model_info", {}),
    }
    return success_response(data=data)
