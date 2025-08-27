from flask import Blueprint, Response

bp = Blueprint("logs", __name__)


@bp.get("/logs")
def logs():
    # Simple logs endpoint that returns recent log content
    try:
        # Try to read from log file if it exists
        import os

        log_file = "/tmp/smartcloudops_api.log"
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                content = f.read()
        else:
            content = "No logs available"

        # Basic sanitization: limit to recent content
        if content and len(content) > 20000:
            content = content[-20000:]
        return Response(content or "No logs available", mimetype="text/plain")
    except Exception:
        return Response("Logs temporarily unavailable", mimetype="text/plain")
