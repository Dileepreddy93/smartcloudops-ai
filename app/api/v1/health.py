from flask import Blueprint

from app.utils.response import make_response, now_iso
from app.core.ml_engine.secure_inference import get_secure_inference_engine


bp = Blueprint("health", __name__)


@bp.get("/status")
def status():
    # DTO data
    engine = get_secure_inference_engine()
    ml_health = engine.health_check()
    data = {
        "message": "OK",
        "timestamp": now_iso(),
        "ml": {"status": ml_health.get("status"), "metrics": ml_health.get("metrics", {})},
    }
    # Compatibility fields for existing consumers
    compat = {"status": "healthy"}
    return make_response(data=data, compatibility=compat)


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


