#!/usr/bin/env python3
"""
ML Service - SmartCloudOps AI
============================

Microservice for machine learning operations including anomaly detection,
model management, and A/B testing.
"""





import os
import time
import json
import joblib
import numpy as np
import pandas as pd
import structlog
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, precision_score, recall_score


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus metrics
ml_requests_total = Counter('ml_requests_total', 'Total ML requests', ['method', 'endpoint', 'status'])
ml_request_duration = Histogram('ml_request_duration_seconds', 'ML request duration')
ml_predictions_total = Counter('ml_predictions_total', 'Total predictions made', ['model_version', 'prediction_type'])
ml_anomaly_rate = Gauge('ml_anomaly_rate', 'Current anomaly detection rate')
ml_model_accuracy = Gauge('ml_model_accuracy', 'Model accuracy score', ['model_version'])

@dataclass
class ModelMetadata:
    """Model metadata for versioning and tracking."""
    version: str
    name: str
    algorithm: str
    created_at: datetime
    accuracy: float
    f1_score: float
    precision: float
    recall: float
    is_active: bool = False
    is_production: bool = False
    parameters: Dict[str, Any] = None
    feature_columns: List[str] = None

@dataclass
class PredictionResult:
    """Prediction result with metadata."""
    prediction: int
    confidence: float
    model_version: str
    timestamp: datetime
    features: Dict[str, float]
    anomaly_score: Optional[float] = None

