from flask import Blueprint, Response


bp = Blueprint("logs", __name__)


@bp.get("/logs")
def logs():
    # Delegate to existing helper in app.main to retain behavior and tests
    from app.main import get_logs_data

    content = get_logs_data()
    # Basic sanitization: limit to recent content
    if content and len(content) > 20000:
        content = content[-20000:]
    return Response(content or "", mimetype="text/plain")
