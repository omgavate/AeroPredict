"""
Database Configuration and Connection Pool Utility for AeroPredict.
Manages MySQL connection pooling, health checks, and schema initialization.
"""

import os
from pathlib import Path
from contextlib import contextmanager
import mysql.connector
from mysql.connector import pooling, Error
from dotenv import load_dotenv

# Load environment variables from backend/.env if present, otherwise system env
env_path = Path(__file__).resolve().parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

# Database Connection Parameters
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'aeropredict_db')
DB_POOL_NAME = os.getenv('DB_POOL_NAME', 'aeropredict_pool')
DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', 5))

_connection_pool = None


def get_db_config(include_db=True):
    """Returns database configuration dictionary."""
    config = {
        'host': DB_HOST,
        'port': DB_PORT,
        'user': DB_USER,
        'password': DB_PASSWORD,
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_unicode_ci',
        'use_pure': False
    }
    if include_db and DB_NAME:
        config['database'] = DB_NAME
    return config


def init_connection_pool():
    """Initializes the MySQL connection pool."""
    global _connection_pool
    if _connection_pool is not None:
        return _connection_pool

    config = get_db_config(include_db=True)
    try:
        _connection_pool = pooling.MySQLConnectionPool(
            pool_name=DB_POOL_NAME,
            pool_size=DB_POOL_SIZE,
            pool_reset_session=True,
            **config
        )
        return _connection_pool
    except Error as e:
        # If database does not exist, connection pool creation may fail; return None
        return None


@contextmanager
def get_db_connection():
    """
    Context manager yielding an active MySQL database connection.
    Attempts to pull from the pool first; falls back to direct connection if needed.
    """
    conn = None
    try:
        pool = init_connection_pool()
        if pool:
            conn = pool.get_connection()
        else:
            conn = mysql.connector.connect(**get_db_config(include_db=True))
        yield conn
    finally:
        if conn and conn.is_connected():
            conn.close()


def check_db_connection():
    """
    Tests connectivity to MySQL Server and verifies database selection.
    Returns:
        tuple: (is_connected: bool, message: str, details: dict)
    """
    details = {
        'host': DB_HOST,
        'port': DB_PORT,
        'user': DB_USER,
        'database': DB_NAME,
        'pool_active': _connection_pool is not None
    }

    try:
        # Test basic connection without specifying database first
        test_conn = mysql.connector.connect(**get_db_config(include_db=False))
        cursor = test_conn.cursor()
        cursor.execute("SELECT VERSION();")
        mysql_version = cursor.fetchone()[0]
        details['server_version'] = mysql_version

        # Test selecting target database
        cursor.execute(f"SHOW DATABASES LIKE '{DB_NAME}';")
        db_exists = cursor.fetchone() is not None
        details['database_exists'] = db_exists

        if not db_exists:
            cursor.close()
            test_conn.close()
            return False, f"Connected to MySQL {mysql_version}, but database '{DB_NAME}' does not exist.", details

        # Select database and run a test query
        cursor.execute(f"USE `{DB_NAME}`;")
        cursor.execute("SELECT 1 AS health_check;")
        result = cursor.fetchone()
        cursor.close()
        test_conn.close()

        if result and result[0] == 1:
            return True, f"Successfully connected to MySQL {mysql_version} (Database: {DB_NAME})", details
        else:
            return False, "Query executed but unexpected result returned", details

    except Error as err:
        details['error_code'] = err.errno
        details['sql_state'] = err.sqlstate
        return False, f"MySQL Error [{err.errno}]: {err.msg}", details


