# 2️⃣ META.NC TABLES

# a) Meta Table (one row per float)
schemas['meta_table'] = '''
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
'''

# b) Launch Config Table
schemas['launch_config_table'] = '''
CREATE TABLE launch_config_table (
    launch_config_id SERIAL PRIMARY KEY,
    platform_number VARCHAR(20) REFERENCES float_table(platform_number),
    launch_config_parameter_name VARCHAR(100),
    launch_config_parameter_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_platform_param (platform_number, launch_config_parameter_name)
);
'''

# c) Config Table
schemas['config_table'] = '''
CREATE TABLE config_table (
    config_id SERIAL PRIMARY KEY,
    platform_number VARCHAR(20) REFERENCES float_table(platform_number),
    config_parameter_name VARCHAR(100),
    config_parameter_value TEXT,
    config_mission_number INTEGER,
    config_mission_comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_platform_mission (platform_number, config_mission_number),
    INDEX idx_param_name (config_parameter_name)
);
'''

# d) Sensor Table
schemas['sensor_table'] = '''
CREATE TABLE sensor_table (
    sensor_id SERIAL PRIMARY KEY,
    platform_number VARCHAR(20) REFERENCES float_table(platform_number),
    sensor VARCHAR(50),
    sensor_maker VARCHAR(100),
    sensor_model VARCHAR(100),
    sensor_serial_no VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_platform_sensor (platform_number, sensor)
);
'''

# e) Parameter Table
schemas['parameter_table'] = '''
CREATE TABLE parameter_table (
    parameter_id SERIAL PRIMARY KEY,
    platform_number VARCHAR(20) REFERENCES float_table(platform_number),
    parameter VARCHAR(50),
    parameter_sensor VARCHAR(50),
    parameter_units VARCHAR(20),
    parameter_accuracy VARCHAR(50),
    parameter_resolution VARCHAR(50),
    predeployment_calib_equation TEXT,
    coefficient JSONB, -- Store coefficients as JSON for flexibility
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_platform_parameter (platform_number, parameter)
);
'''

print("✅ Meta.nc table schemas created")
print("Tables: meta_table, launch_config_table, config_table, sensor_table, parameter_table")