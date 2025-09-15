# Create comprehensive PostgreSQL schema for Argo float data
import json

# Define all table schemas as SQL CREATE statements
schemas = {}

# 1️⃣ PROFILE.NC TABLES

# a) Float Table (one row per float)
schemas['float_table'] = '''
CREATE TABLE float_table (
    platform_number VARCHAR(20) PRIMARY KEY,
    project_name VARCHAR(100),
    pi_name VARCHAR(100),
    launch_latitude DECIMAL(10, 6),
    launch_longitude DECIMAL(11, 6),
    platform_type VARCHAR(50),
    firmware_version VARCHAR(50),
    wmo_inst_type VARCHAR(10),
    positioning_system VARCHAR(50),
    -- Additional metadata fields
    data_type VARCHAR(20),
    format_version VARCHAR(10),
    handbook_version VARCHAR(10),
    date_creation TIMESTAMP,
    date_update TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''

# b) Profile Table (one row per profile/cycle)
schemas['profile_table'] = '''
CREATE TABLE profile_table (
    profile_id SERIAL PRIMARY KEY,
    platform_number VARCHAR(20) REFERENCES float_table(platform_number),
    cycle_number INTEGER,
    juld TIMESTAMP,
    juld_qc CHAR(1),
    latitude DECIMAL(10, 6),
    longitude DECIMAL(11, 6),
    position_qc CHAR(1),
    direction CHAR(1), -- 'A' for ascending, 'D' for descending
    data_mode CHAR(1), -- 'R' for real-time, 'D' for delayed, 'A' for adjusted
    vertical_sampling_scheme VARCHAR(100),
    config_mission_number INTEGER,
    profile_pres_qc CHAR(1),
    profile_temp_qc CHAR(1),
    profile_psal_qc CHAR(1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform_number, cycle_number, direction)
);
'''

# c) Depth Measurements Table (one row per depth per profile)
schemas['depth_measurements_table'] = '''
CREATE TABLE depth_measurements_table (
    measurement_id SERIAL PRIMARY KEY,
    profile_id INTEGER REFERENCES profile_table(profile_id),
    platform_number VARCHAR(20) REFERENCES float_table(platform_number),
    cycle_number INTEGER,
    latitude DECIMAL(10, 6),
    longitude DECIMAL(11, 6),
    
    -- Pressure measurements
    pres DECIMAL(10, 3),
    pres_qc CHAR(1),
    pres_adjusted DECIMAL(10, 3),
    pres_adjusted_qc CHAR(1),
    pres_adjusted_error DECIMAL(10, 3),
    
    -- Temperature measurements
    temp DECIMAL(8, 4),
    temp_qc CHAR(1),
    temp_adjusted DECIMAL(8, 4),
    temp_adjusted_qc CHAR(1),
    temp_adjusted_error DECIMAL(8, 4),
    
    -- Salinity measurements
    psal DECIMAL(8, 4),
    psal_qc CHAR(1),
    psal_adjusted DECIMAL(8, 4),
    psal_adjusted_qc CHAR(1),
    psal_adjusted_error DECIMAL(8, 4),
    
    -- BGC parameters (optional)
    doxy DECIMAL(8, 4),
    doxy_qc CHAR(1),
    doxy_adjusted DECIMAL(8, 4),
    doxy_adjusted_qc CHAR(1),
    doxy_adjusted_error DECIMAL(8, 4),
    
    nitrate DECIMAL(8, 4),
    nitrate_qc CHAR(1),
    nitrate_adjusted DECIMAL(8, 4),
    nitrate_adjusted_qc CHAR(1),
    nitrate_adjusted_error DECIMAL(8, 4),
    
    ph_in_situ_total DECIMAL(8, 4),
    ph_in_situ_total_qc CHAR(1),
    ph_in_situ_total_adjusted DECIMAL(8, 4),
    ph_in_situ_total_adjusted_qc CHAR(1),
    ph_in_situ_total_adjusted_error DECIMAL(8, 4),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_platform_cycle (platform_number, cycle_number),
    INDEX idx_profile_id (profile_id),
    INDEX idx_pres (pres),
    INDEX idx_temp (temp),
    INDEX idx_psal (psal)
);
'''

# d) History Table
schemas['history_table'] = '''
CREATE TABLE history_table (
    history_id SERIAL PRIMARY KEY,
    platform_number VARCHAR(20) REFERENCES float_table(platform_number),
    cycle_number INTEGER,
    history_institution VARCHAR(100),
    history_step VARCHAR(100),
    history_software VARCHAR(100),
    history_software_release VARCHAR(50),
    history_reference VARCHAR(200),
    history_date TIMESTAMP,
    history_action VARCHAR(100),
    history_parameter VARCHAR(100),
    history_start_pres DECIMAL(10, 3),
    history_stop_pres DECIMAL(10, 3),
    history_previous_value TEXT,
    history_qctest VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_platform_cycle (platform_number, cycle_number),
    INDEX idx_history_date (history_date)
);
'''

print("✅ Profile.nc table schemas created")
print("Tables: float_table, profile_table, depth_measurements_table, history_table")