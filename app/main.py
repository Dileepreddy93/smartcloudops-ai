#!/usr/bin/env python3
"""
SmartCloudOps AI - Main Flask Application
"""

from datetime import datetime

from flask import Flask, jsonify, request, Response


def get_status_info() -> dict:
    return {
        "status": "healthy",
        "message": "OK",
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_logs_data() -> str:
    # Simple log reader (path mocked in tests)
    log_path = "logs/app.log"
    if not hasattr(get_logs_data, "_cache"):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                get_logs_data._cache = f.read()
        except Exception:
            get_logs_data._cache = ""
    return get_logs_data._cache


def get_chat_response(user_query: str) -> str:
    # Thin wrapper over the ChatOps service to preserve compatibility
    from app.services import chatops_service
    return chatops_service.chat(user_query)


def create_app():
    app = Flask(__name__)

    # Register v1 blueprints
    try:
        from app.api.v1 import health as health_v1
        from app.api.v1 import chatops as chatops_v1
        from app.api.v1 import logs as logs_v1
        from app.api.v1 import ml as ml_v1
        from app.api.v1 import metrics as metrics_v1

        app.register_blueprint(health_v1.bp)
        app.register_blueprint(chatops_v1.bp)
        app.register_blueprint(logs_v1.bp)
        app.register_blueprint(ml_v1.bp)
        app.register_blueprint(metrics_v1.bp)
    except Exception:
        # Fallback to legacy inline routes if blueprints fail to import
        @app.route("/")
        def home():
            return jsonify(
                {
                    "status": "success",
                    "message": "SmartCloudOps AI Platform",
                    "version": "1.0.0",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        @app.route("/status")
        def status():
            return jsonify(get_status_info())

        @app.route("/query", methods=["POST"])
        def query():
            data = request.get_json(silent=True) or {}
            user_query = data.get("query")
            if not user_query or not isinstance(user_query, str):
                return Response("Invalid request", status=400)

            try:
                ai_response = get_chat_response(user_query)
            except Exception:
                return Response("Invalid request", status=400)

            return jsonify({"response": ai_response})

        @app.route("/logs")
        def logs():
            content = get_logs_data()
            return Response(content, mimetype="text/plain")

    return app


# Create app instance for Gunicorn
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
