from flask import Blueprint

from app.utils.response import success_response, build_success_response
from datetime import datetime, timezone
from app.core.ml_engine.secure_inference import SecureMLInferenceEngine


bp = Blueprint("health", __name__)


@bp.get("/status")
def status():
    # DTO data
    engine = SecureMLInferenceEngine()
    ml_health = engine.health_check()
    data = {
        "message": "OK",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ml": {
            "status": ml_health.get("status"),
            "metrics": ml_health.get("metrics", {}),
        },
    }
    # Merge compatibility fields into the response
    response_data = {
        "status": "healthy",  # Compatibility field
        "message": "OK",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ml": {
            "status": ml_health.get("status"),
            "metrics": ml_health.get("metrics", {}),
        },
    }
    return success_response(data=response_data)


@bp.get("/")
def home():
    # Legacy home response expected by tests/clients
    from datetime import datetime

    return {
        "status": "success",
        "message": "SmartCloudOps AI Platform",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }
