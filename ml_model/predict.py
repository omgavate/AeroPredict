"""
AeroPredict RUL Inference and Prediction Engine.
Provides consistent, production-ready inference from raw sensor telemetry
using the trained RandomForestRegressor and preprocessing pipeline.
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

from ml_model.feature_engineering import (
    INFORMATIVE_SENSORS,
    INFORMATIVE_SETTINGS,
    INVARIANT_COLUMNS,
    extract_features_for_inference,
    prepare_feature_matrix
)

ARTIFACTS_DIR = os.path.join(CURRENT_DIR, 'artifacts')


class RulPredictor:
    """
    RUL Prediction Service for real-time engine health monitoring.
    
    Guarantees:
    - Identical feature names and ordering as used during model training.
    - Automatic extraction of causal rolling features over recent operational cycles.
    - Categorization into aviation maintenance health stages.
    """

    def __init__(self, artifacts_dir=None):
        self.artifacts_dir = artifacts_dir or ARTIFACTS_DIR
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.config = None
        self._load_artifacts()

    def _load_artifacts(self):
        """Loads persisted model, scaler, and feature definitions."""
        model_path = os.path.join(self.artifacts_dir, 'random_forest_rul_model.joblib')
        scaler_path = os.path.join(self.artifacts_dir, 'scaler.joblib')
        features_path = os.path.join(self.artifacts_dir, 'feature_names.joblib')
        config_path = os.path.join(self.artifacts_dir, 'model_config.joblib')

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Trained model not found at: {model_path}. Please run train.py first.")

        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path) if os.path.exists(scaler_path) else None
        self.feature_names = joblib.load(features_path)
        self.config = joblib.load(config_path) if os.path.exists(config_path) else {}

    def get_health_status(self, rul_cycles):
        """
        Maps Remaining Useful Life (RUL) to aviation maintenance severity tiers.
        
        Thresholds:
            RUL > 75: Normal (Healthy operational condition)
            25 < RUL <= 75: Caution (Scheduled maintenance inspection advised)
            RUL <= 25: Warning (Immediate maintenance action required)
        """
        rul = max(0.0, float(rul_cycles))
        if rul > 75.0:
            status = 'Normal'
            risk_level = 'Low'
            color = '#10B981' # Emerald Green
            action = 'Routine monitoring. Engine operating within healthy parameters.'
        elif rul > 25.0:
            status = 'Caution'
            risk_level = 'Medium'
            color = '#F59E0B' # Amber
            action = 'Schedule maintenance inspection within next 20 flight cycles.'
        else:
            status = 'Warning'
            risk_level = 'High'
            color = '#EF4444' # Coral Red
            action = 'CRITICAL: Ground aircraft for immediate engine overhaul or turbine inspection.'

        # Degradation score (0% = brand new, 100% = imminent failure)
        max_benchmark = self.config.get('preprocessing_params', {}).get('max_rul', 125)
        degradation_pct = min(100.0, max(0.0, round((1.0 - (rul / max_benchmark)) * 100.0, 1)))

        return {
            'predicted_rul': round(rul, 1),
            'status': status,
            'risk_level': risk_level,
            'color': color,
            'action_recommendation': action,
            'degradation_percentage': degradation_pct
        }

    def predict_features(self, feature_df):
        """
        Direct inference on a pre-engineered feature DataFrame.
        Enforces identical feature column ordering.
        """
        missing_cols = set(self.feature_names) - set(feature_df.columns)
        if missing_cols:
            raise ValueError(f"Feature matrix missing required features: {missing_cols}")

        X = feature_df[self.feature_names]
        preds = self.model.predict(X)
        return np.maximum(0.0, preds)

    def predict_from_telemetry(self, recent_telemetry_df, window_size=5):
        """
        Real-time inference given recent raw cycle observations of an engine.
        
        Args:
            recent_telemetry_df (pd.DataFrame): DataFrame containing at least 1 and
                up to window_size consecutive cycle readings for an engine unit.
            window_size (int): Rolling window size (default: 5 cycles).
            
        Returns:
            dict: Comprehensive prediction output with RUL, health status, and metadata.
        """
        if recent_telemetry_df.empty:
            raise ValueError("Telemetry DataFrame cannot be empty.")

        latest_feature_row, cols = extract_features_for_inference(recent_telemetry_df, window_size=window_size)
        preds = self.predict_features(latest_feature_row)
        predicted_rul = float(preds[0])

        health_info = self.get_health_status(predicted_rul)
        latest_cycle = int(recent_telemetry_df['time_in_cycles'].iloc[-1])
        unit_id = int(recent_telemetry_df['unit_number'].iloc[-1])

        return {
            'unit_number': unit_id,
            'current_cycle': latest_cycle,
            **health_info,
            'model_info': {
                'model_type': self.config.get('model_type', 'RandomForestRegressor'),
                'features_used': len(self.feature_names)
            }
        }

    def predict_trajectory(self, full_engine_df, window_size=5):
        """
        Computes the complete degradation trajectory over all recorded cycles
        for a single engine unit (ideal for frontend Recharts plotting).
        
        Returns:
            list[dict]: Array of {'cycle': int, 'predicted_rul': float, 'status': str}
        """
        df_features, feature_cols = prepare_feature_matrix(
            full_engine_df,
            window_size=window_size,
            is_training=False
        )

        preds = self.predict_features(df_features[self.feature_names])
        trajectory = []
        for idx, (_, row) in enumerate(full_engine_df.iterrows()):
            cycle = int(row['time_in_cycles'])
            pred_rul = float(preds[idx])
            h = self.get_health_status(pred_rul)
            trajectory.append({
                'cycle': cycle,
                'predicted_rul': round(pred_rul, 1),
                'status': h['status'],
                'risk_level': h['risk_level']
            })

        return trajectory
