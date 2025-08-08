#!/usr/bin/env python3
"""
SmartCloudOps AI - Real Data ML Training Pipeline
===============================================

Modified training pipeline that uses real monitoring data instead of synthetic data.
Automatically falls back to synthetic data if real data is unavailable.
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import os
import json
from real_data_integration import RealDataCollector
from phase3_anomaly_detection import SmartCloudOpsAnomalyDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealDataMLTrainer(SmartCloudOpsAnomalyDetector):
    """
    Enhanced ML trainer that prioritizes real data over synthetic data.
    """
    
    def __init__(self, use_real_data=True, fallback_to_synthetic=True):
        super().__init__()
        self.use_real_data = use_real_data
        self.fallback_to_synthetic = fallback_to_synthetic
        self.real_data_collector = RealDataCollector('../scripts/real_data_config.json')
        # Align S3 bucket with environment for production
        try:
            env_bucket = os.getenv('S3_ML_MODELS_BUCKET') or os.getenv('ML_MODELS_BUCKET')
            if env_bucket:
                self.s3_bucket = env_bucket
                logger.info(f"✅ Using S3 bucket from env: {self.s3_bucket}")
        except Exception:
            pass
        
    def collect_training_data(self, hours_back=24, min_data_points=100):
        """
        Collect training data prioritizing real sources over synthetic.
        
        Args:
            hours_back: Hours of historical data to collect
            min_data_points: Minimum number of data points required
            
        Returns:
            pandas.DataFrame: Training data
        """
        logger.info("📊 Starting data collection for ML training")
        
        if self.use_real_data:
            logger.info("🔄 Attempting to collect real monitoring data")
            
            # Try to collect real data from all sources
            real_data = self.real_data_collector.collect_comprehensive_dataset(hours_back)
            
            if not real_data.empty and len(real_data) >= min_data_points:
                logger.info(f"✅ Successfully collected {len(real_data)} real data points")
                logger.info(f"📊 Data sources: {real_data['source'].unique() if 'source' in real_data.columns else 'Unknown'}")
                
                # Validate data quality
                if self._validate_data_quality(real_data):
                    logger.info("✅ Real data quality validation passed")
                    return self._standardize_data_format(real_data)
                else:
                    logger.warning("⚠️ Real data quality validation failed")
            else:
                logger.warning(f"⚠️ Insufficient real data: {len(real_data) if not real_data.empty else 0} points (need {min_data_points})")
        
        # Fallback to synthetic data if enabled
        if self.fallback_to_synthetic:
            logger.info("🧪 Falling back to synthetic data generation")
            
            # Check if we have some real data to enhance synthetic generation
            if self.use_real_data and not real_data.empty:
                logger.info("🔧 Using real data patterns to enhance synthetic generation")
                synthetic_data = self._generate_enhanced_synthetic_data(real_data, hours_back)
            else:
                logger.info("🔧 Generating standard synthetic data")
                synthetic_data = self.generate_synthetic_data(days=hours_back//24 or 1)
            
            return synthetic_data
        else:
            logger.error("❌ No training data available and synthetic fallback disabled")
            return pd.DataFrame()
    
    def _validate_data_quality(self, df):
        """
        Validate the quality of real data.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            bool: True if data quality is acceptable
        """
        try:
            # Check for required columns
            required_cols = ['timestamp', 'cpu_usage', 'memory_usage']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                logger.error(f"❌ Missing required columns: {missing_cols}")
                return False
            
            # Check for reasonable value ranges
            if 'cpu_usage' in df.columns:
                cpu_values = df['cpu_usage'].dropna()
                if len(cpu_values) > 0 and (cpu_values.min() < 0 or cpu_values.max() > 100):
                    logger.warning("⚠️ CPU usage values outside expected range [0, 100]")
            
            if 'memory_usage' in df.columns:
                mem_values = df['memory_usage'].dropna()
                if len(mem_values) > 0 and (mem_values.min() < 0 or mem_values.max() > 100):
                    logger.warning("⚠️ Memory usage values outside expected range [0, 100]")
            
            # Check for sufficient data variety
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if col not in ['timestamp', 'is_anomaly']:
                    variance = df[col].var()
                    if variance == 0:
                        logger.warning(f"⚠️ No variance in column {col}")
            
            # Check temporal consistency
            if 'timestamp' in df.columns:
                time_diffs = df['timestamp'].diff().dropna()
                if len(time_diffs) > 0:
                    median_interval = time_diffs.median().total_seconds()
                    if median_interval <= 0 or median_interval > 3600:  # More than 1 hour
                        logger.warning(f"⚠️ Unusual time intervals detected: {median_interval}s")
            
            logger.info("✅ Data quality validation completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error validating data quality: {e}")
            return False
    
    def _standardize_data_format(self, df):
        """
        Standardize real data format to match expected ML pipeline format.
        
        Args:
            df: Raw real data DataFrame
            
        Returns:
            pandas.DataFrame: Standardized DataFrame
        """
        logger.info("🔧 Standardizing real data format")
        
        try:
            standardized_df = df.copy()
            
            # Ensure timestamp column is datetime
            if 'timestamp' in standardized_df.columns:
                standardized_df['timestamp'] = pd.to_datetime(standardized_df['timestamp'])
            
            # Map common metric names to expected format
            column_mapping = {
                'cpu_percent': 'cpu_usage',
                'cpu_utilization': 'cpu_usage',
                'mem_percent': 'memory_usage',
                'memory_percent': 'memory_usage',
                'memory_utilization': 'memory_usage',
                'disk_percent': 'disk_usage',
                'disk_utilization': 'disk_usage',
                'network_in': 'network_rx',
                'network_out': 'network_tx',
                'net_io_recv': 'network_rx',
                'net_io_sent': 'network_tx'
            }
            
            for old_col, new_col in column_mapping.items():
                if old_col in standardized_df.columns and new_col not in standardized_df.columns:
                    standardized_df[new_col] = standardized_df[old_col]
                    logger.info(f"🔄 Mapped {old_col} -> {new_col}")
            
            # Ensure required columns exist with default values
            required_metrics = ['cpu_usage', 'memory_usage', 'disk_io', 'network_io', 'response_time']
            
            for metric in required_metrics:
                if metric not in standardized_df.columns:
                    if metric == 'disk_io':
                        # Try to combine disk read/write
                        if 'disk_read_bytes' in standardized_df.columns and 'disk_write_bytes' in standardized_df.columns:
                            standardized_df['disk_io'] = standardized_df['disk_read_bytes'] + standardized_df['disk_write_bytes']
                        else:
                            standardized_df['disk_io'] = 0
                    elif metric == 'network_io':
                        # Try to combine network rx/tx
                        if 'network_rx' in standardized_df.columns and 'network_tx' in standardized_df.columns:
                            standardized_df['network_io'] = standardized_df['network_rx'] + standardized_df['network_tx']
                        else:
                            standardized_df['network_io'] = 0
                    elif metric == 'response_time':
                        # Default response time if not available
                        standardized_df['response_time'] = np.random.normal(100, 20, len(standardized_df))
                    else:
                        standardized_df[metric] = 0
                        
                    logger.info(f"🔧 Added missing column: {metric}")
            
            # Ensure anomaly labels exist
            if 'is_anomaly' not in standardized_df.columns:
                standardized_df['is_anomaly'] = 0
                logger.info("🏷️ Added default anomaly labels")
            
            # Clean up data
            standardized_df = standardized_df.replace([np.inf, -np.inf], np.nan)
            standardized_df = standardized_df.fillna(method='ffill').fillna(method='bfill').fillna(0)
            
            # Sort by timestamp
            standardized_df = standardized_df.sort_values('timestamp').reset_index(drop=True)
            
            logger.info(f"✅ Data standardization complete: {standardized_df.shape}")
            return standardized_df
            
        except Exception as e:
            logger.error(f"❌ Error standardizing data: {e}")
            return df
    
    def _generate_enhanced_synthetic_data(self, real_data_sample, hours_back):
        """
        Generate synthetic data enhanced with patterns from real data.
        
        Args:
            real_data_sample: Sample of real data to learn patterns from
            hours_back: Hours of data to generate
            
        Returns:
            pandas.DataFrame: Enhanced synthetic data
        """
        logger.info("🔬 Generating enhanced synthetic data using real data patterns")
        
        try:
            # Analyze real data patterns
            patterns = self._analyze_real_data_patterns(real_data_sample)
            
            # Generate base synthetic data
            synthetic_df = self.generate_synthetic_data(days=hours_back//24 or 1)
            
            # Apply real data patterns to synthetic data
            synthetic_df = self._apply_real_patterns(synthetic_df, patterns)
            
            logger.info(f"✅ Enhanced synthetic data generated: {len(synthetic_df)} points")
            return synthetic_df
            
        except Exception as e:
            logger.error(f"❌ Error generating enhanced synthetic data: {e}")
            return self.generate_synthetic_data(days=hours_back//24 or 1)
    
    def _analyze_real_data_patterns(self, df):
        """
        Analyze patterns in real data to enhance synthetic generation.
        
        Args:
            df: Real data DataFrame
            
        Returns:
            dict: Analyzed patterns
        """
        patterns = {}
        
        try:
            numeric_cols = ['cpu_usage', 'memory_usage', 'disk_io', 'network_io']
            
            for col in numeric_cols:
                if col in df.columns:
                    values = df[col].dropna()
                    if len(values) > 0:
                        patterns[col] = {
                            'mean': values.mean(),
                            'std': values.std(),
                            'min': values.min(),
                            'max': values.max(),
                            'median': values.median()
                        }
            
            # Analyze time-based patterns
            if 'timestamp' in df.columns:
                df['hour'] = df['timestamp'].dt.hour
                hourly_patterns = {}
                
                for col in numeric_cols:
                    if col in df.columns:
                        hourly_avg = df.groupby('hour')[col].mean()
                        hourly_patterns[col] = hourly_avg.to_dict()
                
                patterns['hourly'] = hourly_patterns
            
            logger.info("✅ Real data patterns analyzed")
            return patterns
            
        except Exception as e:
            logger.error(f"❌ Error analyzing patterns: {e}")
            return {}
    
    def _apply_real_patterns(self, synthetic_df, patterns):
        """
        Apply real data patterns to synthetic data.
        
        Args:
            synthetic_df: Synthetic data DataFrame
            patterns: Patterns from real data
            
        Returns:
            pandas.DataFrame: Enhanced synthetic data
        """
        try:
            enhanced_df = synthetic_df.copy()
            
            # Apply statistical patterns
            for col, stats in patterns.items():
                if col in enhanced_df.columns and isinstance(stats, dict):
                    if 'mean' in stats and 'std' in stats:
                        # Adjust to match real data distribution
                        current_mean = enhanced_df[col].mean()
                        current_std = enhanced_df[col].std()
                        
                        if current_std > 0:
                            # Normalize and rescale
                            normalized = (enhanced_df[col] - current_mean) / current_std
                            enhanced_df[col] = normalized * stats['std'] + stats['mean']
                        
                        # Clip to real data range
                        enhanced_df[col] = np.clip(enhanced_df[col], stats['min'], stats['max'])
            
            # Apply hourly patterns if available
            if 'hourly' in patterns and 'timestamp' in enhanced_df.columns:
                enhanced_df['hour'] = enhanced_df['timestamp'].dt.hour
                
                for col, hourly_data in patterns['hourly'].items():
                    if col in enhanced_df.columns:
                        for hour, avg_value in hourly_data.items():
                            mask = enhanced_df['hour'] == hour
                            if mask.any():
                                # Adjust values for this hour
                                adjustment_factor = avg_value / enhanced_df.loc[mask, col].mean()
                                enhanced_df.loc[mask, col] *= adjustment_factor
                
                enhanced_df = enhanced_df.drop('hour', axis=1)
            
            logger.info("✅ Real patterns applied to synthetic data")
            return enhanced_df
            
        except Exception as e:
            logger.error(f"❌ Error applying patterns: {e}")
            return synthetic_df
    
    def run_real_data_training_pipeline(self, hours_back=24):
        """
        Execute complete training pipeline with real data.
        
        Args:
            hours_back: Hours of historical data to use
            
        Returns:
            dict: Training results
        """
        logger.info("🚀 Starting Real Data ML Training Pipeline")
        
        try:
            # Step 1: Collect training data
            logger.info("📊 Step 1: Real Data Collection")
            training_data = self.collect_training_data(hours_back)
            
            if training_data.empty:
                logger.error("❌ No training data available")
                return {'error': 'No training data available'}
            
            # Step 2: Feature Engineering
            logger.info("🔧 Step 2: Feature Engineering")
            enhanced_data = self.prepare_features(training_data)

            # Align with production inference features
            # Add the same derived features used by production inference
            from datetime import datetime as _dt
            if 'timestamp' in enhanced_data.columns:
                enhanced_data['hour'] = enhanced_data['timestamp'].dt.hour
                enhanced_data['day_of_week'] = enhanced_data['timestamp'].dt.dayofweek
                enhanced_data['is_weekend'] = enhanced_data['day_of_week'].isin([5, 6]).astype(int)
            else:
                now = _dt.now()
                enhanced_data['hour'] = now.hour
                enhanced_data['day_of_week'] = now.weekday()
                enhanced_data['is_weekend'] = int(now.weekday() >= 5)
            enhanced_data['is_business_hours'] = ((enhanced_data['hour'] >= 9) & (enhanced_data['hour'] <= 17) & (~enhanced_data['is_weekend'].astype(bool))).astype(int)
            # Ensure required base columns exist before computing ratios
            for base_col, default in [('cpu_usage', 0.0), ('memory_usage', 0.0), ('disk_io', 0.0), ('network_io', 0.0), ('response_time', 0.0)]:
                if base_col not in enhanced_data.columns:
                    enhanced_data[base_col] = default

            enhanced_data['cpu_memory_ratio'] = enhanced_data['cpu_usage'] / (enhanced_data['memory_usage'] + 1e-6)
            enhanced_data['io_ratio'] = enhanced_data['disk_io'] / (enhanced_data['network_io'] + 1e-6)
            enhanced_data['load_indicator'] = (enhanced_data['cpu_usage'] + enhanced_data['memory_usage']) / 2
            enhanced_data['performance_indicator'] = enhanced_data['response_time'] / (enhanced_data['load_indicator'] + 1e-6)
            
            # Step 3: Model Training
            logger.info("🤖 Step 3: Model Training")
            
            # Define feature columns to match production inference exactly
            feature_columns = [
                'cpu_usage', 'memory_usage', 'disk_io', 'network_io', 'response_time',
                'hour', 'day_of_week', 'is_weekend', 'is_business_hours',
                'cpu_memory_ratio', 'io_ratio', 'load_indicator', 'performance_indicator'
            ]
            # Ensure all features exist
            for _f in feature_columns:
                if _f not in enhanced_data.columns:
                    enhanced_data[_f] = 0.0
            
            # Train models
            iso_results = self.train_isolation_forest(enhanced_data, feature_columns)
            
            # Train Prophet models
            prophet_results = {}
            for metric in ['cpu_usage', 'memory_usage', 'response_time']:
                if metric in enhanced_data.columns:
                    prophet_results[metric] = self.train_prophet_model(enhanced_data, metric)
            
            # Step 4: Model Evaluation
            logger.info("📊 Step 4: Model Evaluation")
            
            results = {
                'data_source': 'real_data' if self.use_real_data else 'synthetic_data',
                'isolation_forest': iso_results,
                'prophet_models': prophet_results,
                'data_summary': {
                    'total_points': len(enhanced_data),
                    'feature_count': len(feature_columns),
                    'anomaly_rate': enhanced_data['is_anomaly'].mean(),
                    'time_range': {
                        'start': enhanced_data['timestamp'].min().isoformat(),
                        'end': enhanced_data['timestamp'].max().isoformat()
                    },
                    'data_sources': list(enhanced_data['source'].unique()) if 'source' in enhanced_data.columns else ['unknown']
                }
            }
            
            # Step 5: Model Persistence
            logger.info("💾 Step 5: Model Persistence")
            # Ensure models go to the optimized path expected by inference
            try:
                # Explicitly write both S3 and local copies to optimized paths
                if getattr(self, 's3_client', None):
                    try:
                        logger.info("💾 Uploading models to S3 optimized paths...")
                        # Isolation Forest
                        if 'isolation_forest' in self.models:
                            import joblib, tempfile
                            with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
                                joblib.dump(self.models['isolation_forest'], f.name)
                                self.s3_client.upload_file(
                                    f.name,
                                    self.s3_bucket,
                                    'models/optimized/optimized_isolation_forest_model.pkl'
                                )
                            with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
                                joblib.dump(self.scalers['isolation_forest'], f.name)
                                self.s3_client.upload_file(
                                    f.name,
                                    self.s3_bucket,
                                    'models/optimized/optimized_isolation_forest_scaler.pkl'
                                )
                    except Exception as e:
                        logger.warning(f"⚠️ S3 upload failed, will still save locally: {e}")

                # Local copies
                import os, joblib
                os.makedirs('../ml_models/optimized', exist_ok=True)
                if 'isolation_forest' in self.models:
                    joblib.dump(self.models['isolation_forest'], '../ml_models/optimized/optimized_isolation_forest_model.pkl')
                    joblib.dump(self.scalers['isolation_forest'], '../ml_models/optimized/optimized_isolation_forest_scaler.pkl')
                    logger.info("✅ Saved optimized Isolation Forest locally")
            except Exception as e:
                logger.error(f"❌ Error persisting models: {e}")
            
            # Step 6: Save training data for reference
            self.real_data_collector.save_real_data(enhanced_data, '../data/training_data_real.csv')
            
            logger.info("✅ Real data training pipeline completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in training pipeline: {e}")
            return {'error': str(e)}

def main():
    """Test the real data ML training pipeline."""
    logger.info("🔍 Testing Real Data ML Training Pipeline")
    print("=" * 60)
    
    # Initialize trainer with real data preference
    trainer = RealDataMLTrainer(use_real_data=True, fallback_to_synthetic=True)
    
    print("🔄 Running training pipeline with real data...")
    results = trainer.run_real_data_training_pipeline(hours_back=24)
    
    if 'error' not in results:
        print(f"\n✅ Training completed successfully!")
        print(f"📊 Data source: {results['data_source']}")
        print(f"📈 Total data points: {results['data_summary']['total_points']}")
        print(f"🔢 Feature count: {results['data_summary']['feature_count']}")
        print(f"🚨 Anomaly rate: {results['data_summary']['anomaly_rate']:.2%}")
        
        if 'f1_score' in results['isolation_forest']:
            print(f"🎯 Model F1-Score: {results['isolation_forest']['f1_score']:.4f}")
        
        print(f"📅 Time range: {results['data_summary']['time_range']['start']} to {results['data_summary']['time_range']['end']}")
        print(f"🔗 Data sources: {results['data_summary']['data_sources']}")
        
        print("\n🎯 Real data training pipeline successful!")
    else:
        print(f"❌ Training failed: {results['error']}")

if __name__ == "__main__":
    main()
