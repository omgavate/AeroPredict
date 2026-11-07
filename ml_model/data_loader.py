"""
NASA C-MAPSS FD001 Data Loader Module.
Loads raw space-delimited text files for training, testing, and ground-truth RUL.
"""

import os
import pandas as pd

# Standard column names for NASA C-MAPSS Turbofan Engine Degradation Simulation
IDENTIFIER_COLUMNS = ['unit_number', 'time_in_cycles']

SETTING_COLUMNS = ['setting_1', 'setting_2', 'setting_3']

SENSOR_COLUMNS = [f'sensor_{i}' for i in range(1, 22)]

CMAPSS_COLUMNS = IDENTIFIER_COLUMNS + SETTING_COLUMNS + SENSOR_COLUMNS


def get_default_dataset_dir():
    """
    Resolves the absolute path to the dataset directory.
    Default: <project_root>/dataset
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, 'dataset')


def load_cmapss_train(dataset_dir=None):
    """
    Loads train_FD001.txt into a Pandas DataFrame.
    
    Returns:
        pd.DataFrame: 20,631 rows x 26 columns with proper column names and types.
    """
    if dataset_dir is None:
        dataset_dir = get_default_dataset_dir()
    filepath = os.path.join(dataset_dir, 'train_FD001.txt')
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Training dataset file not found: {filepath}")

    df = pd.read_csv(filepath, sep=r'\s+', header=None, names=CMAPSS_COLUMNS)
    df['unit_number'] = df['unit_number'].astype(int)
    df['time_in_cycles'] = df['time_in_cycles'].astype(int)
    return df


def load_cmapss_test(dataset_dir=None):
    """
    Loads test_FD001.txt into a Pandas DataFrame.
    
    Returns:
        pd.DataFrame: 13,096 rows x 26 columns with proper column names and types.
    """
    if dataset_dir is None:
        dataset_dir = get_default_dataset_dir()
    filepath = os.path.join(dataset_dir, 'test_FD001.txt')
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Test dataset file not found: {filepath}")

    df = pd.read_csv(filepath, sep=r'\s+', header=None, names=CMAPSS_COLUMNS)
    df['unit_number'] = df['unit_number'].astype(int)
    df['time_in_cycles'] = df['time_in_cycles'].astype(int)
    return df


def load_cmapss_rul(dataset_dir=None):
    """
    Loads RUL_FD001.txt containing ground-truth RUL for the 100 test engine units
    at their last observed cycle.
    
    Returns:
        pd.DataFrame: 100 rows with columns ['unit_number', 'actual_rul'].
    """
    if dataset_dir is None:
        dataset_dir = get_default_dataset_dir()
    filepath = os.path.join(dataset_dir, 'RUL_FD001.txt')
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"RUL ground-truth file not found: {filepath}")

    rul_series = pd.read_csv(filepath, sep=r'\s+', header=None, names=['actual_rul'])
    df_rul = pd.DataFrame({
        'unit_number': range(1, len(rul_series) + 1),
        'actual_rul': rul_series['actual_rul'].astype(int)
    })
    return df_rul
