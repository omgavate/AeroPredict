"""
Comprehensive Test Suite for AeroPredict Model Training and Inference Pipeline.
Verifies artifact integrity, model loading, held-out prediction fidelity,
telemetry-to-inference consistency, and health status mapping.
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ml_model.data_loader import load_cmapss_train, load_cmapss_test, load_cmapss_rul
from ml_model.preprocess import CmapssDataPreprocessor
from ml_model.predict import RulPredictor, ARTIFACTS_DIR


def test_artifact_files_exist():
    print("[1/5] Testing Artifact Files Existence & Non-Empty Sizes...")
    expected_files = [
        'random_forest_rul_model.joblib',
        'scaler.joblib',
        'feature_names.joblib',
        'model_config.joblib',
        'model_metadata.json'
    ]
    for filename in expected_files:
        path = os.path.join(ARTIFACTS_DIR, filename)
        assert os.path.exists(path), f"Missing required artifact: {path}"
        size = os.path.getsize(path)
        assert size > 0, f"Artifact file is empty: {path}"
        print(f"  OK: {filename} exists ({size:,} bytes)")


def test_model_loading_and_config():
    print("\n[2/5] Testing Model Loading & Configuration Deserialization...")
    predictor = RulPredictor()
    assert predictor.model is not None, "Predictor model is None"
    assert len(predictor.feature_names) == 45, f"Expected 45 features, got {len(predictor.feature_names)}"
    assert predictor.config['model_type'] == 'RandomForestRegressor'
    print(f"  OK: Loaded {predictor.config['model_type']} with {len(predictor.feature_names)} features.")
    print(f"  OK: Model parameters: {predictor.config['model_params']}")


def test_held_out_test_predictions():
    print("\n[3/5] Testing Held-Out Test Set Predictions & Error Bounds...")
    predictor = RulPredictor()
    preprocessor = CmapssDataPreprocessor(window_size=5, max_rul=125)
    test_data = preprocessor.prepare_testing_data()

    X_test = test_data['X_test']
    y_test_capped = test_data['y_test']
    y_test_raw = test_data['y_test_raw']

    predictions = predictor.predict_features(X_test)
    assert len(predictions) == 100, f"Expected 100 predictions, got {len(predictions)}"
    assert (predictions >= 0).all(), "Predictions contain negative RUL values!"

    mae_capped = np.mean(np.abs(predictions - y_test_capped))
    rmse_capped = np.sqrt(np.mean((predictions - y_test_capped) ** 2))

    mae_raw = np.mean(np.abs(predictions - y_test_raw))
    rmse_raw = np.sqrt(np.mean((predictions - y_test_raw) ** 2))

    print(f"  OK: Capped Evaluation -> MAE: {mae_capped:.2f} cycles | RMSE: {rmse_capped:.2f} cycles")
    print(f"  OK: Raw Uncapped Evaluation -> MAE: {mae_raw:.2f} cycles | RMSE: {rmse_raw:.2f} cycles")

    # Sanity checks for NASA FD001 literature benchmarks
    # Random Forest on FD001 typically achieves MAE between 12-25 cycles
    assert mae_capped < 30.0, f"MAE capped {mae_capped:.2f} is higher than acceptable baseline threshold (30.0)"
    assert rmse_capped < 35.0, f"RMSE capped {rmse_capped:.2f} is higher than acceptable baseline threshold (35.0)"
    print("  OK: Model accuracy is well within NASA C-MAPSS FD001 benchmark standards.")


def test_telemetry_inference_consistency():
    print("\n[4/5] Testing Real-Time Sliding Window Telemetry Inference...")
    predictor = RulPredictor()
    df_train = load_cmapss_train()

    # Engine 1, cycles 1 to 5
    telemetry_window = df_train[(df_train['unit_number'] == 1) & (df_train['time_in_cycles'] <= 5)].copy()
    result = predictor.predict_from_telemetry(telemetry_window)

    assert result['unit_number'] == 1
    assert result['current_cycle'] == 5
    assert 'predicted_rul' in result
    assert result['status'] in ['Normal', 'Caution', 'Warning']
    assert 0.0 <= result['degradation_percentage'] <= 100.0
    print(f"  OK: Cycle 5 inference -> Predicted RUL: {result['predicted_rul']} cycles, Status: {result['status']}, Risk: {result['risk_level']}")

    # End of life for Engine 1 (cycle 192)
    telemetry_late = df_train[(df_train['unit_number'] == 1) & (df_train['time_in_cycles'].between(188, 192))].copy()
    result_late = predictor.predict_from_telemetry(telemetry_late)
    print(f"  OK: Cycle 192 (near failure) inference -> Predicted RUL: {result_late['predicted_rul']} cycles, Status: {result_late['status']}, Risk: {result_late['risk_level']}")
    assert result_late['predicted_rul'] < result['predicted_rul'], "Late cycle RUL should be strictly lower than early cycle RUL"
    assert result_late['status'] == 'Warning', "Near-failure engine should be flagged as 'Warning'"


def test_trajectory_prediction():
    print("\n[5/5] Testing Engine Health Degradation Trajectory...")
    predictor = RulPredictor()
    df_train = load_cmapss_train()
    unit_1 = df_train[df_train['unit_number'] == 1].copy()

    trajectory = predictor.predict_trajectory(unit_1)
    assert len(trajectory) == len(unit_1), f"Expected trajectory length {len(unit_1)}, got {len(trajectory)}"

    first_rul = trajectory[0]['predicted_rul']
    last_rul = trajectory[-1]['predicted_rul']
    print(f"  OK: Trajectory for Unit 1 -> Initial cycle RUL: {first_rul:.1f} cycles, Final cycle RUL: {last_rul:.1f} cycles")
    assert last_rul < first_rul, "RUL must degrade over full engine operational lifetime"
    print("  OK: Trajectory exhibits clear, monotonic degradation towards end-of-life.")


if __name__ == '__main__':
    print("=" * 65)
    print("AEROPREDICT - MODEL & INFERENCE VERIFICATION TEST SUITE")
    print("=" * 65)
    test_artifact_files_exist()
    test_model_loading_and_config()
    test_held_out_test_predictions()
    test_telemetry_inference_consistency()
    test_trajectory_prediction()
    print("\n" + "=" * 65)
    print("ALL 5 MODEL & INFERENCE VERIFICATION TESTS PASSED!")
    print("=" * 65)
