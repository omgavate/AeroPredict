"""
AeroPredict RUL Model Training and Evaluation Pipeline.
Trains a RandomForestRegressor on NASA C-MAPSS FD001 dataset using
engine-ID-based GroupKFold validation, evaluates on held-out test engines,
and persists artifacts with Joblib.
"""

import os
import sys
import json
import time
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Ensure root directory is on Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ml_model.preprocess import CmapssDataPreprocessor

# Artifacts destination directory
ARTIFACTS_DIR = os.path.join(CURRENT_DIR, 'artifacts')
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

# Baseline Configurable Hyperparameters for Random Forest
MODEL_CONFIG = {
    'n_estimators': 100,
    'max_depth': 18,
    'min_samples_split': 5,
    'min_samples_leaf': 2,
    'max_features': 0.7,
    'random_state': 42,
    'n_jobs': -1
}

PREPROCESSING_CONFIG = {
    'window_size': 5,
    'max_rul': 125,
    'drop_invariant': True
}


def compute_nasa_score(y_true, y_pred):
    """
    Computes the standard NASA C-MAPSS asymmetric degradation score:
    Late predictions (predicting higher RUL than actual) are penalized more heavily:
        d = y_pred - y_true
        s = exp(-d/13) - 1 for d < 0 (early prediction)
        s = exp(d/10) - 1 for d >= 0 (late prediction / safety critical)
    """
    d = np.array(y_pred) - np.array(y_true)
    score = 0.0
    for diff in d:
        if diff < 0:
            score += np.exp(-diff / 13.0) - 1.0
        else:
            score += np.exp(diff / 10.0) - 1.0
    return float(score)


def evaluate_predictions(y_true, y_pred, label=""):
    """
    Computes MAE, RMSE, R2, and NASA Score for regression predictions.
    """
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_true, y_pred)
    nasa_score = compute_nasa_score(y_true, y_pred)

    metrics = {
        'mae': round(float(mae), 4),
        'rmse': round(float(rmse), 4),
        'r2': round(float(r2), 4),
        'nasa_score': round(float(nasa_score), 2)
    }

    if label:
        print(f"  [{label}] MAE: {metrics['mae']} cycles | RMSE: {metrics['rmse']} cycles | R²: {metrics['r2']} | NASA Score: {metrics['nasa_score']}")

    return metrics


