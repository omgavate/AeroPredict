"""
Feature Engineering Module for NASA C-MAPSS FD001 Turbofan Engine Degradation.
Extracts degradation trends, rolling window statistics, and piecewise RUL targets
without future cycle leakage.
"""

import pandas as pd
import numpy as np

# Invariant (zero-variance) columns in C-MAPSS FD001 dataset
INVARIANT_COLUMNS = [
    'setting_3',
    'sensor_1',
    'sensor_5',
    'sensor_10',
    'sensor_16',
    'sensor_18',
    'sensor_19'
]

# Informative sensors with active operational degradation variance
INFORMATIVE_SENSORS = [
    'sensor_2',
    'sensor_3',
    'sensor_4',
    'sensor_7',
    'sensor_8',
    'sensor_9',
    'sensor_11',
    'sensor_12',
    'sensor_13',
    'sensor_14',
    'sensor_15',
    'sensor_17',
    'sensor_20',
    'sensor_21'
]

# Informative operational settings
INFORMATIVE_SETTINGS = [
    'setting_1',
    'setting_2'
]


def compute_piecewise_rul(df, max_rul=125, target_col='rul'):
    """
    Computes Remaining Useful Life (RUL) with piecewise linear capping.
    In early engine life, degradation is undetectable so RUL is capped
    at max_rul (standard C-MAPSS benchmark = 125 cycles).
    
    Formula:
        Raw RUL = max_cycle_of_unit - current_cycle
        Piecewise RUL = min(Raw RUL, max_rul)
        
    Args:
        df (pd.DataFrame): DataFrame containing 'unit_number' and 'time_in_cycles'.
        max_rul (int or None): Maximum RUL threshold. If None, raw linear RUL is used.
        target_col (str): Column name for the calculated RUL.
        
    Returns:
        pd.DataFrame: Copy of df with target_col appended.
    """
    df_out = df.copy()
    if 'unit_number' not in df_out.columns or 'time_in_cycles' not in df_out.columns:
        raise ValueError("DataFrame must contain 'unit_number' and 'time_in_cycles' columns.")

    # Max cycle per engine unit
    max_cycles = df_out.groupby('unit_number')['time_in_cycles'].transform('max')
    raw_rul = max_cycles - df_out['time_in_cycles']

    if max_rul is not None and max_rul > 0:
        df_out[target_col] = raw_rul.clip(upper=max_rul)
    else:
        df_out[target_col] = raw_rul

    return df_out


def extract_rolling_features(df, window_size=5, sensors=None):
    """
    Extracts causal backward rolling statistics (mean and std) per engine unit.
    Uses min_periods=1 so that earlier cycles (cycles 1..window_size-1) have valid
    backward statistics without dropping rows or leaking future cycles.
    
    Args:
        df (pd.DataFrame): DataFrame containing 'unit_number' and sensor columns.
        window_size (int): Number of historical cycles in the rolling window (default 5).
        sensors (list): List of sensor column names to compute rolling stats for.
        
    Returns:
        pd.DataFrame: New DataFrame containing the engineered rolling columns.
    """
    if sensors is None:
        sensors = INFORMATIVE_SENSORS

    rolling_dfs = []
    # Group by unit_number to ensure rolling window NEVER crosses engine boundaries
    grouped = df.groupby('unit_number')[sensors]

    # Backward rolling mean (min_periods=1 ensures no NaNs even at cycle 1)
    roll_mean = grouped.rolling(window=window_size, min_periods=1).mean().reset_index(level=0, drop=True)
    roll_mean.columns = [f'{col}_roll_mean' for col in sensors]
    rolling_dfs.append(roll_mean)

    # Backward rolling standard deviation
    roll_std = grouped.rolling(window=window_size, min_periods=1).std().reset_index(level=0, drop=True)
    roll_std.columns = [f'{col}_roll_std' for col in sensors]
    # At cycle 1, sample size is 1 so std is NaN; fill with 0.0
    roll_std = roll_std.fillna(0.0)
    rolling_dfs.append(roll_std)

    return pd.concat(rolling_dfs, axis=1)


def prepare_feature_matrix(df, window_size=5, is_training=True, max_rul=125):
    """
    Constructs the complete feature matrix for training or evaluation.
    
    Features included:
    1. Operating cycle ('time_in_cycles')
    2. Informative settings ('setting_1', 'setting_2')
    3. Informative sensors (14 active sensors)
    4. Rolling mean over window_size for informative sensors (14 features)
    5. Rolling std over window_size for informative sensors (14 features)
    
    Total engineered features: 1 + 2 + 14 + 14 + 14 = 45 features.
    
    Args:
        df (pd.DataFrame): Raw C-MAPSS DataFrame.
        window_size (int): Size of rolling window.
        is_training (bool): If True, compute piecewise RUL target.
        max_rul (int): Threshold for piecewise RUL capping.
        
    Returns:
        tuple: (df_features, feature_columns)
            df_features (pd.DataFrame): Transformed DataFrame with all features (and target if is_training).
            feature_columns (list): Names of feature columns used for model input.
    """
    df_work = df.copy()

    # Compute target if training
    if is_training:
        df_work = compute_piecewise_rul(df_work, max_rul=max_rul, target_col='rul')

    # Rolling window features
    df_rolling = extract_rolling_features(df_work, window_size=window_size, sensors=INFORMATIVE_SENSORS)

    # Base feature columns
    base_features = ['time_in_cycles'] + INFORMATIVE_SETTINGS + INFORMATIVE_SENSORS
    rolling_features = list(df_rolling.columns)

    feature_columns = base_features + rolling_features

    # Combine
    df_combined = pd.concat([df_work[['unit_number', 'time_in_cycles'] + ([ 'rul'] if is_training else [])],
                             df_work[INFORMATIVE_SETTINGS + INFORMATIVE_SENSORS],
                             df_rolling], axis=1)

    return df_combined, feature_columns


def extract_features_for_inference(recent_telemetry_df, window_size=5):
    """
    Extracts features for online/real-time inference from a sliding window
    of recent engine cycles.
    
    Args:
        recent_telemetry_df (pd.DataFrame): DataFrame with at least 1 and up to
            window_size recent cycles for a single engine unit, sorted by time_in_cycles.
        window_size (int): Rolling window size.
        
    Returns:
        tuple: (latest_feature_vector_df, feature_columns)
            Single-row DataFrame corresponding to the latest cycle with exact feature column alignment.
    """
    df_combined, feature_cols = prepare_feature_matrix(
        recent_telemetry_df,
        window_size=window_size,
        is_training=False
    )
    # Return the latest cycle record
    latest_row = df_combined.iloc[[-1]][feature_cols]
    return latest_row, feature_cols