class ModelRegistry:
    """Model registry for versioning and management."""
    
    def __init__(self, model_path: str = "./ml_models"):
        self.model_path = Path(model_path)
        self.model_path.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.model_path / "metadata.json"
        self.models: Dict[str, ModelMetadata] = {}
        self.load_metadata()
    
    def load_metadata(self):
        """Load model metadata from file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    for model_data in data.values():
                        model_data['created_at'] = datetime.fromisoformat(model_data['created_at'])
                        self.models[model_data['version']] = ModelMetadata(**model_data)
                logger.info("Model metadata loaded", count=len(self.models))
            except Exception as e:
                logger.error("Failed to load model metadata", error=str(e))
    
    def save_metadata(self):
        """Save model metadata to file."""
        try:
            data = {}
            for version, model in self.models.items():
                model_dict = asdict(model)
                model_dict['created_at'] = model.created_at.isoformat()
                data[version] = model_dict
            
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info("Model metadata saved", count=len(self.models))
        except Exception as e:
            logger.error("Failed to save model metadata", error=str(e))
    
    def register_model(self, model, scaler, metadata: ModelMetadata) -> bool:
        """Register a new model version."""
        try:
            # Save model files
            model_file = self.model_path / f"model_{metadata.version}.pkl"
            scaler_file = self.model_path / f"scaler_{metadata.version}.pkl"
            
            joblib.dump(model, model_file)
            joblib.dump(scaler, scaler_file)
            
            # Add to registry
            self.models[metadata.version] = metadata
            self.save_metadata()
            
            logger.info(
                "Model registered successfully",
                version=metadata.version,
                accuracy=metadata.accuracy,
                algorithm=metadata.algorithm
            )
            
            return True
        except Exception as e:
            logger.error("Failed to register model", error=str(e), version=metadata.version)
            return False
    
    def get_model(self, version: str) -> Tuple[Optional[Any], Optional[Any]]:
        """Get model and scaler by version."""
        try:
            model_file = self.model_path / f"model_{version}.pkl"
            scaler_file = self.model_path / f"scaler_{version}.pkl"
            
            if not model_file.exists() or not scaler_file.exists():
                return None, None
            
            model = joblib.load(model_file)
            scaler = joblib.load(scaler_file)
            
            return model, scaler
        except Exception as e:
            logger.error("Failed to load model", error=str(e), version=version)
            return None, None
    
    def get_active_model(self) -> Tuple[Optional[Any], Optional[Any], Optional[ModelMetadata]]:
        """Get the currently active model."""
        for version, metadata in self.models.items():
            if metadata.is_active:
                model, scaler = self.get_model(version)
                return model, scaler, metadata
        return None, None, None
    
    def get_production_model(self) -> Tuple[Optional[Any], Optional[Any], Optional[ModelMetadata]]:
        """Get the production model."""
        for version, metadata in self.models.items():
            if metadata.is_production:
                model, scaler = self.get_model(version)
                return model, scaler, metadata
        return None, None, None

class ABTestManager:
    """A/B testing manager for model comparison."""
    
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self.test_configs = {}
        self.test_results = {}
    
    def start_test(self, test_id: str, model_a: str, model_b: str, 
                   traffic_split: float = 0.5, duration_days: int = 7) -> bool:
        """Start an A/B test between two model versions."""
        try:
            if model_a not in self.registry.models or model_b not in self.registry.models:
                return False
            
            self.test_configs[test_id] = {
                'model_a': model_a,
                'model_b': model_b,
                'traffic_split': traffic_split,
                'start_time': datetime.utcnow(),
                'end_time': datetime.utcnow() + timedelta(days=duration_days),
                'is_active': True
            }
            
            self.test_results[test_id] = {
                'model_a_results': [],
                'model_b_results': [],
                'model_a_metrics': {'accuracy': 0, 'f1_score': 0, 'precision': 0, 'recall': 0},
                'model_b_metrics': {'accuracy': 0, 'f1_score': 0, 'precision': 0, 'recall': 0}
            }
            
            logger.info(
                "A/B test started",
                test_id=test_id,
                model_a=model_a,
                model_b=model_b,
                traffic_split=traffic_split
            )
            
            return True
        except Exception as e:
            logger.error("Failed to start A/B test", error=str(e), test_id=test_id)
            return False
    
    def get_test_model(self, test_id: str) -> Optional[str]:
        """Get model version for A/B test based on traffic split."""
        if test_id not in self.test_configs:
            return None
        
        config = self.test_configs[test_id]
        if not config['is_active'] or datetime.utcnow() > config['end_time']:
            return None
        
        # Simple random assignment based on traffic split
        if np.random.random() < config['traffic_split']:
            return config['model_a']
        else:
            return config['model_b']
    
    def record_result(self, test_id: str, model_version: str, 
                     prediction: int, actual: int, confidence: float):
        """Record prediction result for A/B test."""
        if test_id not in self.test_results:
            return
        
        result = {
            'prediction': prediction,
            'actual': actual,
            'confidence': confidence,
            'timestamp': datetime.utcnow()
        }
        
        if model_version == self.test_configs[test_id]['model_a']:
            self.test_results[test_id]['model_a_results'].append(result)
        else:
            self.test_results[test_id]['model_b_results'].append(result)

class MLService:
    """Main ML service implementation."""
    
    def __init__(self):
        self.registry = ModelRegistry()
        self.ab_manager = ABTestManager(self.registry)
        self.feature_columns = ['cpu_usage', 'memory_usage', 'disk_usage', 'network_io']
        
        # Initialize default model if none exists
        self._initialize_default_model()
    
    def _initialize_default_model(self):
        """Initialize a default model if no models exist."""
        if not self.registry.models:
            logger.info("No models found, initializing default model")
            
            # Create synthetic training data
            np.random.seed(42)
            n_samples = 1000
            
            # Normal data
            normal_data = np.random.normal(0.5, 0.1, (n_samples, len(self.feature_columns)))
            
            # Anomaly data
            anomaly_data = np.random.normal(0.8, 0.2, (n_samples // 10, len(self.feature_columns)))
            
            # Combine data
            X = np.vstack([normal_data, anomaly_data])
            y = np.hstack([np.zeros(n_samples), np.ones(n_samples // 10)])
            
            # Train model
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            model = IsolationForest(contamination=0.1, random_state=42)
            model.fit(X_scaled)
            
            # Evaluate model
            predictions = model.predict(X_scaled)
            accuracy = np.mean(predictions == y)
            f1 = f1_score(y, predictions, average='weighted')
            precision = precision_score(y, predictions, average='weighted')
            recall = recall_score(y, predictions, average='weighted')
            
            # Create metadata
            metadata = ModelMetadata(
                version="v1.0.0",
                name="Default Anomaly Detection Model",
                algorithm="IsolationForest",
                created_at=datetime.utcnow(),
                accuracy=accuracy,
                f1_score=f1,
                precision=precision,
                recall=recall,
                is_active=True,
                is_production=True,
                parameters={'contamination': 0.1, 'random_state': 42},
                feature_columns=self.feature_columns
            )
            
            # Register model
            self.registry.register_model(model, scaler, metadata)
            
            # Update metrics
            ml_model_accuracy.labels(model_version="v1.0.0").set(accuracy)
    
    def predict(self, features: Dict[str, float], test_id: Optional[str] = None) -> PredictionResult:
        """Make prediction using appropriate model."""
        try:
            # Convert features to array
            feature_array = np.array([[features.get(col, 0.0) for col in self.feature_columns]])
            
            # Determine which model to use
            model_version = None
            if test_id:
                model_version = self.ab_manager.get_test_model(test_id)
            
            if not model_version:
                # Use production model
                model, scaler, metadata = self.registry.get_production_model()
                if not model:
                    # Fallback to active model
                    model, scaler, metadata = self.registry.get_active_model()
                    if not model:
                        raise ValueError("No active model available")
                model_version = metadata.version
            else:
                model, scaler, metadata = self.registry.get_model(model_version)
                if not model:
                    raise ValueError(f"Model version {model_version} not found")
            
            # Scale features
            features_scaled = scaler.transform(feature_array)
            
            # Make prediction
            prediction = model.predict(features_scaled)[0]
            anomaly_score = model.score_samples(features_scaled)[0] if hasattr(model, 'score_samples') else None
            
            # Convert prediction (IsolationForest: -1 for anomaly, 1 for normal)
            is_anomaly = 1 if prediction == -1 else 0
            
            # Calculate confidence (simplified)
            confidence = abs(anomaly_score) if anomaly_score is not None else 0.5
            
            result = PredictionResult(
                prediction=is_anomaly,
                confidence=confidence,
                model_version=model_version,
                timestamp=datetime.now(timezone.utc),
                features=features,
                anomaly_score=anomaly_score
            )
            
            # Record metrics
            ml_predictions_total.labels(
                model_version=model_version,
                prediction_type="anomaly" if is_anomaly else "normal"
            ).inc()
            
            # Update anomaly rate
            if is_anomaly:
                ml_anomaly_rate.inc()
            
            # Record A/B test result if applicable
            if test_id:
                self.ab_manager.record_result(test_id, model_version, is_anomaly, 0, confidence)
            
            logger.info(
                "Prediction made",
                prediction=is_anomaly,
                confidence=confidence,
                model_version=model_version,
                test_id=test_id
            )
            
            return result
            
        except Exception as e:
            logger.error("Prediction failed", error=str(e), features=features)
            raise
    
    def train_model(self, training_data: List[Dict[str, Any]], 
                   algorithm: str = "IsolationForest") -> Optional[str]:
        """Train a new model with provided data."""
        try:
            # Prepare training data
            X = []
            y = []
            
            for sample in training_data:
                features = [sample.get(col, 0.0) for col in self.feature_columns]
                X.append(features)
                y.append(sample.get('is_anomaly', 0))
            
            X = np.array(X)
            y = np.array(y)
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Train model
            if algorithm == "IsolationForest":
                model = IsolationForest(contamination=0.1, random_state=42)
                model.fit(X_scaled)
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")
            
            # Evaluate model
            predictions = model.predict(X_scaled)
            accuracy = np.mean(predictions == y)
            f1 = f1_score(y, predictions, average='weighted')
            precision = precision_score(y, predictions, average='weighted')
            recall = recall_score(y, predictions, average='weighted')
            
            # Generate version
            version = f"v{len(self.registry.models) + 1}.0.0"
            
            # Create metadata
            metadata = ModelMetadata(
                version=version,
                name=f"{algorithm} Model",
                algorithm=algorithm,
                created_at=datetime.utcnow(),
                accuracy=accuracy,
                f1_score=f1,
                precision=precision,
                recall=recall,
                is_active=False,
                is_production=False,
                parameters={'contamination': 0.1, 'random_state': 42},
                feature_columns=self.feature_columns
            )
            
            # Register model
            if self.registry.register_model(model, scaler, metadata):
                logger.info(
                    "Model trained successfully",
                    version=version,
                    accuracy=accuracy,
                    algorithm=algorithm
                )
                return version
            
            return None
            
        except Exception as e:
            logger.error("Model training failed", error=str(e), algorithm=algorithm)
            return None
    
    def promote_model(self, version: str, to_production: bool = False) -> bool:
        """Promote model to active or production."""
        try:
            if version not in self.registry.models:
                return False
            
            metadata = self.registry.models[version]
            
            if to_production:
                # Deactivate all production models
                for v, m in self.registry.models.items():
                    m.is_production = False
                metadata.is_production = True
                metadata.is_active = True
            else:
                # Deactivate all active models
                for v, m in self.registry.models.items():
                    m.is_active = False
                metadata.is_active = True
            
            self.registry.save_metadata()
            
            logger.info(
                "Model promoted",
                version=version,
                to_production=to_production
            )
            
            return True
            
        except Exception as e:
            logger.error("Model promotion failed", error=str(e), version=version)
            return False

# Initialize service
ml_service = MLService()

# Create Flask app
app = Flask(__name__)
CORS(app)

@app.before_request
def before_request():
    """Log request details."""
    g.start_time = time.time()
    g.request_id = request.headers.get('X-Request-ID', 'unknown')
    
    logger.info(
        "Request started",
        method=request.method,
        path=request.path,
        remote_addr=request.remote_addr,
        request_id=g.request_id
    )

@app.after_request
def after_request(response):
    """Log response and record metrics."""
    duration = time.time() - g.start_time
    
    # Record metrics
    ml_requests_total.labels(
        method=request.method,
        endpoint=request.path,
        status=response.status_code
    ).inc()
    
    ml_request_duration.observe(duration)
    
    # Log response
    logger.info(
        "Request completed",
        method=request.method,
        path=request.path,
        status_code=response.status_code,
        duration=duration,
        request_id=g.request_id
    )
    
    return response

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'ml-service',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'active_models': len([m for m in ml_service.registry.models.values() if m.is_active])
    })

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint."""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/ml/predict', methods=['POST'])
def predict():
    """Make prediction endpoint."""
    try:
        data = request.get_json()
        
        if not data or 'features' not in data:
            return jsonify({
                'error': 'Missing features',
                'code': 'MISSING_FEATURES'
            }), 400
        
        features = data['features']
        test_id = data.get('test_id')
        
        # Validate features
        required_features = ['cpu_usage', 'memory_usage', 'disk_usage', 'network_io']
        missing_features = [f for f in required_features if f not in features]
        
        if missing_features:
            return jsonify({
                'error': f'Missing required features: {missing_features}',
                'code': 'MISSING_FEATURES'
            }), 400
        
        # Make prediction
        result = ml_service.predict(features, test_id)
        
        return jsonify({
            'prediction': result.prediction,
            'confidence': result.confidence,
            'model_version': result.model_version,
            'timestamp': result.timestamp.isoformat(),
            'anomaly_score': result.anomaly_score,
            'features': result.features
        })
        
    except Exception as e:
        logger.error(
            "Prediction endpoint failed",
            error=str(e),
            request_id=g.request_id,
            exc_info=True
        )
        
        return jsonify({
            'error': 'Prediction failed',
            'code': 'PREDICTION_ERROR'
        }), 500

