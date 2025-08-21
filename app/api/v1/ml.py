from __future__ import annotations

from typing import Any, Dict

from flask import Blueprint, request
from prometheus_client import Counter

from app.core.ml_engine.secure_inference import get_secure_inference_engine
from app.utils.response import make_response


bp = Blueprint("ml", __name__)

ML_PREDICTION_REQUESTS = Counter(
    "ml_prediction_requests_total",
    "Total ML prediction requests",
    ["status"],
)


@bp.get("/ml/health")
def ml_health():
    engine = get_secure_inference_engine()
    health = engine.health_check()
    return make_response(data=health)


@bp.post("/ml/predict")
def ml_predict():
    json: Dict[str, Any] = request.get_json(silent=True) or {}
    metrics = json.get("metrics")
    if not isinstance(metrics, dict):
        return make_response(error="Invalid metrics payload", http_status=400)

    user_id = request.headers.get("X-User-Id")
    engine = get_secure_inference_engine()
    result = engine.predict_anomaly(metrics=metrics, user_id=user_id)

    # If engine returns an error structure, treat as 400 to callers
    if isinstance(result, dict) and result.get("error"):
        ML_PREDICTION_REQUESTS.labels(status="error").inc()
        return make_response(error=result.get("error"), http_status=400)

    ML_PREDICTION_REQUESTS.labels(status="success").inc()
    return make_response(data=result)


@bp.get("/ml/metrics")
def ml_metrics():
    engine = get_secure_inference_engine()
    health = engine.health_check()
    data = {
        "status": health.get("status"),
        "metrics": health.get("metrics", {}),
        "model_info": health.get("model_info", {}),
    }
    return make_response(data=data)


