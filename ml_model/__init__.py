"""
AeroPredict Machine Learning Package.
Modules:
- data_loader: Space-delimited NASA C-MAPSS dataset parser.
- feature_engineering: Piecewise linear RUL and causal rolling feature extractor.
- preprocess: End-to-end dataset preprocessor with GroupKFold partitioning and test set alignment.
- train: Model training pipeline with GroupKFold CV and Joblib persistence.
- predict: Real-time inference engine and aviation health status mapper.
"""

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
from ml_model.predict import RulPredictor

__all__ = [
    'load_cmapss_train',
    'load_cmapss_test',
    'load_cmapss_rul',
    'CMAPSS_COLUMNS',
    'INVARIANT_COLUMNS',
    'INFORMATIVE_SENSORS',
    'INFORMATIVE_SETTINGS',
    'compute_piecewise_rul',
    'extract_rolling_features',
    'prepare_feature_matrix',
    'extract_features_for_inference',
    'CmapssDataPreprocessor',
    'RulPredictor'
]
