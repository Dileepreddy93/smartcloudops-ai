#!/usr/bin/env python3
"""
SmartCloudOps AI - API Documentation
===================================

OpenAPI/Swagger documentation for all API endpoints.
"""

from flask import Blueprint, jsonify
from flask_swagger_ui import get_swaggerui_blueprint

# Swagger configuration
SWAGGER_URL = "/api/docs"
API_URL = "/api/swagger.json"

# Create swagger blueprint
swagger_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL, API_URL, config={"app_name": "SmartCloudOps AI API"}
)

# API documentation blueprint
docs_blueprint = Blueprint("docs", __name__)


@docs_blueprint.route("/api/swagger.json")
def create_swagger_spec():
    """Generate OpenAPI/Swagger specification."""

    swagger_spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "SmartCloudOps AI API",
            "description": "AI-powered cloud operations platform with real-time anomaly detection and automated remediation",
            "version": "3.2.0",
            "contact": {
                "name": "SmartCloudOps AI Support",
                "email": "support@smartcloudops.ai",
            },
            "license": {"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
        },
        "servers": [
            {"url": "https://api.smartcloudops.ai", "description": "Production server"},
            {"url": "http://localhost:5000", "description": "Development server"},
        ],
        "security": [{"ApiKeyAuth": []}, {"BearerAuth": []}],
        "paths": {
            "/health": {
                "get": {
                    "summary": "Health Check",
                    "description": "Get system health status and component information",
                    "tags": ["System"],
                    "responses": {
                        "200": {
                            "description": "System health information",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/HealthResponse"
                                    }
                                }
                            },
                        },
                        "500": {
                            "description": "Internal server error",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            },
                        },
                    },
                }
            },
            "/api/v1/ml/predict": {
                "post": {
                    "summary": "ML Anomaly Detection",
                    "description": "Predict anomalies using ML models",
                    "tags": ["ML"],
                    "security": [{"ApiKeyAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/MLPredictionRequest"
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "ML prediction result",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/MLPredictionResponse"
                                    }
                                }
                            },
                        },
                        "400": {
                            "description": "Invalid request",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            },
                        },
                        "401": {
                            "description": "Unauthorized",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            },
                        },
                    },
                }
            },
            "/api/v1/ml/health": {
                "get": {
                    "summary": "ML Service Health",
                    "description": "Get ML service health and model information",
                    "tags": ["ML"],
                    "responses": {
                        "200": {
                            "description": "ML service health",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/MLHealthResponse"
                                    }
                                }
                            },
                        }
                    },
                }
            },
            "/api/v1/chatops/query": {
                "post": {
                    "summary": "ChatOps Query",
                    "description": "Process natural language queries for system operations",
                    "tags": ["ChatOps"],
                    "security": [{"ApiKeyAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ChatOpsRequest"
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "ChatOps response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ChatOpsResponse"
                                    }
                                }
                            },
                        },
                        "400": {
                            "description": "Invalid request",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            },
                        },
                    },
                }
            },
            "/api/v1/metrics": {
                "get": {
                    "summary": "Get System Metrics",
                    "description": "Retrieve current system metrics and performance data",
                    "tags": ["Monitoring"],
                    "security": [{"ApiKeyAuth": []}],
                    "responses": {
                        "200": {
                            "description": "System metrics",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/MetricsResponse"
                                    }
                                }
                            },
                        }
                    },
                }
            },
            "/api/v1/remediation/actions": {
                "post": {
                    "summary": "Execute Remediation Action",
                    "description": "Execute automated remediation actions",
                    "tags": ["Remediation"],
                    "security": [{"ApiKeyAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/RemediationRequest"
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Remediation result",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/RemediationResponse"
                                    }
                                }
                            },
                        }
                    },
                }
            },
        },
        "components": {
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                    "description": "API key for authentication",
                },
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "JWT token for authentication",
                },
            },
            "schemas": {
                "HealthResponse": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["success", "error"],
                            "description": "Response status",
                        },
                        "message": {
                            "type": "string",
                            "description": "Response message",
                        },
                        "timestamp": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Response timestamp",
                        },
                        "data": {
                            "type": "object",
                            "properties": {
                                "overall_status": {
                                    "type": "string",
                                    "enum": ["healthy", "degraded", "unhealthy"],
                                    "description": "Overall system health",
                                },
                                "components": {
                                    "type": "object",
                                    "properties": {
                                        "database": {
                                            "type": "boolean",
                                            "description": "Database connectivity",
                                        },
                                        "ml_service": {
                                            "type": "boolean",
                                            "description": "ML service status",
                                        },
                                        "cache": {
                                            "type": "boolean",
                                            "description": "Cache service status",
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
                "MLPredictionRequest": {
                    "type": "object",
                    "required": ["metrics"],
                    "properties": {
                        "metrics": {
                            "type": "object",
                            "properties": {
                                "cpu_usage": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 100,
                                    "description": "CPU usage percentage",
                                },
                                "memory_usage": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 100,
                                    "description": "Memory usage percentage",
                                },
                                "disk_usage": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 100,
                                    "description": "Disk usage percentage",
                                },
                                "network_io": {
                                    "type": "number",
                                    "minimum": 0,
                                    "description": "Network I/O in MB/s",
                                },
                                "load_1m": {
                                    "type": "number",
                                    "minimum": 0,
                                    "description": "1-minute load average",
                                },
                                "load_5m": {
                                    "type": "number",
                                    "minimum": 0,
                                    "description": "5-minute load average",
                                },
                                "load_15m": {
                                    "type": "number",
                                    "minimum": 0,
                                    "description": "15-minute load average",
                                },
                                "response_time": {
                                    "type": "number",
                                    "minimum": 0,
                                    "description": "Response time in milliseconds",
                                },
                            },
                        }
                    },
                },
                "MLPredictionResponse": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["success", "error"],
                            "description": "Response status",
                        },
                        "message": {
                            "type": "string",
                            "description": "Response message",
                        },
                        "timestamp": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Response timestamp",
                        },
                        "data": {
                            "type": "object",
                            "properties": {
                                "prediction": {
                                    "type": "object",
                                    "properties": {
                                        "is_anomaly": {
                                            "type": "boolean",
                                            "description": "Whether anomaly was detected",
                                        },
                                        "anomaly_score": {
                                            "type": "number",
                                            "description": "Anomaly detection score",
                                        },
                                        "confidence": {
                                            "type": "number",
                                            "minimum": 0,
                                            "maximum": 1,
                                            "description": "Prediction confidence",
                                        },
                                        "model_version": {
                                            "type": "string",
                                            "description": "ML model version used",
                                        },
                                    },
                                },
                                "input_metrics": {
                                    "type": "object",
                                    "description": "Input metrics used for prediction",
                                },
                            },
                        },
                    },
                },
                "ChatOpsRequest": {
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language query",
                            "example": "What's the current system status?",
                        }
                    },
                },
                "ChatOpsResponse": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["success", "error"],
                            "description": "Response status",
                        },
                        "message": {
                            "type": "string",
                            "description": "Response message",
                        },
                        "timestamp": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Response timestamp",
                        },
                        "data": {
                            "type": "object",
                            "properties": {
                                "response": {
                                    "type": "string",
                                    "description": "ChatOps response",
                                },
                                "intent": {
                                    "type": "string",
                                    "description": "Detected intent",
                                },
                                "confidence": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                    "description": "Intent confidence",
                                },
                            },
                        },
                    },
                },
                "MetricsResponse": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["success", "error"],
                            "description": "Response status",
                        },
                        "message": {
                            "type": "string",
                            "description": "Response message",
                        },
                        "timestamp": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Response timestamp",
                        },
                        "data": {
                            "type": "object",
                            "properties": {
                                "metrics": {
                                    "type": "object",
                                    "description": "System metrics",
                                },
                                "source": {
                                    "type": "string",
                                    "description": "Metrics source",
                                },
                                "collection_time": {
                                    "type": "string",
                                    "format": "date-time",
                                    "description": "When metrics were collected",
                                },
                            },
                        },
                    },
                },
                "RemediationRequest": {
                    "type": "object",
                    "required": ["action", "target"],
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": [
                                "scale_up",
                                "scale_down",
                                "restart_service",
                                "clear_cache",
                            ],
                            "description": "Remediation action to execute",
                        },
                        "target": {
                            "type": "string",
                            "description": "Target resource for remediation",
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Additional parameters for the action",
                        },
                    },
                },
                "RemediationResponse": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["success", "error"],
                            "description": "Response status",
                        },
                        "message": {
                            "type": "string",
                            "description": "Response message",
                        },
                        "timestamp": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Response timestamp",
                        },
                        "data": {
                            "type": "object",
                            "properties": {
                                "action": {
                                    "type": "string",
                                    "description": "Executed action",
                                },
                                "success": {
                                    "type": "boolean",
                                    "description": "Whether action was successful",
                                },
                                "execution_time_seconds": {
                                    "type": "number",
                                    "description": "Time taken to execute action",
                                },
                            },
                        },
                    },
                },
                "ErrorResponse": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["error"],
                            "description": "Response status",
                        },
                        "message": {"type": "string", "description": "Error message"},
                        "error_code": {
                            "type": "string",
                            "description": "Error code for client handling",
                        },
                        "timestamp": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Response timestamp",
                        },
                        "details": {
                            "type": "object",
                            "description": "Additional error details",
                        },
                    },
                },
            },
        },
    }

    return jsonify(swagger_spec)
