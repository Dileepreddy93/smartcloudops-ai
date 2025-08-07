#!/usr/bin/env python3
"""
SmartCloudOps AI - Data Migration Tool
====================================

Tool to help migrate from synthetic data to real data sources.
Provides step-by-step guidance and validation.
"""

import os
import json
import logging
from datetime import datetime
from real_data_integration import RealDataCollector
from real_data_ml_trainer import RealDataMLTrainer
from prometheus_collector import PrometheusCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataMigrationTool:
    """
    Tool to help users migrate from synthetic to real data.
    """
    
    def __init__(self):
        self.data_sources_status = {}
        
    def check_data_source_availability(self):
        """
        Check which real data sources are available.
        
        Returns:
            dict: Status of each data source
        """
        logger.info("🔍 Checking availability of real data sources...")
        
        # 1. Check Prometheus
        try:
            prometheus = PrometheusCollector()
            self.data_sources_status['prometheus'] = {
                'available': prometheus.test_connection(),
                'url': prometheus.prometheus_url,
                'priority': 'high'
            }
        except Exception as e:
            self.data_sources_status['prometheus'] = {
                'available': False,
                'error': str(e),
                'priority': 'high'
            }
        
        # 2. Check System metrics (always available)
        self.data_sources_status['system'] = {
            'available': True,
            'description': 'Local system metrics using psutil',
            'priority': 'medium'
        }
        
        # 3. Check AWS CloudWatch
        try:
            import boto3
            cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
            # Try a simple API call
            cloudwatch.describe_alarms(MaxRecords=1)
            self.data_sources_status['cloudwatch'] = {
                'available': True,
                'description': 'AWS CloudWatch metrics',
                'priority': 'medium'
            }
        except Exception as e:
            self.data_sources_status['cloudwatch'] = {
                'available': False,
                'error': str(e),
                'priority': 'medium'
            }
        
        # 4. Check for CSV files
        csv_paths = ['../data/', '/var/log/metrics/', './metrics.csv']
        csv_found = any(os.path.exists(path) for path in csv_paths)
        self.data_sources_status['csv'] = {
            'available': csv_found,
            'paths_checked': csv_paths,
            'priority': 'low'
        }
        
        # 5. Check for log files
        log_paths = ['/var/log/', '../logs/', './app.log']
        log_found = any(os.path.exists(path) for path in log_paths)
        self.data_sources_status['log'] = {
            'available': log_found,
            'paths_checked': log_paths,
            'priority': 'low'
        }
        
        return self.data_sources_status
    
    def print_migration_report(self):
        """Print detailed migration report."""
        print("\n" + "="*60)
        print("📊 REAL DATA MIGRATION ASSESSMENT")
        print("="*60)
        
        available_sources = []
        unavailable_sources = []
        
        for source, status in self.data_sources_status.items():
            if status['available']:
                available_sources.append((source, status))
                print(f"✅ {source.upper()}: Available")
                if 'description' in status:
                    print(f"   📝 {status['description']}")
                if 'url' in status:
                    print(f"   🔗 URL: {status['url']}")
            else:
                unavailable_sources.append((source, status))
                print(f"❌ {source.upper()}: Not Available")
                if 'error' in status:
                    print(f"   ⚠️ Error: {status['error']}")
        
        print(f"\n📈 SUMMARY:")
        print(f"   ✅ Available sources: {len(available_sources)}")
        print(f"   ❌ Unavailable sources: {len(unavailable_sources)}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        if self.data_sources_status.get('prometheus', {}).get('available'):
            print("   🎯 PRIMARY: Use Prometheus data (best quality, real-time)")
        elif self.data_sources_status.get('system', {}).get('available'):
            print("   🎯 PRIMARY: Use system metrics (local, reliable)")
        else:
            print("   ⚠️ No high-quality data sources available")
        
        if self.data_sources_status.get('cloudwatch', {}).get('available'):
            print("   📊 SECONDARY: CloudWatch provides cloud infrastructure metrics")
        
        if self.data_sources_status.get('csv', {}).get('available'):
            print("   📄 BACKUP: CSV files can supplement other sources")
        
        if len(available_sources) == 0:
            print("   🧪 FALLBACK: Continue using synthetic data with real patterns")
    
    def create_migration_config(self, output_path='../scripts/migration_config.json'):
        """
        Create a configuration file for data migration.
        
        Args:
            output_path: Path to save the configuration
        """
        config = {
            "migration_settings": {
                "created_at": datetime.now().isoformat(),
                "use_real_data": True,
                "fallback_to_synthetic": True,
                "data_source_priority": []
            },
            "data_sources": {}
        }
        
        # Add available sources in priority order
        priority_order = ['prometheus', 'system', 'cloudwatch', 'csv', 'log']
        
        for source in priority_order:
            if source in self.data_sources_status and self.data_sources_status[source]['available']:
                config['migration_settings']['data_source_priority'].append(source)
                config['data_sources'][source] = {
                    'enabled': True,
                    'status': 'available'
                }
            else:
                config['data_sources'][source] = {
                    'enabled': False,
                    'status': 'unavailable'
                }
        
        # Training settings
        config['training'] = {
            "hours_back": 24,
            "min_data_points": 100,
            "validation_enabled": True,
            "enhanced_synthetic": True
        }
        
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"✅ Migration configuration saved to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"❌ Error saving configuration: {e}")
            return None
    
    def test_real_data_collection(self):
        """
        Test real data collection with current configuration.
        
        Returns:
            dict: Test results
        """
        print("\n🧪 TESTING REAL DATA COLLECTION")
        print("-" * 40)
        
        try:
            # Initialize collector
            collector = RealDataCollector()
            
            # Test data collection
            test_data = collector.collect_comprehensive_dataset(hours_back=1)
            
            if not test_data.empty:
                results = {
                    'success': True,
                    'data_points': len(test_data),
                    'columns': list(test_data.columns),
                    'sources': list(test_data['source'].unique()) if 'source' in test_data.columns else [],
                    'time_range': {
                        'start': test_data['timestamp'].min(),
                        'end': test_data['timestamp'].max()
                    } if 'timestamp' in test_data.columns else {}
                }
                
                print(f"✅ Successfully collected {results['data_points']} data points")
                print(f"📊 Columns: {len(results['columns'])}")
                print(f"🔗 Sources: {results['sources']}")
                
                return results
            else:
                print("❌ No real data collected")
                return {'success': False, 'error': 'No data collected'}
                
        except Exception as e:
            print(f"❌ Error testing data collection: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_migration_test(self):
        """
        Run complete migration test including ML training.
        
        Returns:
            dict: Migration test results
        """
        print("\n🚀 RUNNING COMPLETE MIGRATION TEST")
        print("-" * 50)
        
        try:
            # Initialize trainer
            trainer = RealDataMLTrainer(use_real_data=True, fallback_to_synthetic=True)
            
            # Run training pipeline
            results = trainer.run_real_data_training_pipeline(hours_back=2)
            
            if 'error' not in results:
                print("✅ Migration test successful!")
                print(f"📊 Data source: {results['data_source']}")
                print(f"📈 Training points: {results['data_summary']['total_points']}")
                print(f"🔢 Features: {results['data_summary']['feature_count']}")
                
                if 'f1_score' in results['isolation_forest']:
                    print(f"🎯 Model F1-Score: {results['isolation_forest']['f1_score']:.4f}")
                
                return {'success': True, 'results': results}
            else:
                print(f"❌ Migration test failed: {results['error']}")
                return {'success': False, 'error': results['error']}
                
        except Exception as e:
            print(f"❌ Error in migration test: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_migration_instructions(self):
        """Generate step-by-step migration instructions."""
        instructions = f"""
🔄 MIGRATION FROM SYNTHETIC TO REAL DATA
=========================================

Based on your system analysis, here's your migration plan:

STEP 1: IMMEDIATE ACTIONS
-------------------------
"""
        
        if self.data_sources_status.get('prometheus', {}).get('available'):
            instructions += """
✅ Prometheus is available - this is your best option!
   • High-quality, real-time infrastructure metrics
   • Already configured and operational
   • No additional setup required
"""
        else:
            instructions += """
❌ Prometheus not available
   • Check if Prometheus is running on http://3.89.229.102:9090
   • Verify network connectivity
   • Consider setting up Prometheus monitoring
"""
        
        instructions += """
STEP 2: UPDATE YOUR TRAINING SCRIPTS
-----------------------------------
Replace your current training calls:

OLD (Synthetic):
    detector = SmartCloudOpsAnomalyDetector()
    results = detector.run_complete_training_pipeline()

NEW (Real Data):
    trainer = RealDataMLTrainer(use_real_data=True, fallback_to_synthetic=True)
    results = trainer.run_real_data_training_pipeline(hours_back=24)

STEP 3: VERIFY DATA QUALITY
---------------------------
Run the data collection test:
    python scripts/real_data_integration.py

STEP 4: UPDATE PRODUCTION INFERENCE
----------------------------------
The production inference system will automatically use the new models
trained on real data.

STEP 5: MONITOR RESULTS
----------------------
• Check model performance metrics
• Verify anomaly detection accuracy
• Monitor for data quality issues

FALLBACK STRATEGY
-----------------
If real data collection fails, the system will automatically:
• Fall back to enhanced synthetic data
• Use real data patterns to improve synthetic generation
• Maintain model training pipeline functionality
"""
        
        return instructions

def main():
    """Run the complete data migration assessment."""
    print("🔄 SMARTCLOUDOPS AI - DATA MIGRATION TOOL")
    print("=" * 50)
    
    # Initialize migration tool
    migration_tool = DataMigrationTool()
    
    # Step 1: Check data source availability
    print("Step 1: Checking data source availability...")
    migration_tool.check_data_source_availability()
    migration_tool.print_migration_report()
    
    # Step 2: Create migration configuration
    print("\nStep 2: Creating migration configuration...")
    config_path = migration_tool.create_migration_config()
    
    # Step 3: Test real data collection
    print("\nStep 3: Testing real data collection...")
    collection_results = migration_tool.test_real_data_collection()
    
    # Step 4: Run migration test
    if collection_results.get('success'):
        print("\nStep 4: Running complete migration test...")
        migration_results = migration_tool.run_migration_test()
    else:
        print("\nStep 4: Skipping migration test (no real data available)")
        migration_results = {'success': False}
    
    # Step 5: Generate instructions
    print("\nStep 5: Generating migration instructions...")
    instructions = migration_tool.generate_migration_instructions()
    
    # Save instructions to file
    try:
        with open('../docs/MIGRATION_INSTRUCTIONS.md', 'w') as f:
            f.write(instructions)
        print("📄 Migration instructions saved to ../docs/MIGRATION_INSTRUCTIONS.md")
    except Exception as e:
        print(f"⚠️ Could not save instructions: {e}")
    
    # Final summary
    print("\n" + "="*60)
    print("📋 MIGRATION SUMMARY")
    print("="*60)
    
    if migration_results.get('success'):
        print("✅ MIGRATION READY: All tests passed!")
        print("🚀 You can now use real data in your ML pipeline")
        print("📝 Follow the generated migration instructions")
    else:
        print("⚠️ PARTIAL MIGRATION: Some data sources available")
        print("🔧 System will use available sources + synthetic fallback")
        print("📋 Check migration instructions for next steps")
    
    print(f"\n📄 Configuration saved to: {config_path}")
    print("📖 Read migration instructions for detailed steps")

if __name__ == "__main__":
    main()