@app.route('/ml/models', methods=['GET'])
def list_models():
    """List all models endpoint."""
    try:
        models = []
        for version, metadata in ml_service.registry.models.items():
            models.append({
                'version': metadata.version,
                'name': metadata.name,
                'algorithm': metadata.algorithm,
                'created_at': metadata.created_at.isoformat(),
                'accuracy': metadata.accuracy,
                'f1_score': metadata.f1_score,
                'precision': metadata.precision,
                'recall': metadata.recall,
                'is_active': metadata.is_active,
                'is_production': metadata.is_production
            })
        
        return jsonify({
            'models': models,
            'total': len(models)
        })
        
    except Exception as e:
        logger.error(
            "List models failed",
            error=str(e),
            request_id=g.request_id,
            exc_info=True
        )
        
        return jsonify({
            'error': 'Failed to list models',
            'code': 'LIST_ERROR'
        }), 500

@app.route('/ml/models/<version>/promote', methods=['POST'])
def promote_model(version: str):
    """Promote model endpoint."""
    try:
        data = request.get_json() or {}
        to_production = data.get('to_production', False)
        
        success = ml_service.promote_model(version, to_production)
        
        if not success:
            return jsonify({
                'error': 'Model not found or promotion failed',
                'code': 'PROMOTION_FAILED'
            }), 400
        
        return jsonify({
            'message': 'Model promoted successfully',
            'version': version,
            'to_production': to_production
        })
        
    except Exception as e:
        logger.error(
            "Model promotion failed",
            error=str(e),
            version=version,
            request_id=g.request_id,
            exc_info=True
        )
        
        return jsonify({
            'error': 'Model promotion failed',
            'code': 'PROMOTION_ERROR'
        }), 500