def init_database_schema():
    """
    Initializes the aeropredict_db database and all required tables:
    aircraft, sensor_readings, maintenance_alerts, maintenance_records, rul_predictions.
    """
    try:
        # Step 1: Connect to server and create database if not exists
        conn = mysql.connector.connect(**get_db_config(include_db=False))
        cursor = conn.cursor()
        cursor.execute(f"""
            CREATE DATABASE IF NOT EXISTS `{DB_NAME}`
            CHARACTER SET utf8mb4
            COLLATE utf8mb4_unicode_ci;
        """)
        cursor.execute(f"USE `{DB_NAME}`;")

        # Step 2: DDL statements
        ddl_statements = [
            # 1. Aircraft Table
            """
            CREATE TABLE IF NOT EXISTS aircraft (
                id INT AUTO_INCREMENT PRIMARY KEY,
                tail_number VARCHAR(20) NOT NULL UNIQUE,
                model VARCHAR(50) NOT NULL,
                manufacturer VARCHAR(50) NOT NULL,
                manufacturing_year INT NULL,
                engine_type VARCHAR(50) NOT NULL,
                cmapss_unit_id INT UNIQUE NULL,
                current_cycles INT NOT NULL DEFAULT 0,
                flight_hours INT NOT NULL DEFAULT 0,
                status ENUM('OPERATIONAL', 'UNDER_MAINTENANCE', 'ATTENTION_REQUIRED', 'RETIRED') NOT NULL DEFAULT 'OPERATIONAL',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_aircraft_status (status)
            ) ENGINE=InnoDB;
            """,
            # 2. Sensor Readings Table
            """
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                aircraft_id INT NOT NULL,
                cycle INT NOT NULL,
                setting_1 DECIMAL(10,4) NULL,
                setting_2 DECIMAL(10,4) NULL,
                setting_3 DECIMAL(10,4) NULL,
                sensor_1 DECIMAL(12,4) NULL,
                sensor_2 DECIMAL(12,4) NULL,
                sensor_3 DECIMAL(12,4) NULL,
                sensor_4 DECIMAL(12,4) NULL,
                sensor_5 DECIMAL(12,4) NULL,
                sensor_6 DECIMAL(12,4) NULL,
                sensor_7 DECIMAL(12,4) NULL,
                sensor_8 DECIMAL(12,4) NULL,
                sensor_9 DECIMAL(12,4) NULL,
                sensor_10 DECIMAL(12,4) NULL,
                sensor_11 DECIMAL(12,4) NULL,
                sensor_12 DECIMAL(12,4) NULL,
                sensor_13 DECIMAL(12,4) NULL,
                sensor_14 DECIMAL(12,4) NULL,
                sensor_15 DECIMAL(12,4) NULL,
                sensor_16 DECIMAL(12,4) NULL,
                sensor_17 DECIMAL(12,4) NULL,
                sensor_18 DECIMAL(12,4) NULL,
                sensor_19 DECIMAL(12,4) NULL,
                sensor_20 DECIMAL(12,4) NULL,
                sensor_21 DECIMAL(12,4) NULL,
                recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (aircraft_id) REFERENCES aircraft(id) ON DELETE CASCADE,
                INDEX idx_sensor_aircraft_cycle (aircraft_id, cycle DESC)
            ) ENGINE=InnoDB;
            """,
            # 3. Maintenance Alerts Table
            """
            CREATE TABLE IF NOT EXISTS maintenance_alerts (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                aircraft_id INT NOT NULL,
                alert_type ENUM('RUL_CRITICAL', 'RUL_WARNING', 'SENSOR_ANOMALY', 'MAINTENANCE_DUE') NOT NULL,
                severity ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL DEFAULT 'MEDIUM',
                message VARCHAR(255) NOT NULL,
                cycle INT NULL,
                predicted_rul DECIMAL(8,2) NULL,
                is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
                resolved_at TIMESTAMP NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (aircraft_id) REFERENCES aircraft(id) ON DELETE CASCADE,
                INDEX idx_alerts_aircraft (aircraft_id),
                INDEX idx_alerts_active_severity (is_resolved, severity)
            ) ENGINE=InnoDB;
            """,
            # 4. Maintenance Records Table
            """
            CREATE TABLE IF NOT EXISTS maintenance_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                aircraft_id INT NOT NULL,
                title VARCHAR(150) NOT NULL,
                description TEXT NULL,
                priority ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL DEFAULT 'MEDIUM',
                status ENUM('SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED') NOT NULL DEFAULT 'SCHEDULED',
                scheduled_date DATE NOT NULL,
                completed_date DATE NULL,
                technician_notes TEXT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (aircraft_id) REFERENCES aircraft(id) ON DELETE CASCADE,
                INDEX idx_maintenance_aircraft_status (aircraft_id, status),
                INDEX idx_maintenance_status_priority (status, priority)
            ) ENGINE=InnoDB;
            """,
            # 5. RUL Predictions Table
            """
            CREATE TABLE IF NOT EXISTS rul_predictions (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                aircraft_id INT NOT NULL,
                cycle INT NOT NULL,
                predicted_rul DECIMAL(8,2) NOT NULL,
                risk_level ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL,
                recommendation TEXT NOT NULL,
                predicted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (aircraft_id) REFERENCES aircraft(id) ON DELETE CASCADE,
                INDEX idx_prediction_aircraft_time (aircraft_id, predicted_at DESC)
            ) ENGINE=InnoDB;
            """
        ]

        for stmt in ddl_statements:
            cursor.execute(stmt)

        # Migration: Ensure manufacturing_year and flight_hours columns exist on aircraft
        cursor.execute("SHOW COLUMNS FROM aircraft LIKE 'manufacturing_year';")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE aircraft ADD COLUMN manufacturing_year INT NULL AFTER manufacturer;")

        cursor.execute("SHOW COLUMNS FROM aircraft LIKE 'flight_hours';")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE aircraft ADD COLUMN flight_hours INT NOT NULL DEFAULT 0 AFTER current_cycles;")

        conn.commit()
        cursor.close()
        conn.close()
        return True, f"Schema successfully initialized in database '{DB_NAME}'"

    except Error as err:
        return False, f"Schema initialization failed: {err.msg}"
