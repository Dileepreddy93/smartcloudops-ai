#!/usr/bin/env python3
"""
Simple mock training script for tests.
"""
import os
import pickle
import argparse


def main(save_path: str | None = None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--save_path", default=save_path, help="Path to save model")
    args = parser.parse_args(args=[]) if save_path is not None else parser.parse_args()

    target = args.save_path or "ml_models/anomaly_model.pkl"
    os.makedirs(os.path.dirname(target), exist_ok=True)

    # Create a dummy model object
    model = {"model": "dummy", "version": 1}
    with open(target, "wb") as f:
        pickle.dump(model, f)

    print(f"Model saved to {target}")


if __name__ == "__main__":
    main()