@app.route('/ml/train', methods=['POST'])
def train_model():
    """Train new model endpoint."""
    try:
        data = request.get_json()
        
        if not data or 'training_data' not in data:
            return jsonify({
                'error': 'Missing training data',
                'code': 'MISSING_TRAINING_DATA'
            }), 400
        
        training_data = data['training_data']
        algorithm = data.get('algorithm', 'IsolationForest')
        
        version = ml_service.train_model(training_data, algorithm)
        
        if not version:
            return jsonify({
                'error': 'Model training failed',
                'code': 'TRAINING_FAILED'
            }), 500
        
        return jsonify({
            'message': 'Model trained successfully',
            'version': version,
            'algorithm': algorithm
        })
        
    except Exception as e:
        logger.error(
            "Model training failed",
            error=str(e),
            request_id=g.request_id,
            exc_info=True
        )
        
        return jsonify({
            'error': 'Model training failed',
            'code': 'TRAINING_ERROR'
        }), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Global exception handler."""
    logger.error(
        "Unhandled exception",
        error=str(e),
        request_id=g.request_id,
        exc_info=True
    )
    
    return jsonify({
        'error': 'Internal server error',
        'code': 'INTERNAL_ERROR'
    }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5002))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(
        "Starting ML service",
        port=port,
        debug=debug
    )
    
    app.run(host='0.0.0.0', port=port, debug=debug)
