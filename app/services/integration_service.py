#!/usr/bin/env python3
"""
SmartCloudOps AI - ML-Remediation Integration Service
=====================================================

Phase 4: Integration Service
Connects ML anomaly detection with auto-remediation engine.
"""

import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional

from app.core.ml_engine.production_inference import ProductionInferenceEngine
from app.services.remediation_service import remediation_engine

logger = logging.getLogger(__name__)


class MLRemediationIntegration:
    """Integrates ML anomaly detection with auto-remediation engine."""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.ml_engine = ProductionInferenceEngine()
        self.is_running = False
        self.monitoring_thread = None
        self.metrics_buffer: list = []
        self.last_prediction = None

        # Configuration
        self.monitoring_interval = self.config.get("monitoring_interval", 30)  # seconds
        self.buffer_size = self.config.get("buffer_size", 10)
        self.confidence_threshold = self.config.get("confidence_threshold", 0.7)

        logger.info("✅ ML-Remediation Integration initialized")

    def start_monitoring(self):
        """Start the continuous monitoring and remediation process."""
        if self.is_running:
            logger.warning("⚠️ Monitoring already running")
            return

        self.is_running = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )
        self.monitoring_thread.start()
        logger.info("🚀 Started ML-Remediation monitoring loop")

    def stop_monitoring(self):
        """Stop the continuous monitoring process."""
        self.is_running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("⏸️ Stopped ML-Remediation monitoring loop")

    def _monitoring_loop(self):
        """Main monitoring loop that continuously processes metrics and triggers remediation."""
        while self.is_running:
            try:
                # Collect current system metrics
                metrics = self._collect_system_metrics()

                # Get ML prediction
                ml_prediction = self._get_ml_prediction(metrics)

                # Process through remediation engine
                if ml_prediction:
                    triggered_actions = remediation_engine.process_metrics(
                        metrics, ml_prediction
                    )

                    if triggered_actions:
                        logger.info(
                            f"🎯 Triggered {len(triggered_actions)} remediation actions"
                        )
                        for action in triggered_actions:
                            logger.info(
                                f"  - {action['rule_name']}: {action['action']} ({'✅' if action['success'] else '❌'})"
                            )

                # Store metrics in buffer
                self._update_metrics_buffer(metrics, ml_prediction)

                # Wait for next monitoring cycle
                time.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)

    def _collect_system_metrics(self) -> Dict:
        """Collect current system metrics."""
        try:
            import psutil

            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Get network metrics
            network = psutil.net_io_counters()

            # Calculate response time (simulated for now)
            response_time_ms = self._measure_response_time()

            # Calculate error rate (simulated for now)
            error_rate = self._calculate_error_rate()

            metrics = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024**3),
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_recv": network.bytes_recv,
                "response_time_ms": response_time_ms,
                "error_rate": error_rate,
                "timestamp": datetime.utcnow().isoformat(),
            }

            return metrics

        except ImportError:
            # Fallback to simulated metrics if psutil is not available
            logger.warning("⚠️ psutil not available, using simulated metrics")
            return self._get_simulated_metrics()
        except Exception as e:
            logger.error(f"❌ Error collecting system metrics: {e}")
            return self._get_simulated_metrics()

    def _get_simulated_metrics(self) -> Dict:
        """Get simulated metrics for testing."""
        import random

        return {
            "cpu_percent": random.uniform(20, 95),
            "memory_percent": random.uniform(30, 90),
            "memory_available_gb": random.uniform(0.5, 2.0),
            "disk_percent": random.uniform(40, 80),
            "disk_free_gb": random.uniform(5, 20),
            "network_bytes_sent": random.randint(1000, 10000),
            "network_bytes_recv": random.randint(1000, 10000),
            "response_time_ms": random.uniform(50, 5000),
            "error_rate": random.uniform(0.01, 0.2),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _measure_response_time(self) -> float:
        """Measure application response time."""
        try:
            import requests

            start_time = time.time()
            response = requests.get("http://localhost:5000/status", timeout=5)
            end_time = time.time()

            if response.status_code == 200:
                return (end_time - start_time) * 1000  # Convert to milliseconds
            else:
                return 5000  # High response time for errors

        except Exception:
            return 100  # Default response time if measurement fails

    def _calculate_error_rate(self) -> float:
        """Calculate current error rate."""
        try:
            # This would typically come from application logs or metrics
            # For now, we'll use a simple simulation
            import random

            return random.uniform(0.01, 0.05)  # 1-5% error rate
        except Exception:
            return 0.02  # Default 2% error rate

    def _get_ml_prediction(self, metrics: Dict) -> Optional[Dict]:
        """Get ML prediction for the current metrics."""
        try:
            # Prepare features for ML prediction
            features = self._prepare_features(metrics)

            # Get prediction from ML engine
            prediction = self.ml_engine.predict_anomaly(features)

            if prediction:
                self.last_prediction = {
                    "anomaly_score": prediction.get("anomaly_score", 0.0),
                    "confidence": prediction.get("confidence", 0.0),
                    "is_anomaly": prediction.get("is_anomaly", False),
                    "timestamp": datetime.utcnow().isoformat(),
                }

                # Only return prediction if confidence is above threshold
                if self.last_prediction["confidence"] >= self.confidence_threshold:
                    return self.last_prediction

            return None

        except Exception as e:
            logger.error(f"❌ Error getting ML prediction: {e}")
            return None

    def _prepare_features(self, metrics: Dict) -> Dict:
        """Prepare features for ML prediction."""
        try:
            # Extract relevant features for anomaly detection
            features = {
                "cpu_percent": metrics.get("cpu_percent", 0.0),
                "memory_percent": metrics.get("memory_percent", 0.0),
                "disk_percent": metrics.get("disk_percent", 0.0),
                "response_time_ms": metrics.get("response_time_ms", 0.0),
                "error_rate": metrics.get("error_rate", 0.0),
                "network_bytes_sent": metrics.get("network_bytes_sent", 0),
                "network_bytes_recv": metrics.get("network_bytes_recv", 0),
            }

            # Add derived features
            features["memory_available_gb"] = metrics.get("memory_available_gb", 0.0)
            features["disk_free_gb"] = metrics.get("disk_free_gb", 0.0)

            # Add time-based features
            timestamp = datetime.fromisoformat(
                metrics.get("timestamp", datetime.utcnow().isoformat())
            )
            features["hour"] = timestamp.hour
            features["minute"] = timestamp.minute
            features["day_of_week"] = timestamp.weekday()

            return features

        except Exception as e:
            logger.error(f"❌ Error preparing features: {e}")
            return {}

    def _update_metrics_buffer(self, metrics: Dict, ml_prediction: Optional[Dict]):
        """Update the metrics buffer with new data."""
        buffer_entry = {
            "metrics": metrics,
            "ml_prediction": ml_prediction,
            "timestamp": datetime.utcnow(),
        }

        self.metrics_buffer.append(buffer_entry)

        # Keep buffer size manageable
        if len(self.metrics_buffer) > self.buffer_size:
            self.metrics_buffer.pop(0)

    def get_status(self) -> Dict:
        """Get the current status of the integration service."""
        return {
            "is_running": self.is_running,
            "monitoring_interval": self.monitoring_interval,
            "confidence_threshold": self.confidence_threshold,
            "buffer_size": len(self.metrics_buffer),
            "last_prediction": self.last_prediction,
            "remediation_engine_status": remediation_engine.get_status(),
        }

    def get_recent_metrics(self, limit: int = 10) -> List[Dict]:
        """Get recent metrics and predictions."""
        return self.metrics_buffer[-limit:] if self.metrics_buffer else []

    def trigger_manual_remediation(self, metrics: Dict) -> List[Dict]:
        """Manually trigger remediation with provided metrics."""
        try:
            # Get ML prediction for the metrics
            ml_prediction = self._get_ml_prediction(metrics)

            # Process through remediation engine
            triggered_actions = remediation_engine.process_metrics(
                metrics, ml_prediction
            )

            logger.info(
                f"🔧 Manual remediation triggered: {len(triggered_actions)} actions"
            )

            return triggered_actions

        except Exception as e:
            logger.error(f"❌ Error in manual remediation: {e}")
            return []

    def update_config(self, new_config: Dict):
        """Update the integration configuration."""
        try:
            if "monitoring_interval" in new_config:
                self.monitoring_interval = new_config["monitoring_interval"]

            if "confidence_threshold" in new_config:
                self.confidence_threshold = new_config["confidence_threshold"]

            if "buffer_size" in new_config:
                self.buffer_size = new_config["buffer_size"]
                # Trim buffer if needed
                while len(self.metrics_buffer) > self.buffer_size:
                    self.metrics_buffer.pop(0)

            logger.info("✅ Integration configuration updated")

        except Exception as e:
            logger.error(f"❌ Error updating configuration: {e}")


# Global instance
integration_service = MLRemediationIntegration()