def train_and_evaluate():
    """
    Orchestrates the complete Phase 6 training and evaluation pipeline:
    1. Preprocesses train and test datasets.
    2. Performs 5-fold GroupKFold cross-validation on train units (zero engine leakage).
    3. Trains final RandomForestRegressor model on full training set.
    4. Evaluates on held-out test units (100 engines at final observed cycle).
    5. Persists model artifacts using Joblib and JSON.
    """
    print("=" * 70)
    print("AEROPREDICT - NASA C-MAPSS FD001 MODEL TRAINING PIPELINE")
    print("=" * 70)
    start_time = time.time()

    # Step 1: Preprocessing
    print("\n[Step 1/5] Ingesting & Preprocessing Dataset...")
    preprocessor = CmapssDataPreprocessor(
        window_size=PREPROCESSING_CONFIG['window_size'],
        max_rul=PREPROCESSING_CONFIG['max_rul'],
        drop_invariant=PREPROCESSING_CONFIG['drop_invariant']
    )

    train_data = preprocessor.prepare_training_data()
    X_train = train_data['X']
    y_train = train_data['y']
    groups = train_data['groups']
    feature_names = train_data['feature_names']
    print(f"  Training Features shape: {X_train.shape} (20,631 records across 100 engines)")
    print(f"  Target piecewise RUL range: [{y_train.min()}, {y_train.max()}] cycles")
    print(f"  Engineered feature count: {len(feature_names)} features")

    test_data = preprocessor.prepare_testing_data()
    X_test = test_data['X_test']
    y_test_capped = test_data['y_test']
    y_test_raw = test_data['y_test_raw']
    print(f"  Test evaluation set shape: {X_test.shape} (100 test engines at final cycle)")
    print(f"  Test ground-truth RUL range: [{y_test_raw.min()}, {y_test_raw.max()}] cycles (mean: {y_test_raw.mean():.2f})")

    # Step 2: Fit Scaler
    print("\n[Step 2/5] Fitting Feature Scaler (Fitted strictly on train set)...")
    X_train_scaled, X_test_scaled, scaler = preprocessor.fit_and_transform_scaler(X_train, X_test)
    print("  StandardScaler fitted successfully.")

    # Step 3: Engine-ID Group Cross-Validation
    print(f"\n[Step 3/5] Performing 5-Fold GroupKFold Cross-Validation by Engine Unit...")
    fold_metrics = []
    oof_predictions = np.zeros(len(y_train))

    for train_idx, val_idx, fold_num in preprocessor.get_group_kfold_splits(X_train, y_train, groups, n_splits=5):
        X_tr, y_tr = X_train.iloc[train_idx], y_train.iloc[train_idx]
        X_vl, y_vl = X_train.iloc[val_idx], y_train.iloc[val_idx]

        fold_model = RandomForestRegressor(**MODEL_CONFIG)
        fold_model.fit(X_tr, y_tr)
        val_pred = fold_model.predict(X_vl)
        oof_predictions[val_idx] = val_pred

        m = evaluate_predictions(y_vl, val_pred, label=f"Fold {fold_num}")
        fold_metrics.append(m)

    # Compute overall Out-Of-Fold CV metrics
    cv_overall = evaluate_predictions(y_train, oof_predictions, label="Overall OOF Cross-Validation")
    mean_cv_mae = np.mean([m['mae'] for m in fold_metrics])
    mean_cv_rmse = np.mean([m['rmse'] for m in fold_metrics])
    print(f"  Average CV MAE: {mean_cv_mae:.2f} cycles | Average CV RMSE: {mean_cv_rmse:.2f} cycles")

    # Step 4: Full Model Training
    print("\n[Step 4/5] Training Final Production Model on Full Training Fleet...")
    t_train_start = time.time()
    final_model = RandomForestRegressor(**MODEL_CONFIG)
    final_model.fit(X_train, y_train)
    t_train_elapsed = time.time() - t_train_start
    print(f"  Model trained in {t_train_elapsed:.2f} seconds.")

    # Training set fit metrics
    train_pred = final_model.predict(X_train)
    train_metrics = evaluate_predictions(y_train, train_pred, label="Full Training Set Fit")

    # Final Test Set Evaluation
    print("\n[Step 5/5] Evaluating on Held-Out NASA Test Fleet (100 Test Engines)...")
    test_pred = final_model.predict(X_test)

    # Evaluation against capped benchmark RUL
    test_metrics_capped = evaluate_predictions(y_test_capped, test_pred, label="Test Set (Capped RUL <= 125)")
    # Evaluation against raw uncapped ground-truth RUL
    test_metrics_raw = evaluate_predictions(y_test_raw, test_pred, label="Test Set (Raw Uncapped RUL)")

    # Feature Importance Top 10
    importances = final_model.feature_importances_
    sorted_idx = np.argsort(importances)[::-1]
    top_features = []
    print("\n  Top 10 Most Predictive Degradation Features:")
    for rank, idx in enumerate(sorted_idx[:10], start=1):
        feat = feature_names[idx]
        imp = float(importances[idx])
        top_features.append({'rank': rank, 'feature': feat, 'importance': round(imp, 4)})
        print(f"    {rank:2d}. {feat:<28} (importance: {imp:.4f})")

    # Step 6: Artifact Persistence
    print("\n[Artifact Persistence] Saving Model, Scaler, and Configuration...")
    model_path = os.path.join(ARTIFACTS_DIR, 'random_forest_rul_model.joblib')
    scaler_path = os.path.join(ARTIFACTS_DIR, 'scaler.joblib')
    features_path = os.path.join(ARTIFACTS_DIR, 'feature_names.joblib')
    config_path = os.path.join(ARTIFACTS_DIR, 'model_config.joblib')
    metadata_json_path = os.path.join(ARTIFACTS_DIR, 'model_metadata.json')

    joblib.dump(final_model, model_path, compress=3)
    joblib.dump(scaler, scaler_path)
    joblib.dump(feature_names, features_path)

    full_config = {
        'model_type': 'RandomForestRegressor',
        'model_params': MODEL_CONFIG,
        'preprocessing_params': PREPROCESSING_CONFIG,
        'feature_count': len(feature_names),
        'feature_names': feature_names,
        'training_summary': {
            'train_samples': len(X_train),
            'train_units': 100,
            'test_samples': len(X_test),
            'test_units': 100,
            'training_time_sec': round(t_train_elapsed, 2)
        },
        'cv_metrics': cv_overall,
        'fold_metrics': fold_metrics,
        'test_metrics_capped': test_metrics_capped,
        'test_metrics_raw': test_metrics_raw,
        'top_features': top_features,
        'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    joblib.dump(full_config, config_path)

    # Save human-readable JSON
    with open(metadata_json_path, 'w') as f:
        json.dump(full_config, f, indent=2)

    total_time = time.time() - start_time
    print(f"\n  Saved artifacts:")
    print(f"    - {model_path} ({os.path.getsize(model_path) / 1024 / 1024:.2f} MB)")
    print(f"    - {scaler_path} ({os.path.getsize(scaler_path) / 1024:.2f} KB)")
    print(f"    - {features_path} ({os.path.getsize(features_path) / 1024:.2f} KB)")
    print(f"    - {config_path} ({os.path.getsize(config_path) / 1024:.2f} KB)")
    print(f"    - {metadata_json_path}")

    print("\n" + "=" * 70)
    print(f"MODEL TRAINING & EVALUATION COMPLETED IN {total_time:.2f} SECONDS")
    print("=" * 70)

    return full_config


if __name__ == '__main__':
    train_and_evaluate()
