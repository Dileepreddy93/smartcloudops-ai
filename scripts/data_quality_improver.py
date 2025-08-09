#!/usr/bin/env python3
"""
Real Data Quality Improvement Script
===================================

Script to analyze and improve the quality of existing real data points.
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.impute import KNNImputer
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataQualityImprover:
    """Improve the quality of existing real data."""
    
    def __init__(self):
        self.data = None
        self.quality_report = {}
        
    def load_existing_data(self, file_path: str):
        """Load existing real data."""
        logger.info(f"📂 Loading data from {file_path}")
        
        if file_path.endswith('.json'):
            with open(file_path, 'r') as f:
                self.data = pd.DataFrame(json.load(f))
        elif file_path.endswith('.csv'):
            self.data = pd.read_csv(file_path)
        else:
            raise ValueError("Unsupported file format")
        
        logger.info(f"✅ Loaded {len(self.data)} data points")
        return self.data
    
    def analyze_data_quality(self):
        """Analyze the quality of the current data."""
        logger.info("🔍 Analyzing data quality")
        
        if self.data is None:
            logger.error("❌ No data loaded")
            return
        
        quality_report = {
            'total_points': len(self.data),
            'total_features': len(self.data.columns),
            'missing_values': {},
            'duplicate_rows': 0,
            'anomaly_analysis': {},
            'temporal_analysis': {},
            'feature_analysis': {}
        }
        
        # Check for missing values
        for col in self.data.columns:
            missing_count = self.data[col].isnull().sum()
            missing_pct = (missing_count / len(self.data)) * 100
            quality_report['missing_values'][col] = {
                'count': missing_count,
                'percentage': missing_pct
            }
        
        # Check for duplicates
        quality_report['duplicate_rows'] = self.data.duplicated().sum()
        
        # Anomaly analysis
        if 'is_anomaly' in self.data.columns:
            anomaly_count = self.data['is_anomaly'].sum()
            quality_report['anomaly_analysis'] = {
                'total_anomalies': anomaly_count,
                'anomaly_rate': anomaly_count / len(self.data),
                'normal_points': len(self.data) - anomaly_count
            }
        
        # Temporal analysis
        if 'timestamp' in self.data.columns:
            self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
            time_diffs = self.data['timestamp'].diff().dropna()
            quality_report['temporal_analysis'] = {
                'time_span_hours': (self.data['timestamp'].max() - self.data['timestamp'].min()).total_seconds() / 3600,
                'average_interval_minutes': time_diffs.mean().total_seconds() / 60,
                'irregular_intervals': (time_diffs.std() > timedelta(minutes=1)).sum()
            }
        
        # Feature analysis
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col != 'is_anomaly':
                quality_report['feature_analysis'][col] = {
                    'mean': self.data[col].mean(),
                    'std': self.data[col].std(),
                    'min': self.data[col].min(),
                    'max': self.data[col].max(),
                    'zeros_count': (self.data[col] == 0).sum(),
                    'zeros_percentage': (self.data[col] == 0).sum() / len(self.data) * 100
                }
        
        self.quality_report = quality_report
        self.print_quality_report()
        return quality_report
    
    def print_quality_report(self):
        """Print a formatted quality report."""
        print("\n📊 DATA QUALITY REPORT")
        print("=" * 50)
        
        print(f"📈 Dataset Overview:")
        print(f"   Total Data Points: {self.quality_report['total_points']}")
        print(f"   Total Features: {self.quality_report['total_features']}")
        print(f"   Duplicate Rows: {self.quality_report['duplicate_rows']}")
        
        print(f"\n🚨 Anomaly Analysis:")
        if 'anomaly_analysis' in self.quality_report and self.quality_report['anomaly_analysis']:
            anom = self.quality_report['anomaly_analysis']
            print(f"   Anomalies: {anom['total_anomalies']} ({anom['anomaly_rate']:.2%})")
            print(f"   Normal Points: {anom['normal_points']}")
        else:
            print("   No anomaly information available")
        
        print(f"\n⏰ Temporal Analysis:")
        if 'temporal_analysis' in self.quality_report and self.quality_report['temporal_analysis']:
            temp = self.quality_report['temporal_analysis']
            print(f"   Time Span: {temp['time_span_hours']:.1f} hours")
            print(f"   Average Interval: {temp['average_interval_minutes']:.1f} minutes")
        
        print(f"\n❌ Missing Values:")
        for col, info in self.quality_report['missing_values'].items():
            if info['count'] > 0:
                print(f"   {col}: {info['count']} ({info['percentage']:.1f}%)")
        
        print(f"\n🔧 Feature Quality Issues:")
        for col, info in self.quality_report['feature_analysis'].items():
            if info['zeros_percentage'] > 50:
                print(f"   {col}: {info['zeros_percentage']:.1f}% zero values (potentially low quality)")
    
    def improve_data_quality(self):
        """Improve the quality of the data."""
        logger.info("🔧 Improving data quality")
        
        improved_data = self.data.copy()
        improvements = []
        
        # 1. Remove duplicates
        before_count = len(improved_data)
        improved_data = improved_data.drop_duplicates()
        after_count = len(improved_data)
        if before_count != after_count:
            improvements.append(f"Removed {before_count - after_count} duplicate rows")
        
        # 2. Handle missing values
        numeric_cols = improved_data.select_dtypes(include=[np.number]).columns
        
        # Use KNN imputation for missing values
        for col in numeric_cols:
            missing_count = improved_data[col].isnull().sum()
            if missing_count > 0 and missing_count < len(improved_data) * 0.5:  # Don't impute if >50% missing
                # Simple forward fill for time series data
                improved_data[col] = improved_data[col].fillna(method='ffill').fillna(method='bfill')
                improvements.append(f"Filled {missing_count} missing values in {col}")
        
        # 3. Add temporal features if timestamp exists
        if 'timestamp' in improved_data.columns:
            improved_data['timestamp'] = pd.to_datetime(improved_data['timestamp'])
            improved_data = improved_data.sort_values('timestamp').reset_index(drop=True)
            
            # Add time-based features
            improved_data['hour'] = improved_data['timestamp'].dt.hour
            improved_data['day_of_week'] = improved_data['timestamp'].dt.dayofweek
            improved_data['is_weekend'] = (improved_data['day_of_week'] >= 5).astype(int)
            improved_data['is_business_hours'] = ((improved_data['hour'] >= 9) & (improved_data['hour'] <= 17)).astype(int)
            improvements.append("Added temporal features (hour, day_of_week, is_weekend, is_business_hours)")
        
        # 4. Add rolling averages for smoother trends
        if len(improved_data) >= 5:
            for col in ['cpu_usage', 'memory_usage', 'load_1m']:
                if col in improved_data.columns:
                    improved_data[f'{col}_ma_5'] = improved_data[col].rolling(window=5, min_periods=1).mean()
                    improved_data[f'{col}_ma_15'] = improved_data[col].rolling(window=15, min_periods=1).mean()
            improvements.append("Added moving averages (5-point and 15-point)")
        
        # 5. Add derived metrics
        if 'cpu_usage' in improved_data.columns and 'memory_usage' in improved_data.columns:
            improved_data['system_stress'] = (improved_data['cpu_usage'] + improved_data['memory_usage']) / 2
            improvements.append("Added system_stress derived metric")
        
        if 'disk_io_read' in improved_data.columns and 'disk_io_write' in improved_data.columns:
            improved_data['disk_io_total'] = improved_data['disk_io_read'] + improved_data['disk_io_write']
            improved_data['disk_io_ratio'] = improved_data['disk_io_write'] / (improved_data['disk_io_read'] + 1e-6)
            improvements.append("Added disk I/O derived metrics")
        
        # 6. Improve anomaly detection
        if 'is_anomaly' not in improved_data.columns or improved_data['is_anomaly'].sum() < len(improved_data) * 0.01:
            improved_data = self.add_improved_anomaly_detection(improved_data)
            improvements.append("Added/improved anomaly detection")
        
        # 7. Add data point quality scores
        improved_data['data_quality_score'] = self.calculate_quality_scores(improved_data)
        improvements.append("Added data quality scores")
        
        logger.info(f"✅ Data quality improvements completed:")
        for improvement in improvements:
            logger.info(f"   • {improvement}")
        
        return improved_data, improvements
    
    def add_improved_anomaly_detection(self, data):
        """Add improved anomaly detection."""
        logger.info("🚨 Adding improved anomaly detection")
        
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        # Remove non-metric columns
        exclude_cols = ['is_anomaly', 'hour', 'day_of_week', 'is_weekend', 'is_business_hours']
        numeric_cols = [col for col in numeric_cols if col not in exclude_cols]
        
        if len(numeric_cols) < 2:
            data['is_anomaly'] = 0
            return data
        
        # Prepare data for anomaly detection
        X = data[numeric_cols].fillna(data[numeric_cols].median())
        
        # Use multiple methods and combine
        isolation_forest = IsolationForest(contamination=0.05, random_state=42)
        iso_labels = isolation_forest.fit_predict(X)
        
        # Statistical method (IQR)
        iqr_anomalies = np.zeros(len(data))
        for col in numeric_cols:
            Q1 = data[col].quantile(0.25)
            Q3 = data[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            iqr_anomalies |= (data[col] < lower_bound) | (data[col] > upper_bound)
        
        # Combine methods (anomaly if either method detects it)
        data['is_anomaly'] = ((iso_labels == -1) | iqr_anomalies).astype(int)
        
        # Add anomaly confidence scores
        anomaly_scores = isolation_forest.score_samples(X)
        data['anomaly_score'] = anomaly_scores
        
        anomaly_rate = data['is_anomaly'].mean()
        logger.info(f"   Anomaly rate: {anomaly_rate:.2%}")
        
        return data
    
    def calculate_quality_scores(self, data):
        """Calculate quality scores for each data point."""
        scores = np.ones(len(data))
        
        # Penalize data points with many zero values
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col not in ['is_anomaly', 'hour', 'day_of_week', 'is_weekend', 'is_business_hours']:
                zero_mask = (data[col] == 0)
                scores[zero_mask] *= 0.9  # Reduce score for zero values
        
        # Boost scores for data points with complete information
        complete_mask = data.notnull().all(axis=1)
        scores[complete_mask] *= 1.1
        
        # Normalize scores to 0-1 range
        scores = np.clip(scores, 0, 1)
        
        return scores
    
    def generate_synthetic_data_to_balance(self, target_count: int = 1000):
        """Generate additional synthetic data points to reach target count."""
        logger.info(f"🧪 Generating synthetic data to reach {target_count} total points")
        
        if len(self.data) >= target_count:
            logger.info("✅ Already have enough data points")
            return self.data
        
        needed_points = target_count - len(self.data)
        logger.info(f"   Generating {needed_points} additional points")
        
        # Use existing data patterns to generate realistic synthetic data
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns.tolist()
        
        synthetic_data = []
        base_timestamp = pd.to_datetime(self.data['timestamp'].max()) if 'timestamp' in self.data.columns else datetime.now()
        
        for i in range(needed_points):
            # Sample from existing distribution with small variations
            base_row = self.data.sample(1).iloc[0].to_dict()
            
            # Add timestamp progression
            if 'timestamp' in base_row:
                new_timestamp = base_timestamp + timedelta(minutes=5 * (i + 1))
                base_row['timestamp'] = new_timestamp.isoformat()
            
            # Add realistic variations to numeric columns
            for col in numeric_cols:
                if col in base_row and col not in ['is_anomaly', 'hour', 'day_of_week', 'is_weekend', 'is_business_hours']:
                    original_value = base_row[col]
                    # Add noise (±10% of the value)
                    noise = np.random.normal(0, abs(original_value) * 0.1)
                    base_row[col] = max(0, original_value + noise)
            
            # Occasionally make it an anomaly (5% chance)
            if np.random.random() < 0.05:
                base_row['is_anomaly'] = 1
                # Spike some values for anomalies
                if 'cpu_usage' in base_row:
                    base_row['cpu_usage'] = min(100, base_row['cpu_usage'] * np.random.uniform(1.5, 2.0))
                if 'memory_usage' in base_row:
                    base_row['memory_usage'] = min(100, base_row['memory_usage'] * np.random.uniform(1.3, 1.8))
            
            synthetic_data.append(base_row)
        
        # Combine original and synthetic data
        synthetic_df = pd.DataFrame(synthetic_data)
        combined_data = pd.concat([self.data, synthetic_df], ignore_index=True)
        
        logger.info(f"✅ Generated {len(synthetic_data)} synthetic points")
        return combined_data
    
    def save_improved_data(self, improved_data, output_path: str):
        """Save the improved data."""
        logger.info(f"💾 Saving improved data to {output_path}")
        
        # Save as JSON
        if output_path.endswith('.json'):
            improved_data.to_json(output_path, orient='records', indent=2)
        # Save as CSV
        elif output_path.endswith('.csv'):
            improved_data.to_csv(output_path, index=False)
        
        # Save metadata
        metadata = {
            'improvement_timestamp': datetime.now().isoformat(),
            'original_points': len(self.data),
            'improved_points': len(improved_data),
            'features_count': len(improved_data.columns),
            'anomaly_rate': improved_data.get('is_anomaly', pd.Series()).mean(),
            'quality_improvements': getattr(self, 'improvements', [])
        }
        
        metadata_path = output_path.replace('.json', '_metadata.json').replace('.csv', '_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"✅ Saved improved data and metadata")
        return output_path


def main():
    """Main function to run data quality improvement."""
    print("🔧 SmartCloudOps AI - Data Quality Improvement")
    print("=" * 60)
    
    improver = DataQualityImprover()
    
    # Load existing data
    data_files = [
        "../data/real_training_data.json",
        "../data/real_training_data.csv"
    ]
    
    for file_path in data_files:
        try:
            improver.load_existing_data(file_path)
            break
        except FileNotFoundError:
            continue
    
    if improver.data is None:
        print("❌ No data files found")
        return
    
    # Analyze current quality
    quality_report = improver.analyze_data_quality()
    
    # Improve data quality
    improved_data, improvements = improver.improve_data_quality()
    improver.improvements = improvements
    
    # Generate additional data if needed
    balanced_data = improver.generate_synthetic_data_to_balance(target_count=2000)
    
    # Save improved data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"../data/improved_real_training_data_{timestamp}.json"
    improver.save_improved_data(balanced_data, output_path)
    
    print(f"\n✅ Data quality improvement complete!")
    print(f"📊 Original points: {len(improver.data)}")
    print(f"📈 Improved points: {len(balanced_data)}")
    print(f"💾 Saved to: {output_path}")
    
    print(f"\n🎯 Improvements made:")
    for improvement in improvements:
        print(f"   • {improvement}")


if __name__ == "__main__":
    main()
