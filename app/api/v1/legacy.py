#!/usr/bin/env python3
"""
SmartCloudOps AI - Legacy API
=============================

Legacy endpoints for backward compatibility.
"""

from flask import Blueprint, jsonify, request

# Create blueprint
bp = Blueprint("legacy", __name__, url_prefix="/api/v1/legacy")


@bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for legacy service."""
    return jsonify(
        {
            "status": "healthy",
            "service": "legacy",
            "message": "Legacy service is running",
        }
    )


@bp.route("/status", methods=["GET"])
def get_status():
    """Get legacy system status."""
    return jsonify(
        {
            "status": "success",
            "data": {
                "version": "1.0.0",
                "deprecated": True,
                "message": "This endpoint is deprecated",
            },
        }
    )
