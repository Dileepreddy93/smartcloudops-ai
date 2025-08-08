#!/usr/bin/env python3
"""
SmartCloudOps AI - Real Data Training Entrypoint
================================================

Runs Phase 3 training using real infrastructure data and persists models to
S3 (if configured) and local paths used by production inference.
"""

import os
import logging
from real_data_ml_trainer import RealDataMLTrainer


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    hours_back = int(os.getenv('TRAINING_HOURS_BACK', '24'))

    logger.info("🚀 Starting SmartCloudOps AI real-data training run")
    logger.info(f"⏱️ Hours back: {hours_back}")

    trainer = RealDataMLTrainer(use_real_data=True, fallback_to_synthetic=True)

    results = trainer.run_real_data_training_pipeline(hours_back=hours_back)

    if 'error' in results:
        logger.error(f"❌ Training failed: {results['error']}")
        return 1

    logger.info("✅ Training completed successfully")
    logger.info(f"📊 Data points: {results['data_summary']['total_points']}")
    if 'f1_score' in results['isolation_forest']:
        logger.info(f"🎯 F1-score: {results['isolation_forest']['f1_score']:.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


