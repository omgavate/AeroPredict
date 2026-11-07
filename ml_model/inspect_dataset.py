"""
Dataset Inspection and Statistical Audit for NASA C-MAPSS FD001.
Audits row counts, engine units, cycle ranges, missing values, and sensor variance.
"""

import os
from collections import defaultdict

COLUMN_NAMES = [
    'unit_number', 'time_in_cycles', 'setting_1', 'setting_2', 'setting_3',
    'sensor_1', 'sensor_2', 'sensor_3', 'sensor_4', 'sensor_5',
    'sensor_6', 'sensor_7', 'sensor_8', 'sensor_9', 'sensor_10',
    'sensor_11', 'sensor_12', 'sensor_13', 'sensor_14', 'sensor_15',
    'sensor_16', 'sensor_17', 'sensor_18', 'sensor_19', 'sensor_20',
    'sensor_21'
]

DATASET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dataset')


def audit_file(filename, expected_cols=26):
    filepath = os.path.join(DATASET_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Missing required dataset file: {filepath}")

    size_bytes = os.path.getsize(filepath)
    with open(filepath, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    total_rows = len(lines)
    col_counts = set()
    units = set()
    cycles_by_unit = defaultdict(list)
    missing_count = 0

    # Accumulate values for variance analysis
    column_values = [[] for _ in range(expected_cols)]

    for line_idx, line in enumerate(lines):
        parts = line.split()
        col_counts.add(len(parts))
        if len(parts) != expected_cols:
            continue

        try:
            unit = int(parts[0])
            cycle = int(parts[1])
            units.add(unit)
            cycles_by_unit[unit].append(cycle)

            for col_idx in range(expected_cols):
                val = float(parts[col_idx])
                column_values[col_idx].append(val)
        except ValueError:
            missing_count += 1

    # Statistical variance & min/max
    stats = {}
    invariant_cols = []
    for col_idx, name in enumerate(COLUMN_NAMES[:expected_cols]):
        vals = column_values[col_idx]
        if not vals:
            continue
        n = len(vals)
        mean = sum(vals) / n
        variance = sum((x - mean) ** 2 for x in vals) / (n - 1) if n > 1 else 0.0
        std = variance ** 0.5
        min_v = min(vals)
        max_v = max(vals)

        stats[name] = {
            'mean': mean,
            'std': std,
            'min': min_v,
            'max': max_v,
            'is_constant': (min_v == max_v) or (std < 1e-6)
        }
        if stats[name]['is_constant']:
            invariant_cols.append(name)

    cycle_lengths = [len(cycs) for cycs in cycles_by_unit.values()]

    return {
        'filename': filename,
        'size_bytes': size_bytes,
        'total_rows': total_rows,
        'column_counts': list(col_counts),
        'total_units': len(units),
        'min_unit': min(units) if units else None,
        'max_unit': max(units) if units else None,
        'min_cycle': min(cycle_lengths) if cycle_lengths else None,
        'max_cycle': max(cycle_lengths) if cycle_lengths else None,
        'missing_count': missing_count,
        'invariant_columns': invariant_cols,
        'stats': stats
    }


def audit_rul(filename='RUL_FD001.txt'):
    filepath = os.path.join(DATASET_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Missing required ground-truth file: {filepath}")

    size_bytes = os.path.getsize(filepath)
    with open(filepath, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    ruls = [int(x) for x in lines]
    return {
        'filename': filename,
        'size_bytes': size_bytes,
        'total_ruls': len(ruls),
        'min_rul': min(ruls),
        'max_rul': max(ruls),
        'mean_rul': sum(ruls) / len(ruls),
        'values': ruls
    }


if __name__ == '__main__':
    print("=== NASA C-MAPSS FD001 AUDIT ===")
    train_res = audit_file('train_FD001.txt')
    print(f"\n[train_FD001.txt]")
    print(f"  File size: {train_res['size_bytes']} bytes")
    print(f"  Rows: {train_res['total_rows']}")
    print(f"  Units: {train_res['total_units']} (IDs {train_res['min_unit']} to {train_res['max_unit']})")
    print(f"  Cycle range per unit: min {train_res['min_cycle']}, max {train_res['max_cycle']}")
    print(f"  Column counts found: {train_res['column_counts']}")
    print(f"  Missing / corrupted entries: {train_res['missing_count']}")
    print(f"  Constant / Invariant columns ({len(train_res['invariant_columns'])}): {train_res['invariant_columns']}")

    test_res = audit_file('test_FD001.txt')
    print(f"\n[test_FD001.txt]")
    print(f"  File size: {test_res['size_bytes']} bytes")
    print(f"  Rows: {test_res['total_rows']}")
    print(f"  Units: {test_res['total_units']} (IDs {test_res['min_unit']} to {test_res['max_unit']})")
    print(f"  Cycle range per unit: min {test_res['min_cycle']}, max {test_res['max_cycle']}")
    print(f"  Missing / corrupted entries: {test_res['missing_count']}")

    rul_res = audit_rul('RUL_FD001.txt')
    print(f"\n[RUL_FD001.txt]")
    print(f"  File size: {rul_res['size_bytes']} bytes")
    print(f"  Total RUL entries: {rul_res['total_ruls']} (matching 100 test units)")
    print(f"  RUL range: min {rul_res['min_rul']}, max {rul_res['max_rul']}, mean {rul_res['mean_rul']:.2f}")
