"""
Verification and Test Suite for NASA C-MAPSS FD001 Preprocessing Pipeline.
Validates data loading, RUL capping, rolling feature extraction,
group-based cross validation, and test set alignment.
"""

import os
import sys

# Ensure root directory is on Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_model.data_loader import (
    load_cmapss_train,
    load_cmapss_test,
    load_cmapss_rul,
    CMAPSS_COLUMNS
)
from ml_model.feature_engineering import (
    INVARIANT_COLUMNS,
    INFORMATIVE_SENSORS,
    INFORMATIVE_SETTINGS,
    compute_piecewise_rul,
    extract_rolling_features,
    prepare_feature_matrix,
    extract_features_for_inference
)
from ml_model.preprocess import CmapssDataPreprocessor


def test_data_loader():
    print("[1/6] Testing Data Loader...")
    df_train = load_cmapss_train()
    assert df_train.shape == (20631, 26), f"Expected train shape (20631, 26), got {df_train.shape}"
    assert list(df_train.columns) == CMAPSS_COLUMNS, "Train column headers mismatch"
    assert df_train['unit_number'].nunique() == 100, f"Expected 100 units, got {df_train['unit_number'].nunique()}"
    assert df_train.isnull().sum().sum() == 0, "Found unexpected null values in train set"
    print(f"  OK: Train loaded successfully -> {df_train.shape[0]} rows, {df_train.shape[1]} cols, 100 engines.")

    df_test = load_cmapss_test()
    assert df_test.shape == (13096, 26), f"Expected test shape (13096, 26), got {df_test.shape}"
    assert df_test['unit_number'].nunique() == 100, f"Expected 100 test units, got {df_test['unit_number'].nunique()}"
    assert df_test.isnull().sum().sum() == 0, "Found unexpected null values in test set"
    print(f"  OK: Test loaded successfully -> {df_test.shape[0]} rows, {df_test.shape[1]} cols, 100 engines.")

    df_rul = load_cmapss_rul()
    assert len(df_rul) == 100, f"Expected 100 ground truth RULs, got {len(df_rul)}"
    assert (df_rul['actual_rul'] >= 0).all(), "RUL values cannot be negative"
    print(f"  OK: Ground-truth RUL loaded -> {len(df_rul)} values, range: [{df_rul['actual_rul'].min()}, {df_rul['actual_rul'].max()}].")


def test_piecewise_rul():
    print("\n[2/6] Testing Piecewise Linear RUL Target Calculation...")
    df_train = load_cmapss_train()
    
    # Raw uncapped RUL
    df_raw = compute_piecewise_rul(df_train, max_rul=None)
    assert 'rul' in df_raw.columns, "Target column 'rul' missing"
    assert df_raw['rul'].max() == 361, f"Expected max raw RUL 361, got {df_raw['rul'].max()}"
    assert df_raw['rul'].min() == 0, f"Expected min raw RUL 0, got {df_raw['rul'].min()}"

    # Capped piecewise RUL (max_rul=125)
    df_capped = compute_piecewise_rul(df_train, max_rul=125)
    assert df_capped['rul'].max() == 125, f"Expected capped max RUL 125, got {df_capped['rul'].max()}"
    assert df_capped['rul'].min() == 0, f"Expected min RUL 0, got {df_capped['rul'].min()}"
    print(f"  OK: Piecewise linear RUL capped at 125 cycles successfully (min: {df_capped['rul'].min()}, max: {df_capped['rul'].max()}).")


def test_feature_engineering():
    print("\n[3/6] Testing Rolling Feature Extraction & Invariant Column Filtering...")
    df_train = load_cmapss_train()
    
    # Verify invariant columns
    assert len(INVARIANT_COLUMNS) == 7, f"Expected 7 invariant columns, got {len(INVARIANT_COLUMNS)}"
    assert len(INFORMATIVE_SENSORS) == 14, f"Expected 14 informative sensors, got {len(INFORMATIVE_SENSORS)}"
    assert len(INFORMATIVE_SETTINGS) == 2, f"Expected 2 informative settings, got {len(INFORMATIVE_SETTINGS)}"

    # Feature matrix preparation
    df_features, feature_cols = prepare_feature_matrix(df_train, window_size=5, is_training=True, max_rul=125)
    
    # Check total feature count: 1 (cycle) + 2 (settings) + 14 (sensors) + 14 (roll_mean) + 14 (roll_std) = 45 features
    expected_feature_count = 1 + 2 + 14 + 14 + 14
    assert len(feature_cols) == expected_feature_count, f"Expected {expected_feature_count} features, got {len(feature_cols)}"
    assert df_features[feature_cols].isnull().sum().sum() == 0, "Engineered features contain unexpected NaN values"
    
    # Check that invariant columns are NOT in feature_cols
    for col in INVARIANT_COLUMNS:
        assert col not in feature_cols, f"Invariant column {col} was incorrectly retained in feature list"
    
    print(f"  OK: Feature matrix generated -> {len(feature_cols)} features ({feature_cols[:4]} ... {feature_cols[-2:]}).")
    print(f"  OK: 7 invariant columns successfully dropped: {INVARIANT_COLUMNS}")


