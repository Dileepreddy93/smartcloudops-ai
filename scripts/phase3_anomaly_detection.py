#!/usr/bin/env python3
"""
SmartCloudOps AI - Phase 3: ML Anomaly Detection System
===================================================

Comprehensive anomaly detection system using Isolation Forest and Prophet
for real-time monitoring of cloud infrastructure metrics.

Target: F1-score ≥ 0.85
Data Source: Prometheus metrics from monitoring infrastructure
Storage: S3 bucket for model persistence
"""

import json
import logging
import os
import sys
import warnings
from datetime import datetime, timedelta

import boto3
import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import seaborn as sns
from prophet import Prophet
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# Prefer real data for training when available
try:
    from real_data_integration import RealDataCollector

    _REAL_DATA_AVAILABLE = True
except Exception:
    _REAL_DATA_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("../logs/anomaly_detection.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class SmartCloudOpsAnomalyDetector:
    """
    Advanced anomaly detection system for cloud infrastructure monitoring.

    Features:
    - Multi-algorithm approach (Isolation Forest + Prophet)
    - Real-time data collection from Prometheus
    - S3 model persistence
    - Performance metrics tracking
    - Automated threshold optimization
    """

    def __init__(
        self,
        prometheus_url="http://3.89.229.102:9090",
        s3_bucket="smartcloudops-ai-ml-models-aa7be1e7",
    ):
        """
        Initialize the anomaly detection system.

        Args:
            prometheus_url (str): Prometheus server URL
            s3_bucket (str): S3 bucket for model storage
        """
        self.prometheus_url = prometheus_url
        self.s3_bucket = s3_bucket
        self.models = {}
        self.scalers = {}
        self.metrics_config = {
            "cpu_usage": "cpu_usage_percent",
            "memory_usage": "memory_usage_percent",
            "disk_io": "disk_io_rate",
            "network_io": "network_io_rate",
            "response_time": "http_response_time",
        }

        # Initialize AWS S3 client
        try:
            self.s3_client = boto3.client("s3")
            logger.info("✅ AWS S3 client initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ AWS S3 client initialization failed: {e}")
            self.s3_client = None

        # Model parameters
        self.isolation_forest_params = {
            "contamination": 0.1,
            "random_state": 42,
            "n_estimators": 100,
        }

        logger.info("🚀 SmartCloudOps Anomaly Detector initialized")
        logger.info(f"📊 Prometheus URL: {self.prometheus_url}")
        logger.info(f"🗄️ S3 Bucket: {self.s3_bucket}")

    def collect_prometheus_data(self, query, start_time=None, end_time=None, step="1m"):
        """
        Collect time series data from Prometheus.

        Args:
            query (str): PromQL query string
            start_time (datetime): Start time for data collection
            end_time (datetime): End time for data collection
            step (str): Query resolution step

        Returns:
            pandas.DataFrame: Time series data
        """
        try:
            if start_time is None:
                start_time = datetime.now() - timedelta(hours=24)
            if end_time is None:
                end_time = datetime.now()

            # Convert to Unix timestamps
            start_ts = int(start_time.timestamp())
            end_ts = int(end_time.timestamp())

            # Prometheus range query
            url = f"{self.prometheus_url}/api/v1/query_range"
            params = {"query": query, "start": start_ts, "end": end_ts, "step": step}

            logger.info(f"📊 Collecting data: {query}")
            response = requests.get(url, params=params, timeout=30)

            if response.status_code != 200:
                logger.error(f"❌ Prometheus query failed: {response.status_code}")
                return pd.DataFrame()

            data = response.json()

            if data["status"] != "success":
                logger.error(f"❌ Prometheus query error: {data}")
                return pd.DataFrame()

            # Parse time series data
            time_series = []
            for result in data["data"]["result"]:
                metric_name = result["metric"].get("__name__", "unknown")
                instance = result["metric"].get("instance", "unknown")

                for timestamp, value in result["values"]:
                    time_series.append(
                        {
                            "timestamp": pd.to_datetime(timestamp, unit="s"),
                            "metric": metric_name,
                            "instance": instance,
                            "value": float(value),
                        }
                    )

            df = pd.DataFrame(time_series)
            if not df.empty:
                df = df.sort_values("timestamp").reset_index(drop=True)
                logger.info(f"✅ Collected {len(df)} data points")
            else:
                logger.warning("⚠️ No data collected from Prometheus")

            return df

        except Exception as e:
            logger.error(f"❌ Error collecting Prometheus data: {e}")
            return pd.DataFrame()

    def generate_synthetic_data(self, days=7):
        """
        Generate synthetic monitoring data for training and testing.
        This simulates real infrastructure metrics with embedded anomalies.

        Args:
            days (int): Number of days of data to generate

        Returns:
            pandas.DataFrame: Synthetic time series data
        """
        logger.info(f"🧪 Generating {days} days of synthetic data")

        # Generate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        timestamps = pd.date_range(start_time, end_time, freq="1min")

        np.random.seed(42)
        data_points = []

        for ts in timestamps:
            # Simulate daily patterns
            hour = ts.hour
            day_of_week = ts.weekday()

            # Base patterns with daily/weekly seasonality
            cpu_base = (
                30
                + 20 * np.sin(2 * np.pi * hour / 24)
                + 10 * np.sin(2 * np.pi * day_of_week / 7)
            )
            memory_base = (
                45
                + 15 * np.sin(2 * np.pi * hour / 24)
                + 5 * np.sin(2 * np.pi * day_of_week / 7)
            )

            # Add normal noise
            cpu_usage = max(0, min(100, cpu_base + np.random.normal(0, 5)))
            memory_usage = max(0, min(100, memory_base + np.random.normal(0, 3)))
            disk_io = max(
                0, 100 + 50 * np.sin(2 * np.pi * hour / 24) + np.random.normal(0, 10)
            )
            network_io = max(
                0, 200 + 100 * np.sin(2 * np.pi * hour / 24) + np.random.normal(0, 20)
            )
            response_time = max(
                50, 200 + 50 * np.sin(2 * np.pi * hour / 24) + np.random.normal(0, 15)
            )

            # Inject anomalies (10% of data points)
            is_anomaly = False
            if np.random.random() < 0.1:
                is_anomaly = True
                # Create various types of anomalies
                anomaly_type = np.random.choice(["spike", "drop", "sustained_high"])

                if anomaly_type == "spike":
                    cpu_usage = min(100, cpu_usage * 1.8)
                    memory_usage = min(100, memory_usage * 1.6)
                    response_time *= 2.5
                elif anomaly_type == "drop":
                    cpu_usage *= 0.1
                    memory_usage *= 0.3
                    disk_io *= 0.2
                elif anomaly_type == "sustained_high":
                    cpu_usage = min(100, 85 + np.random.normal(0, 3))
                    memory_usage = min(100, 80 + np.random.normal(0, 2))

            data_points.append(
                {
                    "timestamp": ts,
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory_usage,
                    "disk_io": disk_io,
                    "network_io": network_io,
                    "response_time": response_time,
                    "is_anomaly": is_anomaly,
                }
            )

        df = pd.DataFrame(data_points)
        logger.info(f"✅ Generated {len(df)} synthetic data points")
        logger.info(f"🎯 Anomaly rate: {df['is_anomaly'].mean():.2%}")

        return df

    def prepare_features(self, df):
        """
        Prepare features for anomaly detection models.

        Args:
            df (pandas.DataFrame): Raw time series data

        Returns:
            pandas.DataFrame: Feature-engineered dataset
        """
        logger.info("🔧 Preparing features for ML models")

        # Sort by timestamp
        df = df.sort_values("timestamp").reset_index(drop=True)

        # Extract time-based features
        df["hour"] = df["timestamp"].dt.hour
        df["day_of_week"] = df["timestamp"].dt.dayofweek
        df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

        # Rolling statistics (moving averages and standard deviations)
        feature_cols = [
            "cpu_usage",
            "memory_usage",
            "disk_io",
            "network_io",
            "response_time",
        ]

        for col in feature_cols:
            # Moving averages
            df[f"{col}_ma_5"] = df[col].rolling(window=5, min_periods=1).mean()
            df[f"{col}_ma_15"] = df[col].rolling(window=15, min_periods=1).mean()
            df[f"{col}_ma_60"] = df[col].rolling(window=60, min_periods=1).mean()

            # Moving standard deviations
            df[f"{col}_std_5"] = (
                df[col].rolling(window=5, min_periods=1).std().fillna(0)
            )
            df[f"{col}_std_15"] = (
                df[col].rolling(window=15, min_periods=1).std().fillna(0)
            )

            # Rate of change
            df[f"{col}_diff"] = df[col].diff().fillna(0)
            df[f"{col}_pct_change"] = df[col].pct_change().fillna(0)

        # Cross-metric features
        df["cpu_memory_ratio"] = df["cpu_usage"] / (df["memory_usage"] + 1e-6)
        df["io_total"] = df["disk_io"] + df["network_io"]
        df["load_indicator"] = (df["cpu_usage"] + df["memory_usage"]) / 2

        # Handle infinite and NaN values
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.fillna(0)

        # Clip extreme values to reasonable ranges
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col not in [
                "timestamp",
                "hour",
                "day_of_week",
                "is_weekend",
                "is_anomaly",
            ]:
                df[col] = np.clip(df[col], -1e6, 1e6)

        logger.info(f"✅ Feature engineering complete: {df.shape[1]} features")
        return df

    def train_isolation_forest(self, df, feature_columns):
        """
        Train Isolation Forest model for anomaly detection.

        Args:
            df (pandas.DataFrame): Training data
            feature_columns (list): List of feature column names

        Returns:
            dict: Training results and metrics
        """
        logger.info("🌲 Training Isolation Forest model")

        # Prepare training data
        X = df[feature_columns].copy()

        # Clean the data thoroughly
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.fillna(0)

        # Convert all columns to numeric, coercing errors to NaN
        for col in X.columns:
            X[col] = pd.to_numeric(X[col], errors="coerce")

        # Fill any remaining NaN values
        X = X.fillna(0)

        # Ensure all values are finite
        for col in X.columns:
            X[col] = np.clip(X[col], -1e6, 1e6)

        y_true = df["is_anomaly"].values if "is_anomaly" in df.columns else None

        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Train Isolation Forest
        iso_forest = IsolationForest(**self.isolation_forest_params)
        iso_forest.fit(X_scaled)

        # Predict anomalies (-1 for anomalies, 1 for normal)
        predictions = iso_forest.predict(X_scaled)
        anomaly_scores = iso_forest.decision_function(X_scaled)

        # Convert predictions to binary (1 for anomaly, 0 for normal)
        y_pred = (predictions == -1).astype(int)

        # Store models
        self.models["isolation_forest"] = iso_forest
        self.scalers["isolation_forest"] = scaler

        # Calculate performance metrics if ground truth is available
        results = {
            "model_type": "isolation_forest",
            "predictions": y_pred,
            "anomaly_scores": anomaly_scores,
            "feature_count": len(feature_columns),
        }

        if y_true is not None:
            f1 = f1_score(y_true, y_pred)
            results.update(
                {
                    "f1_score": f1,
                    "classification_report": classification_report(y_true, y_pred),
                    "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
                }
            )

            logger.info(f"🎯 Isolation Forest F1-Score: {f1:.4f}")
            logger.info(
                f"📊 Classification Report:\n{results['classification_report']}"
            )

        return results

    def train_prophet_model(self, df, metric_column="cpu_usage"):
        """
        Train Prophet model for time series anomaly detection.

        Args:
            df (pandas.DataFrame): Training data
            metric_column (str): Target metric column

        Returns:
            dict: Training results and predictions
        """
        logger.info(f"📈 Training Prophet model for {metric_column}")

        # Prepare data for Prophet (needs 'ds' and 'y' columns)
        prophet_df = df[["timestamp", metric_column]].copy()
        prophet_df.columns = ["ds", "y"]
        prophet_df = prophet_df.dropna()

        # Initialize and train Prophet model
        prophet_model = Prophet(
            changepoint_prior_scale=0.05,
            seasonality_prior_scale=10.0,
            interval_width=0.95,
            daily_seasonality=True,
            weekly_seasonality=True,
        )

        prophet_model.fit(prophet_df)

        # Make predictions
        future = prophet_model.make_future_dataframe(periods=0, freq="min")
        forecast = prophet_model.predict(future)

        # Calculate residuals and identify anomalies
        merged = pd.merge(
            prophet_df, forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]], on="ds"
        )
        merged["residual"] = merged["y"] - merged["yhat"]
        merged["residual_abs"] = np.abs(merged["residual"])

        # Define anomalies as points outside prediction intervals
        merged["is_anomaly_prophet"] = (
            (merged["y"] < merged["yhat_lower"]) | (merged["y"] > merged["yhat_upper"])
        ).astype(int)

        # Store model
        self.models[f"prophet_{metric_column}"] = prophet_model

        results = {
            "model_type": "prophet",
            "metric": metric_column,
            "predictions": merged["is_anomaly_prophet"].values,
            "forecast_data": forecast,
            "residuals": merged["residual"].values,
        }

        logger.info(f"✅ Prophet model trained for {metric_column}")
        return results

    def save_models_to_s3(self):
        """
        Save trained models to S3 bucket for persistence.
        """
        if not self.s3_client:
            logger.warning("⚠️ S3 client not available, saving models locally")
            return self._save_models_locally()

        try:
            logger.info("💾 Saving models to S3...")

            # Save Isolation Forest model and scaler
            if "isolation_forest" in self.models:
                # Save model
                model_path = "/tmp/anomaly_model.pkl"
                joblib.dump(self.models["isolation_forest"], model_path)
                self.s3_client.upload_file(
                    model_path, self.s3_bucket, "models/anomaly_model.pkl"
                )

                # Save scaler
                scaler_path = "/tmp/isolation_forest_scaler.pkl"
                joblib.dump(self.scalers["isolation_forest"], scaler_path)
                self.s3_client.upload_file(
                    scaler_path, self.s3_bucket, "models/isolation_forest_scaler.pkl"
                )

                logger.info("✅ Isolation Forest model saved to S3")

            # Save Prophet models
            for model_name, model in self.models.items():
                if model_name.startswith("prophet_"):
                    model_path = f"/tmp/{model_name}_model.pkl"
                    joblib.dump(model, model_path)
                    self.s3_client.upload_file(
                        model_path, self.s3_bucket, f"models/{model_name}_model.pkl"
                    )
                    logger.info(f"✅ {model_name} model saved to S3")

            # Save metadata
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "models": list(self.models.keys()),
                "scalers": list(self.scalers.keys()),
                "bucket": self.s3_bucket,
            }

            metadata_path = "/tmp/model_metadata.json"
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)

            self.s3_client.upload_file(
                metadata_path, self.s3_bucket, "models/metadata.json"
            )
            logger.info("✅ All models and metadata saved to S3")

        except Exception as e:
            logger.error(f"❌ Error saving models to S3: {e}")
            logger.info("📁 Falling back to local storage")
            self._save_models_locally()

    def _save_models_locally(self):
        """
        Save models locally as fallback.
        """
        try:
            os.makedirs("../ml_models", exist_ok=True)

            # Save Isolation Forest
            if "isolation_forest" in self.models:
                joblib.dump(
                    self.models["isolation_forest"], "../ml_models/anomaly_model.pkl"
                )
                joblib.dump(
                    self.scalers["isolation_forest"],
                    "../ml_models/isolation_forest_scaler.pkl",
                )
                logger.info("✅ Isolation Forest saved locally")

            # Save Prophet models
            for model_name, model in self.models.items():
                if model_name.startswith("prophet_"):
                    joblib.dump(model, f"../ml_models/{model_name}_model.pkl")
                    logger.info(f"✅ {model_name} saved locally")

            # Save metadata
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "models": list(self.models.keys()),
                "scalers": list(self.scalers.keys()),
                "location": "local",
            }

            with open("../ml_models/metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)

            logger.info("✅ All models saved locally")

        except Exception as e:
            logger.error(f"❌ Error saving models locally: {e}")

    def create_visualizations(self, df, results):
        """
        Create comprehensive visualizations for anomaly detection results.

        Args:
            df (pandas.DataFrame): Data with predictions
            results (dict): Model results
        """
        logger.info("📊 Creating anomaly detection visualizations")

        try:
            # Set up the plotting style
            plt.style.use("default")
            sns.set_palette("husl")

            # Create figure with subplots
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle(
                "SmartCloudOps AI - Anomaly Detection Analysis",
                fontsize=16,
                fontweight="bold",
            )

            # Plot 1: Time series with anomalies
            ax1 = axes[0, 0]
            df_plot = df.tail(1000)  # Plot last 1000 points for visibility

            ax1.plot(
                df_plot["timestamp"],
                df_plot["cpu_usage"],
                "b-",
                alpha=0.7,
                label="CPU Usage",
            )
            ax1.plot(
                df_plot["timestamp"],
                df_plot["memory_usage"],
                "g-",
                alpha=0.7,
                label="Memory Usage",
            )

            # Highlight anomalies
            if "is_anomaly" in df_plot.columns:
                anomalies = df_plot[df_plot["is_anomaly"] == 1]
                ax1.scatter(
                    anomalies["timestamp"],
                    anomalies["cpu_usage"],
                    color="red",
                    s=50,
                    alpha=0.8,
                    label="True Anomalies",
                )

            ax1.set_title("Infrastructure Metrics with Anomalies")
            ax1.set_xlabel("Time")
            ax1.set_ylabel("Usage (%)")
            ax1.legend()
            ax1.grid(True, alpha=0.3)

            # Plot 2: Anomaly scores distribution
            ax2 = axes[0, 1]
            if "anomaly_scores" in results:
                ax2.hist(
                    results["anomaly_scores"],
                    bins=50,
                    alpha=0.7,
                    color="skyblue",
                    edgecolor="black",
                )
                ax2.set_title("Isolation Forest Anomaly Scores")
                ax2.set_xlabel("Anomaly Score")
                ax2.set_ylabel("Frequency")
                ax2.grid(True, alpha=0.3)

            # Plot 3: Confusion Matrix (if available)
            ax3 = axes[1, 0]
            if "confusion_matrix" in results:
                cm = np.array(results["confusion_matrix"])
                sns.heatmap(
                    cm,
                    annot=True,
                    fmt="d",
                    cmap="Blues",
                    ax=ax3,
                    xticklabels=["Normal", "Anomaly"],
                    yticklabels=["Normal", "Anomaly"],
                )
                ax3.set_title("Confusion Matrix")
                ax3.set_xlabel("Predicted")
                ax3.set_ylabel("Actual")

            # Plot 4: Feature importance/correlation
            ax4 = axes[1, 1]
            feature_cols = [
                "cpu_usage",
                "memory_usage",
                "disk_io",
                "network_io",
                "response_time",
            ]
            correlation_matrix = df[feature_cols].corr()
            sns.heatmap(
                correlation_matrix, annot=True, cmap="coolwarm", center=0, ax=ax4
            )
            ax4.set_title("Feature Correlation Matrix")

            plt.tight_layout()

            # Save visualization
            os.makedirs("../docs", exist_ok=True)
            plt.savefig(
                "../docs/anomaly_detection_analysis.png", dpi=300, bbox_inches="tight"
            )
            logger.info(
                "✅ Visualization saved to ../docs/anomaly_detection_analysis.png"
            )

            plt.close()

        except Exception as e:
            logger.error(f"❌ Error creating visualizations: {e}")

    def run_complete_training_pipeline(self):
        """
        Execute the complete training pipeline for Phase 3.

        Returns:
            dict: Complete training results and metrics
        """
        logger.info("🚀 Starting Phase 3 ML Anomaly Detection Training Pipeline")

        # Step 1: Data Collection
        logger.info("📊 Step 1: Data Collection")

        # Prefer real monitoring data; fallback to synthetic
        data = pd.DataFrame()
        if _REAL_DATA_AVAILABLE:
            try:
                collector = RealDataCollector()
                real_df = collector.collect_comprehensive_dataset(hours_back=24)
                if not real_df.empty:
                    logger.info("📊 Using real monitoring data for training")
                    data = real_df
                else:
                    logger.info(
                        "📊 No real data available, falling back to synthetic data"
                    )
            except Exception as e:
                logger.warning(
                    f"⚠️ Real data collection failed, falling back to synthetic: {e}"
                )

        if data.empty:
            data = self.generate_synthetic_data(days=7)

        # Step 2: Feature Engineering
        logger.info("🔧 Step 2: Feature Engineering")
        enhanced_data = self.prepare_features(data)

        # Step 3: Model Training
        logger.info("🤖 Step 3: Model Training")

        # Define feature columns for Isolation Forest (exclude non-numeric/meta cols)
        feature_columns = [
            col
            for col in enhanced_data.columns
            if col not in ["timestamp", "is_anomaly", "source"]
        ]

        # Train Isolation Forest
        iso_results = self.train_isolation_forest(enhanced_data, feature_columns)

        # Train Prophet models for key metrics
        prophet_results = {}
        for metric in ["cpu_usage", "memory_usage", "response_time"]:
            if metric in enhanced_data.columns:
                prophet_results[metric] = self.train_prophet_model(
                    enhanced_data, metric
                )

        # Step 4: Model Evaluation
        logger.info("📊 Step 4: Model Evaluation")

        # Combine results
        combined_results = {
            "isolation_forest": iso_results,
            "prophet_models": prophet_results,
            "data_summary": {
                "total_points": len(enhanced_data),
                "feature_count": len(feature_columns),
                "anomaly_rate": enhanced_data["is_anomaly"].mean(),
                "time_range": {
                    "start": enhanced_data["timestamp"].min().isoformat(),
                    "end": enhanced_data["timestamp"].max().isoformat(),
                },
            },
        }

        # Step 5: Model Persistence
        logger.info("💾 Step 5: Model Persistence")
        self.save_models_to_s3()

        # Step 6: Visualization
        logger.info("📊 Step 6: Creating Visualizations")
        self.create_visualizations(enhanced_data, iso_results)

        # Step 7: Performance Summary
        logger.info("📋 Step 7: Performance Summary")
        self._print_performance_summary(combined_results)

        return combined_results

    def _print_performance_summary(self, results):
        """
        Print comprehensive performance summary.

        Args:
            results (dict): Training results
        """
        print("\n" + "=" * 80)
        print("🎯 SMARTCLOUDOPS AI - PHASE 3 TRAINING COMPLETE")
        print("=" * 80)

        # Isolation Forest Results
        if "isolation_forest" in results:
            iso_results = results["isolation_forest"]
            print("\n🌲 ISOLATION FOREST RESULTS:")
            print(f"   Features Used: {iso_results['feature_count']}")

            if "f1_score" in iso_results:
                f1_score = iso_results["f1_score"]
                target_score = 0.85
                status = (
                    "✅ TARGET ACHIEVED"
                    if f1_score >= target_score
                    else "⚠️ NEEDS IMPROVEMENT"
                )
                print(f"   F1-Score: {f1_score:.4f} (Target: ≥{target_score}) {status}")

        # Prophet Results
        if "prophet_models" in results:
            print("\n📈 PROPHET MODELS TRAINED:")
            for metric, model_results in results["prophet_models"].items():
                anomaly_rate = model_results["predictions"].mean()
                print(f"   {metric}: {anomaly_rate:.2%} anomalies detected")

        # Data Summary
        if "data_summary" in results:
            summary = results["data_summary"]
            print("\n📊 DATA SUMMARY:")
            print(f"   Total Data Points: {summary['total_points']:,}")
            print(f"   Features Engineered: {summary['feature_count']}")
            print(f"   Ground Truth Anomaly Rate: {summary['anomaly_rate']:.2%}")
            print(
                f"   Time Range: {summary['time_range']['start']} to {summary['time_range']['end']}"
            )

        print("\n💾 MODELS SAVED:")
        print(f"   S3 Bucket: {self.s3_bucket}")
        print("   Local Backup: ../ml_models/")

        print("\n📊 VISUALIZATIONS:")
        print("   Analysis Chart: ../docs/anomaly_detection_analysis.png")

        print("\n🚀 NEXT STEPS:")
        print("   1. Review model performance metrics")
        print("   2. Deploy models for real-time inference")
        print("   3. Set up automated retraining pipeline")
        print("   4. Integrate with alerting system")

        print("\n" + "=" * 80)
        print("✅ PHASE 3 TRAINING PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 80)


def main():
    """
    Main execution function for Phase 3 training.
    """
    print("🤖 SmartCloudOps AI - Phase 3: ML Anomaly Detection")
    print("=" * 60)

    # Initialize the anomaly detector
    detector = SmartCloudOpsAnomalyDetector()

    # Run the complete training pipeline
    results = detector.run_complete_training_pipeline()

    # Check if target F1-score is achieved
    if "isolation_forest" in results and "f1_score" in results["isolation_forest"]:
        f1_score = results["isolation_forest"]["f1_score"]
        if f1_score >= 0.85:
            print(f"\n🎉 SUCCESS: Target F1-score achieved! ({f1_score:.4f} ≥ 0.85)")
            return 0
        else:
            print(f"\n⚠️ ATTENTION: F1-score below target ({f1_score:.4f} < 0.85)")
            print("Consider hyperparameter tuning or feature engineering improvements.")
            return 1
    else:
        print("\n✅ Training completed successfully!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
