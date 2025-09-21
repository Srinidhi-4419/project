# script.py
# Generates the corrected Argo PostgreSQL schema as 'argo_float_schema_corrected.sql'

schema_sql = """
-- Argo Float Database Schema
-- Generated on 2025-09-12
-- Complete PostgreSQL schema for Argo oceanographic float data
-- CORRECTED VERSION - All syntax errors fixed

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- CREATE EXTENSION IF NOT EXISTS "postgis"; -- Commented out - install separately if needed

-- Set timezone
SET timezone = 'UTC';

-- QC Flags Table
CREATE TABLE qc_flags_table (
    qc_flag CHAR(1) PRIMARY KEY,
    qc_description VARCHAR(100),
    qc_meaning TEXT
);

INSERT INTO qc_flags_table (qc_flag, qc_description, qc_meaning) VALUES
('0', 'No QC performed', 'No quality control has been performed'),
('1', 'Good data', 'All real-time and delayed-mode QC tests passed'),
('2', 'Probably good data', 'A few real-time QC tests failed, value may still be good'),
('3', 'Bad data that are potentially correctable', 'Value may be recoverable with further work'),
('4', 'Bad data', 'Value is bad and not recoverable'),
('5', 'Value changed', 'Value was changed as a result of QC'),
('6', 'Not used', 'Reserved for future use'),
('7', 'Not used', 'Reserved for future use'),
('8', 'Estimated value', 'Value has been estimated using a model or other method'),
('9', 'Missing value', 'Value is missing');

-- Data Mode Table
CREATE TABLE data_mode_table (
    data_mode_flag CHAR(1) PRIMARY KEY,
    data_mode_description VARCHAR(50),
    data_mode_meaning TEXT
);

INSERT INTO data_mode_table (data_mode_flag, data_mode_description, data_mode_meaning) VALUES
('R', 'Real-time', 'Real-time data, automatic QC only'),
('A', 'Real-time adjusted', 'Real-time data with adjustments applied'),
('D', 'Delayed-mode', 'Delayed-mode data with full scientific QC');

-- BGC Parameters Table
CREATE TABLE bgc_parameters_table (
    parameter_code VARCHAR(20) PRIMARY KEY,
    parameter_name VARCHAR(100),
    parameter_units VARCHAR(20),
    parameter_description TEXT,
    is_core_parameter BOOLEAN DEFAULT FALSE
);

INSERT INTO bgc_parameters_table (parameter_code, parameter_name, parameter_units, parameter_description, is_core_parameter) VALUES
('PRES', 'Pressure', 'decibar', 'Sea water pressure', TRUE),
('TEMP', 'Temperature', 'degree_Celsius', 'Sea water temperature', TRUE),
('PSAL', 'Salinity', 'psu', 'Practical salinity', TRUE),
('DOXY', 'Dissolved Oxygen', 'micromole/kg', 'Dissolved oxygen concentration', FALSE),
('CHLA', 'Chlorophyll-a', 'mg/m3', 'Chlorophyll-a concentration', FALSE),
('BBP700', 'Backscattering', 'm-1', 'Particle backscattering coefficient at 700nm', FALSE),
('NITRATE', 'Nitrate', 'micromole/kg', 'Nitrate concentration', FALSE),
('PH_IN_SITU_TOTAL', 'pH', '1', 'pH in situ total scale', FALSE),
('CDOM', 'CDOM', 'ppb', 'Colored dissolved organic matter fluorescence', FALSE),
('DOWNWELLING_PAR', 'PAR', 'microMoleQuanta/m2/s', 'Downwelling photosynthetic available radiation', FALSE);

-- Float Table
CREATE TABLE float_table (
    platform_number VARCHAR(20) PRIMARY KEY,
    project_name VARCHAR(100),
    wmo_inst_type VARCHAR(10),
    positioning_system VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Meta Table
CREATE TABLE meta_table (
    meta_id SERIAL PRIMARY KEY,
    platform_number VARCHAR(20) REFERENCES float_table(platform_number),
    data_type VARCHAR(20),
    format_version VARCHAR(10),
    handbook_version VARCHAR(10),
    date_creation TIMESTAMP,
    date_update TIMESTAMP,
    ptt VARCHAR(20),
    trans_system VARCHAR(50),
    trans_system_id VARCHAR(50),
    trans_frequency VARCHAR(20),
    positioning_system VARCHAR(50),
    platform_family VARCHAR(50),
    platform_type VARCHAR(50),
    platform_maker VARCHAR(100),
    firmware_version VARCHAR(50),
    manual_version VARCHAR(50),
    float_serial_no VARCHAR(50),
    dac_format_id VARCHAR(20),
    wmo_inst_type VARCHAR(10),
    project_name VARCHAR(100),
    data_centre VARCHAR(50),
    pi_name VARCHAR(100),
    anomaly TEXT,
    battery_type VARCHAR(50),
    battery_packs INTEGER,
    controller_board_type_primary VARCHAR(100),
    controller_board_type_secondary VARCHAR(100),
    serial_no_primary VARCHAR(50),
    serial_no_secondary VARCHAR(50),
    special_features TEXT,
    float_owner VARCHAR(100),
    operating_institution VARCHAR(100),
    customisation TEXT,
    launch_date DATE,
    launch_latitude DECIMAL(10, 6),
    launch_longitude DECIMAL(11, 6),
    launch_qc CHAR(1),
    start_date DATE,
    start_date_qc CHAR(1),
    startup_date DATE,
    startup_date_qc CHAR(1),
    end_mission_date DATE,
    end_mission_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform_number)
);

-- Profile Table
CREATE TABLE profile_table (
    profile_id SERIAL PRIMARY KEY,
    platform_number VARCHAR(20) REFERENCES float_table(platform_number),
    cycle_number INTEGER,
    juld TIMESTAMP,
    juld_qc CHAR(1),
    latitude DECIMAL(10, 6),
    longitude DECIMAL(11, 6),
    position_qc CHAR(1),
    direction CHAR(1),
    data_mode CHAR(1),
    vertical_sampling_scheme VARCHAR(100),
    config_mission_number INTEGER,
    profile_pres_qc CHAR(1),
    profile_temp_qc CHAR(1),
    profile_psal_qc CHAR(1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform_number, cycle_number, direction)
);

-- Depth Measurements Table
CREATE TABLE depth_measurements_table (
    measurement_id SERIAL PRIMARY KEY,
    profile_id INTEGER REFERENCES profile_table(profile_id),
    platform_number VARCHAR(20) REFERENCES float_table(platform_number),
    cycle_number INTEGER,
    latitude DECIMAL(10, 6),
    longitude DECIMAL(11, 6),

    pres DECIMAL(10, 3),
    pres_qc CHAR(1),
    pres_adjusted DECIMAL(10, 3),
    pres_adjusted_qc CHAR(1),
    pres_adjusted_error DECIMAL(10, 3),

    temp DECIMAL(8, 4),
    temp_qc CHAR(1),
    temp_adjusted DECIMAL(8, 4),
    temp_adjusted_qc CHAR(1),
    temp_adjusted_error DECIMAL(8, 4),

    psal DECIMAL(8, 4),
    psal_qc CHAR(1),
    psal_adjusted DECIMAL(8, 4),
    psal_adjusted_qc CHAR(1),
    psal_adjusted_error DECIMAL(8, 4),

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

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- History Table
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Launch Config Table
CREATE TABLE launch_config_table (
    launch_config_id SERIAL PRIMARY KEY,
    platform_number VARCHAR(20) REFERENCES float_table(platform_number),
    launch_config_parameter_name VARCHAR(100),
    launch_config_parameter_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Config Table
CREATE TABLE config_table (
    config_id SERIAL PRIMARY KEY,
    platform_number VARCHAR(20) REFERENCES float_table(platform_number),
    config_parameter_name VARCHAR(100),
    config_parameter_value TEXT,
    config_mission_number INTEGER,
    config_mission_comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sensor Table
CREATE TABLE sensor_table (
    sensor_id SERIAL PRIMARY KEY,
    platform_number VARCHAR(20) REFERENCES float_table(platform_number),
    sensor VARCHAR(50),
    sensor_maker VARCHAR(100),
    sensor_model VARCHAR(100),
    sensor_serial_no VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Parameter Table
CREATE TABLE parameter_table (
    parameter_id SERIAL PRIMARY KEY,
    platform_number VARCHAR(20) REFERENCES float_table(platform_number),
    parameter VARCHAR(50),
    parameter_sensor VARCHAR(50),
    parameter_units VARCHAR(20),
    parameter_accuracy VARCHAR(50),
    parameter_resolution VARCHAR(50),
    predeployment_calib_equation TEXT,
    coefficient JSONB,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trajectory Table (Enhanced version)
CREATE TABLE trajectory_table (
    trajectory_id SERIAL PRIMARY KEY,
    platform_number VARCHAR(20) REFERENCES float_table(platform_number),
    cycle_number INTEGER,
    juld_first_location TIMESTAMP,
    juld_qc CHAR(1),
    first_latitude DECIMAL(10, 6),
    first_longitude DECIMAL(11, 6),
    position_qc CHAR(1),
    positioning_system VARCHAR(50),
    data_mode CHAR(1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    juld_last_location TIMESTAMP,
    juld_first_message TIMESTAMP,
    juld_last_message TIMESTAMP,
    juld_ascent_start TIMESTAMP,
    juld_ascent_end TIMESTAMP,
    juld_descent_start TIMESTAMP,
    juld_descent_end TIMESTAMP,
    juld_park_start TIMESTAMP,
    juld_park_end TIMESTAMP,
    juld_transmission_start TIMESTAMP,
    juld_transmission_end TIMESTAMP,
    
    juld_first_location_status CHAR(1),
    juld_last_location_status CHAR(1),
    juld_first_message_status CHAR(1),
    juld_last_message_status CHAR(1),
    
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    last_latitude DECIMAL(10, 6),
    last_longitude DECIMAL(11, 6),
    
    config_mission_number INTEGER,
    grounded CHAR(1),
    representative_park_pressure DECIMAL(10, 3),
    representative_park_pressure_status CHAR(1),
    cycle_number_adjusted INTEGER,
    
    UNIQUE(platform_number, cycle_number)
);

-- Trajectory Depth Table (Enhanced version)
CREATE TABLE trajectory_depth_table (
    trajectory_depth_id SERIAL PRIMARY KEY,
    trajectory_id INTEGER REFERENCES trajectory_table(trajectory_id) ON DELETE CASCADE,
    platform_number VARCHAR(20) REFERENCES float_table(platform_number),
    cycle_number INTEGER,
    latitude DECIMAL(10, 6),
    longitude DECIMAL(11, 6),
    juld TIMESTAMP,
    
    pres DECIMAL(10, 3),
    pres_qc CHAR(1),
    pres_adjusted DECIMAL(10, 3),
    pres_adjusted_qc CHAR(1),
    pres_adjusted_error DECIMAL(10, 3),
    
    temp DECIMAL(8, 4),
    temp_qc CHAR(1),
    temp_adjusted DECIMAL(8, 4),
    temp_adjusted_qc CHAR(1),
    temp_adjusted_error DECIMAL(8, 4),
    
    psal DECIMAL(8, 4),
    psal_qc CHAR(1),
    psal_adjusted DECIMAL(8, 4),
    psal_adjusted_qc CHAR(1),
    psal_adjusted_error DECIMAL(8, 4),
    
    doxy DECIMAL(8, 4),
    doxy_qc CHAR(1),
    chla DECIMAL(8, 4),
    chla_qc CHAR(1),
    bbp700 DECIMAL(8, 4),
    bbp700_qc CHAR(1),
    nitrate DECIMAL(8, 4),
    nitrate_qc CHAR(1),
    ph_in_situ_total DECIMAL(8, 4),
    ph_in_situ_total_qc CHAR(1),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    measurement_code INTEGER,
    measurement_index INTEGER,
    
    juld_status CHAR(1),
    juld_adjusted TIMESTAMP,
    juld_adjusted_qc CHAR(1),
    juld_adjusted_status CHAR(1),
    
    position_accuracy CHAR(1),
    axes_error_ellipse_major DECIMAL(8, 2),
    axes_error_ellipse_minor DECIMAL(8, 2),
    axes_error_ellipse_angle DECIMAL(6, 2),
    satellite_name VARCHAR(10),
    positioning_system VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    position_qc CHAR(1),
    
    UNIQUE(platform_number, cycle_number, measurement_code, juld),
    UNIQUE(platform_number, cycle_number, measurement_code, measurement_index)
);

-- Performance indexes
CREATE INDEX idx_float_launch_location ON float_table(launch_latitude, launch_longitude);
CREATE INDEX idx_profile_location ON profile_table(latitude, longitude);
CREATE INDEX idx_profile_date ON profile_table(juld);
CREATE INDEX idx_depth_measurements_depth ON depth_measurements_table(pres);
CREATE INDEX idx_trajectory_location ON trajectory_table(first_latitude, first_longitude);
CREATE INDEX idx_trajectory_platform_cycle ON trajectory_table(platform_number, cycle_number);
CREATE INDEX idx_trajectory_time ON trajectory_table(juld_first_location);
CREATE INDEX idx_trajectory_timing ON trajectory_table(juld_first_location, juld_last_location);
CREATE INDEX idx_trajectory_depth_pres ON trajectory_depth_table(pres);
CREATE INDEX idx_trajectory_depth_trajectory_ref ON trajectory_depth_table(trajectory_id);
CREATE INDEX idx_trajectory_depth_measurement ON trajectory_depth_table(measurement_code);
CREATE INDEX idx_trajectory_depth_platform_cycle ON trajectory_depth_table(platform_number, cycle_number);
CREATE INDEX idx_trajectory_depth_position ON trajectory_depth_table(latitude, longitude);
CREATE INDEX idx_trajectory_depth_time ON trajectory_depth_table(juld);
CREATE INDEX idx_depth_platform_cycle ON depth_measurements_table(platform_number, cycle_number);
CREATE INDEX idx_depth_profile_id ON depth_measurements_table(profile_id);
CREATE INDEX idx_depth_temp ON depth_measurements_table(temp);
CREATE INDEX idx_depth_psal ON depth_measurements_table(psal);
CREATE INDEX idx_history_platform_cycle ON history_table(platform_number, cycle_number);
CREATE INDEX idx_history_date ON history_table(history_date);
CREATE INDEX idx_launch_config_platform_param ON launch_config_table(platform_number, launch_config_parameter_name);
CREATE INDEX idx_config_platform_mission ON config_table(platform_number, config_mission_number);
CREATE INDEX idx_config_param_name ON config_table(config_parameter_name);
CREATE INDEX idx_sensor_platform_sensor ON sensor_table(platform_number, sensor);
CREATE INDEX idx_parameter_platform_param ON parameter_table(platform_number, parameter);

-- Partial indexes for active data
CREATE INDEX idx_active_profiles ON profile_table(platform_number, cycle_number) 
    WHERE juld > (CURRENT_DATE - INTERVAL '2 years');

-- Comments for documentation
COMMENT ON TABLE float_table IS 'Master table containing one row per Argo float with basic metadata';
COMMENT ON TABLE profile_table IS 'Profile-level data with one row per float cycle/profile';
COMMENT ON TABLE depth_measurements_table IS 'Depth-resolved measurements from profiles';
COMMENT ON TABLE trajectory_table IS 'Trajectory data showing float positions over time';
COMMENT ON TABLE meta_table IS 'Comprehensive metadata for each float from meta.nc files';
COMMENT ON TABLE history_table IS 'Processing history and quality control actions';

-- Views
CREATE VIEW v_active_floats AS
SELECT 
    f.*,
    COUNT(p.profile_id) as total_profiles,
    MAX(p.juld) as last_profile_date,
    MIN(p.juld) as first_profile_date
FROM float_table f
LEFT JOIN profile_table p ON f.platform_number = p.platform_number
GROUP BY f.platform_number;

CREATE VIEW v_latest_profiles AS
SELECT DISTINCT ON (platform_number) 
    platform_number,
    cycle_number,
    juld,
    latitude,
    longitude,
    data_mode
FROM profile_table 
ORDER BY platform_number, juld DESC;

-- Script end
"""

with open("argo_float_schema_corrected.sql", "w") as f:
    f.write(schema_sql)

print("✅ Argo Float PostgreSQL schema file generated as argo_float_schema_corrected.sql.")
print("To apply the schema, run:\npsql -U postgres -d argo_floats -f argo_float_schema_corrected.sql")
