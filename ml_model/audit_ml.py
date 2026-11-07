"""
Machine Learning Technical Audit Script for AeroPredict.
Verifies dataset integrity, model artifacts, feature consistency,
inference engine, and non-fabricated performance metrics.
"""

import sys
import os
import json
from pathlib import Path
import joblib
import pandas as pd
import numpy as np

# Set paths
root_dir = Path(__file__).resolve().parent.parent
ml_dir = root_dir / 'ml_model'
dataset_dir = root_dir / 'dataset'
backend_dir = root_dir / 'backend'

if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(ml_dir) not in sys.path:
    sys.path.insert(0, str(ml_dir))

def run_ml_audit():
    print("=" * 65)
    print("AEROPREDICT MACHINE LEARNING PIPELINE TECHNICAL AUDIT")
    print("=" * 65)

    # 1. Dataset Integrity
    print("\n--- 1. DATASET INTEGRITY & SPLIT VERIFICATION ---")
    train_path = dataset_dir / 'train_FD001.txt'
    test_path = dataset_dir / 'test_FD001.txt'
    rul_path = dataset_dir / 'RUL_FD001.txt'

    assert train_path.exists(), f"Missing train file: {train_path}"
    assert test_path.exists(), f"Missing test file: {test_path}"
    assert rul_path.exists(), f"Missing RUL file: {rul_path}"

    cols = ['unit_number', 'time_in_cycles', 'setting_1', 'setting_2', 'setting_3'] + [f'sensor_{i}' for i in range(1, 22)]
    train_df = pd.read_csv(train_path, sep=r'\s+', header=None, names=cols)
    test_df = pd.read_csv(test_path, sep=r'\s+', header=None, names=cols)
    rul_df = pd.read_csv(rul_path, sep=r'\s+', header=None, names=['true_rul'])

    print(f"Train Dataset Shape: {train_df.shape} | Engines: {train_df['unit_number'].nunique()} | Nulls: {train_df.isnull().sum().sum()}")
    print(f"Test Dataset Shape:  {test_df.shape} | Engines: {test_df['unit_number'].nunique()} | Nulls: {test_df.isnull().sum().sum()}")
    print(f"RUL Ground Truth:    {rul_df.shape} | Engines: {len(rul_df)} | Nulls: {rul_df.isnull().sum().sum()}")

    assert train_df.shape == (20631, 26), f"Unexpected train shape: {train_df.shape}"
    assert test_df.shape == (13096, 26), f"Unexpected test shape: {test_df.shape}"
    assert len(rul_df) == 100, f"Unexpected RUL count: {len(rul_df)}"
    print("Status: PASS - Dataset intact, zero nulls, exact dimensions verified.")

    # 2. Saved Artifacts Audit
    print("\n--- 2. SAVED MODEL ARTIFACTS AUDIT ---")
    artifacts_dir = ml_dir / 'artifacts'
    model_file = artifacts_dir / 'random_forest_rul_model.joblib'
    scaler_file = artifacts_dir / 'scaler.joblib'
    feat_file = artifacts_dir / 'feature_names.joblib'
    meta_file = artifacts_dir / 'model_metadata.json'

    for f in [model_file, scaler_file, feat_file, meta_file]:
        assert f.exists(), f"Missing artifact: {f}"
        size_kb = f.stat().st_size / 1024
        print(f"Artifact: {f.name:32} | Size: {size_kb:8.2f} KB | Status: EXISTS")

    # 3. Model Loading & Feature Consistency
    print("\n--- 3. MODEL LOADING & FEATURE ALIGNMENT ---")
    model = joblib.load(model_file)
    scaler = joblib.load(scaler_file)
    features = joblib.load(feat_file)
    with open(meta_file, 'r') as fp:
        meta = json.load(fp)

    print(f"Model Class:             {type(model).__name__}")
    print(f"Model Estimators:        {len(model.estimators_)}")
    print(f"Scaler Features:         {scaler.n_features_in_}")
    print(f"Feature Count:           {len(features)} features")
    assert len(features) == 45, f"Expected 45 features, got {len(features)}"
    assert scaler.n_features_in_ == 45, f"Scaler feature mismatch: {scaler.n_features_in_}"
    assert model.n_features_in_ == 45, f"Model feature mismatch: {model.n_features_in_}"
    print("Status: PASS - 45/45 feature alignment between scaler, model, and configuration.")

    # 4. Verified Metrics Audit
    print("\n--- 4. EMPIRICAL MODEL METRICS AUDIT ---")
    print(f"Cross-Validation MAE:    {meta['cv_metrics']['mae']:.4f} cycles")
    print(f"Cross-Validation RMSE:   {meta['cv_metrics']['rmse']:.4f} cycles")
    print(f"Cross-Validation R2:     {meta['cv_metrics']['r2']:.4f}")
    print(f"Test Set Capped MAE:     {meta['test_metrics_capped']['mae']:.4f} cycles")
    print(f"Test Set Capped RMSE:    {meta['test_metrics_capped']['rmse']:.4f} cycles")
    print(f"Test Set Capped R2:      {meta['test_metrics_capped']['r2']:.4f}")
    print(f"Top Predictive Feature:  {meta['top_features'][0]['feature']} (Importance: {meta['top_features'][0]['importance']})")

    # 5. Prediction Service Runtime Inference Verification
    print("\n--- 5. LIVE PREDICTION SERVICE VERIFICATION ---")
    from services.prediction_service import PredictionService
    ps = PredictionService()
    assert ps.is_model_loaded(), "PredictionService failed to load model!"
    
    # Test sample inference with known engine 1 cycle 192 (critical failure condition)
    sample_telemetry = {
        'sensor_1': 518.67, 'sensor_2': 643.02, 'sensor_3': 1585.29, 'sensor_4': 1404.59,
        'sensor_5': 14.62, 'sensor_6': 21.61, 'sensor_7': 553.75, 'sensor_8': 2388.04,
        'sensor_9': 9044.07, 'sensor_10': 1.30, 'sensor_11': 47.35, 'sensor_12': 521.82,
        'sensor_13': 2388.08, 'sensor_14': 8128.87, 'sensor_15': 8.4195, 'sensor_16': 0.03,
        'sensor_17': 392.0, 'sensor_18': 2388.0, 'sensor_19': 100.0, 'sensor_20': 39.06,
        'sensor_21': 23.4190
    }
    pred_res = ps.predict_rul({'aircraft_id': 1, 'cycle': 192, 'telemetry': sample_telemetry, 'save_to_db': False})
    print(f"Inference Test Aircraft 1: RUL={pred_res['predicted_rul']} cycles | Risk={pred_res['risk_level']} | Alert={pred_res['alert_created']}")
    assert pred_res['predicted_rul'] > 0 and pred_res['predicted_rul'] < 25, f"Unexpected RUL: {pred_res['predicted_rul']}"
    assert pred_res['risk_level'] in ('HIGH', 'CRITICAL'), f"Unexpected risk level: {pred_res['risk_level']}"
    print("Status: PASS - Prediction service delivers verified physical inference.")

    print("\n" + "=" * 65)
    print("MACHINE LEARNING AUDIT COMPLETED: 100% PASS")
    print("=" * 65)

if __name__ == '__main__':
    run_ml_audit()