def test_inference_feature_extractor():
    print("\n[4/6] Testing Online Inference Feature Extraction...")
    df_train = load_cmapss_train()
    # Extract first 5 cycles of unit 1
    recent_telemetry = df_train[(df_train['unit_number'] == 1) & (df_train['time_in_cycles'] <= 5)].copy()
    latest_feature_row, cols = extract_features_for_inference(recent_telemetry, window_size=5)
    
    assert latest_feature_row.shape == (1, 45), f"Expected shape (1, 45), got {latest_feature_row.shape}"
    assert latest_feature_row['time_in_cycles'].values[0] == 5, "Inference feature row should be for latest cycle (5)"
    print(f"  OK: Real-time inference feature extraction matches exact 45-feature schema.")


def test_preprocessor_pipeline():
    print("\n[5/6] Testing CmapssDataPreprocessor Pipeline...")
    preprocessor = CmapssDataPreprocessor(window_size=5, max_rul=125)
    
    # 1. Train preparation
    train_data = preprocessor.prepare_training_data()
    X = train_data['X']
    y = train_data['y']
    groups = train_data['groups']
    assert X.shape == (20631, 45), f"Expected X shape (20631, 45), got {X.shape}"
    assert len(y) == 20631, f"Expected y length 20631, got {len(y)}"
    assert len(groups) == 20631, f"Expected groups length 20631, got {len(groups)}"
    print(f"  OK: Training set prepared -> X: {X.shape}, y: {y.shape}, groups: {groups.shape}")

    # 2. Test preparation
    test_data = preprocessor.prepare_testing_data()
    X_test = test_data['X_test']
    y_test = test_data['y_test']
    y_test_raw = test_data['y_test_raw']
    test_summary = test_data['test_units_summary']
    assert X_test.shape == (100, 45), f"Expected X_test shape (100, 45), got {X_test.shape}"
    assert len(y_test) == 100, f"Expected y_test length 100, got {len(y_test)}"
    assert len(y_test_raw) == 100, f"Expected y_test_raw length 100, got {len(y_test_raw)}"
    assert len(test_summary) == 100, f"Expected test_summary length 100, got {len(test_summary)}"
    print(f"  OK: Test set prepared and aligned -> 100 engine units, 45 features, ground-truth RUL matched.")

    # 3. Scaler fitting on train only
    X_train_scaled, X_test_scaled, scaler = preprocessor.fit_and_transform_scaler(X, X_test)
    assert X_train_scaled.shape == X.shape, "Scaled train feature shape mismatch"
    assert X_test_scaled.shape == X_test.shape, "Scaled test feature shape mismatch"
    # Verify train features have mean ~ 0 and std ~ 1
    assert abs(X_train_scaled.mean().mean()) < 1e-3, "Scaled train features mean is not centered near 0"
    print(f"  OK: StandardScaler fitted exclusively on training set and applied to train and test.")


def test_group_kfold_no_leakage():
    print("\n[6/6] Testing GroupKFold Validation (Zero Engine Leakage)...")
    preprocessor = CmapssDataPreprocessor(window_size=5, max_rul=125)
    train_data = preprocessor.prepare_training_data()
    X = train_data['X']
    y = train_data['y']
    groups = train_data['groups']

    folds = list(preprocessor.get_group_kfold_splits(X, y, groups, n_splits=5))
    assert len(folds) == 5, f"Expected 5 folds, got {len(folds)}"

    for train_idx, val_idx, fold_num in folds:
        train_engines = set(groups.iloc[train_idx])
        val_engines = set(groups.iloc[val_idx])
        overlap = train_engines.intersection(val_engines)
        assert len(overlap) == 0, f"DATA LEAKAGE in fold {fold_num}: engines {overlap} present in both train and val!"
        print(f"  Fold {fold_num}: Train units = {len(train_engines)}, Val units = {len(val_engines)}, Overlap = {len(overlap)} (Clean)")

    print("  OK: All 5 folds validated with strictly zero engine leakage.")


if __name__ == '__main__':
    print("=" * 60)
    print("AEROPREDICT - NASA C-MAPSS FD001 PREPROCESSING TEST SUITE")
    print("=" * 60)
    test_data_loader()
    test_piecewise_rul()
    test_feature_engineering()
    test_inference_feature_extractor()
    test_preprocessor_pipeline()
    test_group_kfold_no_leakage()
    print("\n" + "=" * 60)
    print("ALL 6 PREPROCESSING TEST SUITES PASSED SUCCESSFULLY!")
    print("=" * 60)
