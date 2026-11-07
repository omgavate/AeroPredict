"""
Data Preprocessing and Pipeline Preparation Module for NASA C-MAPSS FD001.
Handles data loading, piecewise linear RUL target generation, causal rolling feature extraction,
GroupKFold partitioning by engine unit, and test set alignment with RUL_FD001.txt.
"""

import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold

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
    prepare_feature_matrix
)


class CmapssDataPreprocessor:
    """
    Comprehensive Preprocessor for the NASA C-MAPSS FD001 turbofan dataset.
    
    Attributes:
        window_size (int): Size of rolling backward window (default: 5 cycles).
        max_rul (int): Maximum threshold for piecewise linear RUL capping (default: 125 cycles).
        drop_invariant (bool): Whether to drop zero-variance columns (default: True).
        scaler (StandardScaler): Scaler fitted strictly on training data.
        feature_names (list): Final list of feature column names.
    """

    def __init__(self, window_size=5, max_rul=125, drop_invariant=True):
        self.window_size = window_size
        self.max_rul = max_rul
        self.drop_invariant = drop_invariant
        self.scaler = None
        self.feature_names = None

    def prepare_training_data(self, dataset_dir=None):
        """
        Loads and prepares the complete training dataset.
        
        Steps:
        1. Parse train_FD001.txt (20,631 rows, 100 engine units).
        2. Compute piecewise linear RUL: RUL = min(max_cycle - current_cycle, max_rul).
        3. Compute backward rolling mean and std over window_size for informative sensors.
        4. Exclude 7 invariant columns (setting_3, sensor_1, 5, 10, 16, 18, 19).
        5. Return X, y, groups, and feature names.
        
        Returns:
            dict: {
                'X': pd.DataFrame (20,631 rows x 45 features),
                'y': pd.Series (piecewise RUL),
                'groups': pd.Series (unit_number for group cross-validation),
                'feature_names': list[str],
                'df_full': pd.DataFrame (including identifiers and raw target)
            }
        """
        raw_train = load_cmapss_train(dataset_dir)
        df_full, feature_cols = prepare_feature_matrix(
            raw_train,
            window_size=self.window_size,
            is_training=True,
            max_rul=self.max_rul
        )

        self.feature_names = feature_cols
        X = df_full[feature_cols].copy()
        y = df_full['rul'].copy()
        groups = df_full['unit_number'].copy()

        return {
            'X': X,
            'y': y,
            'groups': groups,
            'feature_names': feature_cols,
            'df_full': df_full
        }

    def prepare_testing_data(self, dataset_dir=None):
        """
        Loads and prepares the NASA test dataset (test_FD001.txt) and aligns
        with ground-truth RUL (RUL_FD001.txt) at the last observed cycle of each engine.
        
        In C-MAPSS FD001, test engines are truncated prior to failure.
        The ground truth in RUL_FD001.txt provides the remaining cycles
        from the LAST recorded cycle for each of the 100 test units.
        
        Returns:
            dict: {
                'X_test': pd.DataFrame (100 rows x 45 features, last cycle per unit),
                'y_test': pd.Series (piecewise RUL capped at max_rul),
                'y_test_raw': pd.Series (raw uncapped actual RUL),
                'test_units_summary': pd.DataFrame (unit_number, max_observed_cycle, actual_rul, capped_rul),
                'df_test_full': pd.DataFrame (all 13,096 cycles with engineered features)
            }
        """
        raw_test = load_cmapss_test(dataset_dir)
        rul_df = load_cmapss_rul(dataset_dir)

        # Apply exact same feature engineering to test data
        df_test_full, _ = prepare_feature_matrix(
            raw_test,
            window_size=self.window_size,
            is_training=False
        )

        # Extract only the LAST observed cycle for each unit_number
        last_cycles_idx = df_test_full.groupby('unit_number')['time_in_cycles'].idxmax()
        df_last_cycles = df_test_full.loc[last_cycles_idx].copy().reset_index(drop=True)

        # Merge with ground truth RUL
        merged = pd.merge(df_last_cycles, rul_df, on='unit_number', how='inner')
        if len(merged) != len(rul_df):
            raise ValueError(f"Mismatch in test units: found {len(merged)}, expected {len(rul_df)}")

        # Features for evaluation
        X_test = merged[self.feature_names].copy()
        y_test_raw = merged['actual_rul'].copy()
        y_test_capped = y_test_raw.clip(upper=self.max_rul).copy()

        summary_df = pd.DataFrame({
            'unit_number': merged['unit_number'],
            'max_observed_cycle': merged['time_in_cycles'],
            'actual_rul': y_test_raw,
            'capped_rul': y_test_capped
        })

        return {
            'X_test': X_test,
            'y_test': y_test_capped,
            'y_test_raw': y_test_raw,
            'test_units_summary': summary_df,
            'df_test_full': df_test_full
        }

    def fit_and_transform_scaler(self, X_train, X_test=None):
        """
        Fits a StandardScaler on training features only (preventing test set leakage),
        and transforms training (and optionally test) features.
        
        Args:
            X_train (pd.DataFrame): Training features.
            X_test (pd.DataFrame, optional): Test features.
            
        Returns:
            tuple: (X_train_scaled, X_test_scaled, scaler)
        """
        self.scaler = StandardScaler()
        X_train_scaled = pd.DataFrame(
            self.scaler.fit_transform(X_train),
            columns=X_train.columns,
            index=X_train.index
        )

        X_test_scaled = None
        if X_test is not None:
            X_test_scaled = pd.DataFrame(
                self.scaler.transform(X_test),
                columns=X_test.columns,
                index=X_test.index
            )

        return X_train_scaled, X_test_scaled, self.scaler

    def get_group_kfold_splits(self, X, y, groups, n_splits=5):
        """
        Generates cross-validation fold splits using GroupKFold.
        Guarantees that engine units in the validation fold NEVER appear
        in the training fold, preventing optimistic leakage.
        
        Args:
            X (pd.DataFrame): Feature matrix.
            y (pd.Series): Target RUL.
            groups (pd.Series): Engine unit numbers.
            n_splits (int): Number of folds (default: 5).
            
        Yields:
            tuple: (train_indices, val_indices, fold_number)
        """
        gkf = GroupKFold(n_splits=n_splits)
        for fold_idx, (train_idx, val_idx) in enumerate(gkf.split(X, y, groups=groups), start=1):
            train_units = set(groups.iloc[train_idx])
            val_units = set(groups.iloc[val_idx])
            overlap = train_units.intersection(val_units)
            if overlap:
                raise RuntimeError(f"GroupKFold leakage detected in fold {fold_idx}: units {overlap} in both train and val!")
            yield train_idx, val_idx, fold_idx
