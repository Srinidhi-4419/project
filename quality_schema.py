# Create additional utility tables and views for the Argo float database

# Quality Control Lookup Table
schemas['qc_flags_table'] = '''
CREATE TABLE qc_flags_table (
    qc_flag CHAR(1) PRIMARY KEY,
    qc_description VARCHAR(100),
    qc_meaning TEXT
);

-- Insert standard Argo QC flag values
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
'''

# Data Mode Lookup Table
schemas['data_mode_table'] = '''
CREATE TABLE data_mode_table (
    data_mode_flag CHAR(1) PRIMARY KEY,
    data_mode_description VARCHAR(50),
    data_mode_meaning TEXT
);

INSERT INTO data_mode_table (data_mode_flag, data_mode_description, data_mode_meaning) VALUES
('R', 'Real-time', 'Real-time data, automatic QC only'),
('A', 'Real-time adjusted', 'Real-time data with adjustments applied'),
('D', 'Delayed-mode', 'Delayed-mode data with full scientific QC');
'''

# BGC Parameter Types Table
schemas['bgc_parameters_table'] = '''
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
'''

print("✅ Utility tables created")
print("Tables: qc_flags_table, data_mode_table, bgc_parameters_table")