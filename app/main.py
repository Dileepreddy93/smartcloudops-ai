#!/usr/bin/env python3
"""
SmartCloudOps AI - Main Flask Application
"""

from flask import Flask, jsonify
from datetime import datetime

def create_app():
    app = Flask(__name__)
    
    @app.route("/")
    def home():
        return jsonify({
            "status": "success",
            "message": "SmartCloudOps AI Platform",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @app.route("/status")
    def status():
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)
