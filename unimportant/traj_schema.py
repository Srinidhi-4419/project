# 3️⃣ TRAJ.NC TABLES

# a) Trajectory Table
schemas['trajectory_table'] = '''
CREATE TABLE trajectory_table (
    trajectory_id SERIAL PRIMARY KEY,
    platform_number VARCHAR(20) REFERENCES float_table(platform_number),
    cycle_number INTEGER,
    juld TIMESTAMP,
    juld_qc CHAR(1),
    latitude DECIMAL(10, 6),
    longitude DECIMAL(11, 6),
    position_qc CHAR(1),
    positioning_system VARCHAR(50),
    direction CHAR(1), -- 'A' for ascending, 'D' for descending
    data_mode CHAR(1), -- 'R' for real-time, 'D' for delayed, 'A' for adjusted
    
    -- Basic measurements at trajectory points
    pres DECIMAL(10, 3),
    temp DECIMAL(8, 4),
    psal DECIMAL(8, 4),
    parameter VARCHAR(50), -- Main parameter being measured
    
    -- BGC parameters (if present)
    doxy DECIMAL(8, 4),
    nitrate DECIMAL(8, 4),
    ph_in_situ_total DECIMAL(8, 4),
    chla DECIMAL(8, 4), -- Chlorophyll-a
    bbp700 DECIMAL(8, 4), -- Backscattering coefficient
    cdom DECIMAL(8, 4), -- Colored dissolved organic matter
    
    -- Station parameters (JSON array for flexibility)
    station_parameters JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_platform_cycle_traj (platform_number, cycle_number),
    INDEX idx_trajectory_time (juld),
    INDEX idx_trajectory_location (latitude, longitude)
);
'''

# b) Trajectory Depth Table (for depth-resolved trajectory data, if present)
schemas['trajectory_depth_table'] = '''
CREATE TABLE trajectory_depth_table (
    trajectory_depth_id SERIAL PRIMARY KEY,
    trajectory_id INTEGER REFERENCES trajectory_table(trajectory_id),
    platform_number VARCHAR(20) REFERENCES float_table(platform_number),
    cycle_number INTEGER,
    latitude DECIMAL(10, 6),
    longitude DECIMAL(11, 6),
    juld TIMESTAMP,
    
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
    
    -- BGC parameters (optional, depth-resolved)
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
    INDEX idx_traj_depth_platform (platform_number, cycle_number),
    INDEX idx_traj_depth_pres (pres),
    INDEX idx_trajectory_ref (trajectory_id)
);
'''

# Trajectory History Table (similar to profile history but for trajectory data)
schemas['trajectory_history_table'] = '''
CREATE TABLE trajectory_history_table (
    trajectory_history_id SERIAL PRIMARY KEY,
    platform_number VARCHAR(20) REFERENCES float_table(platform_number),
    cycle_number INTEGER,
    trajectory_id INTEGER REFERENCES trajectory_table(trajectory_id),
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
    INDEX idx_traj_hist_platform (platform_number, cycle_number),
    INDEX idx_traj_hist_date (history_date)
);
'''

print("✅ Traj.nc table schemas created")
print("Tables: trajectory_table, trajectory_depth_table, trajectory_history_table")