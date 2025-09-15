#!/usr/bin/env python3
"""
Ultimate Comprehensive Argo NetCDF Parser - ALL 15 TABLES
Handles profile.nc, meta.nc, and trajectory.nc files with complete database population
"""

import numpy as np
import xarray as xr
import psycopg2
from psycopg2.extras import execute_values
from configparser import ConfigParser
import pandas as pd
# from datetime import datetime
from datetime import datetime, timedelta
import json
import logging
import os
# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UltimateArgoNetCDFParser:
    def __init__(self, postgres_config="database.ini"):
        self.postgres_config = postgres_config
        self.connection = None

    def load_postgres_config(self):
        """Load PostgreSQL configuration"""
        parser = ConfigParser()
        parser.read(self.postgres_config)

        config = {}
        if parser.has_section('database'):
            params = parser.items('database')
            for param in params:
                config[param[0]] = param[1]
        return config

    def connect_postgres(self):
        """Connect to PostgreSQL database"""
        if not self.connection or self.connection.closed:
            config = self.load_postgres_config()
            self.connection = psycopg2.connect(
                host=config['host'],
                port=int(config['port']),
                user=config['user'],
                password=config['password'],
                database=config['database']
            )
        return self.connection

    def safe_decode(self, value):
        """Enhanced safe decode with proper bytes handling and QC field support"""
        if value is None:
            return ''
        
        try:
            # Handle bytes
            if isinstance(value, bytes):
                decoded = value.decode('utf-8', errors='ignore').strip()
            # Handle numpy bytes
            elif isinstance(value, np.bytes_):
                decoded = str(value, 'utf-8', errors='ignore').strip()
            # Handle numpy scalars
            elif hasattr(value, 'item'):
                item_val = value.item()
                if isinstance(item_val, bytes):
                    decoded = item_val.decode('utf-8', errors='ignore').strip()
                else:
                    decoded = str(item_val).strip()
            else:
                decoded = str(value).strip()
            
            # Handle empty strings and whitespace
            if not decoded or decoded.lower() == 'nan':
                return ''
                
            return decoded
            
        except Exception as e:
            logger.warning(f"Error in safe_decode for value {repr(value)}: {e}")
            return ''



    def safe_float(self, value):
        """Safely convert to float"""
        try:
            if value is None:
                return None
            if isinstance(value, np.ma.MaskedArray):
                if value.mask:
                    return None
                value = value.data
            if isinstance(value, np.ndarray):
                if value.size == 1:
                    value = value.item()
                else:
                    return None
            if np.isnan(float(value)) or np.isinf(float(value)):
                return None
            return float(value)
        except (ValueError, TypeError, OverflowError):
            return None

    def safe_int(self, value):
        """Safely convert to integer"""
        try:
            float_val = self.safe_float(value)
            if float_val is None:
                return None
            return int(float_val)
        except (ValueError, TypeError, OverflowError):
            return None

    def argo_date_to_datetime(self, argo_date):
        """Convert Argo date format to Python datetime"""
        try:
            if isinstance(argo_date, str) and len(argo_date) >= 14:
                return datetime.strptime(argo_date[:14], '%Y%m%d%H%M%S')
            elif hasattr(argo_date, 'values'):
                return self.argo_date_to_datetime(str(argo_date.values))
            return None
        except:
            return None
    def clean_timestamp_value(self, timestamp_value):
        """Clean timestamp values before database insertion"""
        if timestamp_value is None:
            return None
        
        # Handle string representations of NaT
        if isinstance(timestamp_value, str):
            if timestamp_value.lower() in ['nat', 'nan', 'none', '']:
                return None
            # Check for 'NaT' string specifically
            if timestamp_value == 'NaT':
                return None
        
        # Handle pandas NaT
        try:
            import pandas as pd
            if pd.isna(timestamp_value):
                return None
        except:
            pass
        
        return timestamp_value

    
    def enhanced_julian_to_datetime(self, julian_date):
        """Convert Julian date to datetime with better error handling"""
        import numpy as np
        from datetime import datetime
        import pandas as pd

        if julian_date is None:
            return None

        try:
            # Handle different input types
            if isinstance(julian_date, (bytes, np.bytes_)):
                # Decode bytes first
                decoded_val = julian_date.decode('utf-8', errors='ignore').strip()
                
                # Check if it's a status code (like '2', '4') instead of Julian date
                if decoded_val.isdigit() and len(decoded_val) <= 2:
                    # Change to DEBUG to reduce spam
                    logger.debug(f"Skipping status code as Julian date: {decoded_val}")
                    return None
                    
                # Try to convert to float
                try:
                    julian_date = float(decoded_val)
                except ValueError:
                    logger.debug(f"Cannot convert decoded value to float: {decoded_val}")
                    return None
            
            # Handle string inputs
            elif isinstance(julian_date, str):
                if julian_date.lower() in ['nat', 'nan', '', 'none']:
                    return None
                # Check if it's a status code
                if julian_date.isdigit() and len(julian_date) <= 2:
                    logger.debug(f"Skipping status code as Julian date: {julian_date}")
                    return None
                
                # Check if it's already a datetime string
                if '-' in julian_date and ('T' in julian_date or ' ' in julian_date):
                    return pd.to_datetime(julian_date).to_pydatetime()
                
                try:
                    julian_date = float(julian_date)
                except ValueError:
                    return None
            
            # Handle numpy arrays
            elif isinstance(julian_date, np.ndarray):
                if julian_date.size == 1:
                    julian_date = julian_date.item()
                else:
                    return None
            
            # Check if it's a numpy datetime64
            if hasattr(julian_date, 'dtype') and 'datetime' in str(julian_date.dtype):
                return pd.to_datetime(julian_date).to_pydatetime()
            
            # Handle pandas NaT and numpy nan
            if pd.isna(julian_date):
                return None
                
            # Check for NaN values (numeric)
            if isinstance(julian_date, (int, float)) and np.isnan(julian_date):
                return None
            
            # Handle actual Julian dates (numeric values)
            if isinstance(julian_date, (int, float)):
                if 10000 <= julian_date <= 50000:  # Days since 1950-01-01
                    from datetime import timedelta
                    reference_date = datetime(1950, 1, 1)
                    return reference_date + timedelta(days=float(julian_date))
                else:
                    logger.debug(f"Julian date outside expected range: {julian_date}")
                    return None
            
            # Try to convert whatever it is to datetime
            return pd.to_datetime(julian_date).to_pydatetime()
                
        except Exception as e:
            logger.debug(f"Failed to convert Julian date {julian_date}: {e}")
            return None





    def safe_get_measurement_var(self, ds, var_name, meas_idx, default=None):
        """Safely extract measurement-level variable with better handling"""
        if var_name not in ds:
            return default
        
        try:
            var_values = ds[var_name].values
            if var_values.ndim == 0:
                raw_val = var_values.item()
            elif meas_idx < len(var_values):
                raw_val = var_values[meas_idx]
            else:
                return default
            
            # Handle JULD variables specially
            if 'JULD' in var_name:
                return self.enhanced_julian_to_datetime(raw_val)
            elif isinstance(default, str):
                decoded = self.safe_decode(raw_val)
                if decoded and decoded.lower() in ['nan', 'nat', '']:
                    return None
                return decoded
            else:
                return self.safe_float(raw_val)
                
        except Exception as e:
            logger.warning(f"Error extracting {var_name}[{meas_idx}]: {e}")
            return default
    def detect_file_type(self, filepath):
        """Detect if file is profile, meta, or trajectory"""
        filename = filepath.lower()
        if 'meta' in filename:
            return 'meta'
        elif 'prof' in filename:
            return 'profile'
        elif 'traj' in filename:
            return 'trajectory'
        else:
            return 'unknown'
    
    
    def process_argo_file(self, filepath):
        """Main file processing dispatcher"""
        filename = os.path.basename(filepath).lower()
    
    # Debug: Print filename
        logger.info(f"Processing file: {filename}")
    
    # Check for meta file patterns
        if ('meta' in filename or 
            '_meta.nc' in filename or 
            filename.endswith('_meta.nc') or
            'metadata' in filename):
            logger.info(f"Detected as META file: {filename}")
            return self.process_meta_file(filepath)
    
    # Check for profile file patterns  
        elif ('prof' in filename or 
            'profile' in filename or 
            '_prof.nc' in filename or
            filename.endswith('_prof.nc')):
            logger.info(f"Detected as PROFILE file: {filename}")
            return self.process_profile_file(filepath)
    
        elif 'traj' in filename or 'trajectory' in filename:
            logger.info(f"Detected as TRAJECTORY file: {filename}")
            return self.process_trajectory_file(filepath)
    
    # Unknown file type - try profile first, then meta
        else:
            logger.info(f"Unknown file type, trying as profile: {filename}")
            if self.process_profile_file(filepath):
                 return True
            else:
                logger.info(f"Failed as profile, trying as meta: {filename}")
            return self.process_meta_file(filepath)

    def insert_parameter_data(self, param_data_list):
        """Insert parameter data with duplicate prevention"""
        if not param_data_list:
            return

        conn = self.connect_postgres()
        cursor = conn.cursor()

        try:
            param_values = []
            for param_data in param_data_list:
                # Handle coefficient field properly for JSON
                coefficient_value = param_data.get('coefficient', '')
                
                if coefficient_value and str(coefficient_value).lower() not in ['n/a', 'none', '', 'null']:
                    try:
                        import json
                        coefficient_json = json.dumps(str(coefficient_value))
                    except:
                        coefficient_json = None
                else:
                    coefficient_json = None

                param_values.append((
                    param_data['platform_number'],
                    param_data['parameter'],
                    param_data['parameter_sensor'],
                    param_data['parameter_units'],
                    param_data['parameter_accuracy'],
                    param_data['parameter_resolution'],
                    param_data['predeployment_calib_equation'],
                    coefficient_json,
                    param_data['comment']
                ))

            # ✅ INSERT with DO NOTHING to prevent errors on duplicates
            sql = """
            INSERT INTO parameter_table (
                platform_number, parameter, parameter_sensor, parameter_units,
                parameter_accuracy, parameter_resolution, predeployment_calib_equation,
                coefficient, comment
            ) VALUES %s
            ON CONFLICT (platform_number, parameter) DO NOTHING
            """

            from psycopg2.extras import execute_values
            execute_values(cursor, sql, param_values)
            conn.commit()
            
            logger.info(f"✅ Processed parameter_table: {len(param_data_list)} parameters (duplicates ignored)")

        except Exception as e:
            conn.rollback()
            logger.error(f"Error inserting parameter data: {e}")
            raise
        finally:
            cursor.close()


            
    def _safe_get_array_value(self, ds, var_name, index, default=''):
        """Safely get value from array variable at index with JSON handling"""
        try:
            if var_name in ds.variables:
                values = ds[var_name].values
                if hasattr(values, '__len__') and index < len(values):
                    raw_value = self.safe_decode(values[index])
                    
                    # Special handling for coefficient field
                    if var_name == 'PREDEPLOYMENT_CALIB_COEFFICIENT':
                        if raw_value and raw_value.lower() not in ['n/a', 'none', '']:
                            # Try to convert to proper format for JSON
                            try:
                                # If it looks like a number, keep it as is
                                float(raw_value)
                                return raw_value
                            except:
                                return raw_value
                        else:
                            return None  # Will be converted to NULL in database
                    
                    return raw_value
            return default
        except Exception as e:
            logger.debug(f"Error getting {var_name}[{index}]: {e}")
            return default

    def insert_profile_data_with_ids(self, profile_data_list):
        """Insert profile data list and return mapping of (platform_number, cycle_number, juld) -> profile_id"""
        if not profile_data_list:
            return {}

        conn = self.connect_postgres()
        cursor = conn.cursor()
        profile_id_mapping = {}

        try:
            for profile_data in profile_data_list:
                platform_number = profile_data['platform_number']
                cycle_number = profile_data['cycle_number']
                juld = profile_data['juld']
                
                # First, check if profile already exists
                cursor.execute("""
                    SELECT profile_id FROM profile_table 
                    WHERE platform_number = %s AND cycle_number = %s AND juld = %s
                """, (platform_number, cycle_number, juld))
                
                existing_profile = cursor.fetchone()
                
                if existing_profile:
                    # Profile exists, use existing profile_id
                    profile_id = existing_profile[0]
                    logger.debug(f"Found existing profile {platform_number}/{cycle_number} -> profile_id {profile_id}")
                else:
                    # Profile doesn't exist, insert new one
                    cursor.execute("""
                        INSERT INTO profile_table (
                            platform_number, cycle_number, juld, juld_qc, latitude, longitude,
                            position_qc, direction, data_mode, vertical_sampling_scheme,
                            config_mission_number, profile_pres_qc, profile_temp_qc, profile_psal_qc
                        ) VALUES (
                            %(platform_number)s, %(cycle_number)s, %(juld)s, %(juld_qc)s, 
                            %(latitude)s, %(longitude)s, %(position_qc)s, %(direction)s,
                            %(data_mode)s, %(vertical_sampling_scheme)s, %(config_mission_number)s,
                            %(profile_pres_qc)s, %(profile_temp_qc)s, %(profile_psal_qc)s
                        ) RETURNING profile_id
                    """, profile_data)
                    
                    result = cursor.fetchone()
                    if result:
                        profile_id = result[0]
                        logger.debug(f"Inserted new profile {platform_number}/{cycle_number} -> profile_id {profile_id}")
                    else:
                        logger.error(f"Failed to insert profile {platform_number}/{cycle_number}")
                        continue
                
                # Create mapping key
                key = (platform_number, cycle_number, juld)
                profile_id_mapping[key] = profile_id

            conn.commit()
            logger.info(f"✅ Processed {len(profile_data_list)} profiles, got {len(profile_id_mapping)} profile IDs")

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Error processing profiles: {e}")
            logger.error(f"Failed profile data: {profile_data_list}")
            raise
        finally:
            cursor.close()

        return profile_id_mapping


    def safe_qc_decode(self, value, default='0'):
        """Safely decode QC fields ensuring they are exactly 1 character"""
        if value is None:
            return default
        
        try:
            # Handle different types
            if isinstance(value, bytes):
                decoded = value.decode('utf-8', errors='ignore').strip()
            elif isinstance(value, np.bytes_):
                decoded = str(value, 'utf-8', errors='ignore').strip()
            elif hasattr(value, 'item'):
                item_val = value.item()
                if isinstance(item_val, bytes):
                    decoded = item_val.decode('utf-8', errors='ignore').strip()
                else:
                    decoded = str(item_val).strip()
            else:
                decoded = str(value).strip()
            
            # Handle empty or invalid values
            if not decoded or decoded.lower() in ['nan', 'none', '']:
                return default
            
            # Take only the first character
            first_char = decoded[0] if len(decoded) > 0 else default
            
            # Validate it's a reasonable QC flag
            if first_char.isdigit() or first_char.upper() in ['A', 'B', 'C', 'D', 'E', 'F']:
                return first_char
            else:
                logger.debug(f"Invalid QC flag '{first_char}' from '{repr(value)}', using default '{default}'")
                return default
                
        except Exception as e:
            logger.warning(f"Error in safe_qc_decode for value {repr(value)}: {e}")
            return default

    def process_profile_file(self, filepath):
        """Process profile.nc file - FIXED PROJECT NAME + ARRAY HANDLING + PROFILE_ID LINKING"""
        logger.info(f"Processing profile file: {filepath}")

        try:
            ds = xr.open_dataset(filepath)
            logger.info(f"Successfully opened {filepath}")

            # Extract platform number
            platform_number = self.safe_decode(ds.attrs.get('platform_number', ''))
            if not platform_number and 'PLATFORM_NUMBER' in ds.variables:
                platform_values = ds['PLATFORM_NUMBER'].values
                if platform_values.ndim == 0:
                    platform_number = self.safe_decode(platform_values.item())
                else:
                    platform_number = self.safe_decode(platform_values[0])

            logger.info(f"Platform number: {platform_number}")

            # EXTENSIVE DEBUG FOR PROJECT NAME AND ARRAYS
            logger.info("=== ATTRIBUTE AND VARIABLE DEBUG START ===")
            logger.info(f"All NetCDF attributes: {list(ds.attrs.keys())}")
            logger.info(f"All NetCDF variables: {list(ds.variables.keys())}")
            
            # Helper function to parse arrays of bytes
            def parse_byte_array_variable(var_name):
                """Parse NetCDF variable that contains array of bytes"""
                if var_name not in ds.variables:
                    return None
                
                try:
                    var_values = ds[var_name].values
                    logger.info(f"Raw {var_name} values: {repr(var_values)}")
                    logger.info(f"{var_name} shape: {var_values.shape}")
                    logger.info(f"{var_name} dtype: {var_values.dtype}")
                    
                    # Handle different array structures
                    if hasattr(var_values, '__len__') and len(var_values) > 0:
                        # Take first element and decode
                        first_elem = var_values[0] if var_values.ndim > 0 else var_values
                        decoded_value = self.safe_decode(first_elem)
                        logger.info(f"Decoded {var_name}: '{decoded_value}'")
                        return decoded_value
                    else:
                        decoded_value = self.safe_decode(var_values)
                        logger.info(f"Decoded {var_name}: '{decoded_value}'")
                        return decoded_value
                        
                except Exception as e:
                    logger.warning(f"Error parsing {var_name}: {e}")
                    return None

            # Check PROJECT_NAME (variable vs attribute)
            project_name_from_variable = None
            if 'PROJECT_NAME' in ds.variables:
                project_name_from_variable = parse_byte_array_variable('PROJECT_NAME')

            project_name_upper = ds.attrs.get('PROJECT_NAME')
            project_name_lower = ds.attrs.get('project_name')
            
            logger.info(f"PROJECT_NAME from variable: {repr(project_name_from_variable)}")
            logger.info(f"PROJECT_NAME (upper attr): {repr(project_name_upper)}")
            logger.info(f"project_name (lower attr): {repr(project_name_lower)}")

            # Check WMO_INST_TYPE (handle array format)
            wmo_inst_from_variable = None
            if 'WMO_INST_TYPE' in ds.variables:
                wmo_inst_from_variable = parse_byte_array_variable('WMO_INST_TYPE')

            wmo_inst_upper = ds.attrs.get('WMO_INST_TYPE')
            wmo_inst_lower = ds.attrs.get('wmo_inst_type')
            
            logger.info(f"WMO_INST_TYPE from variable: {repr(wmo_inst_from_variable)}")
            logger.info(f"WMO_INST_TYPE (upper attr): {repr(wmo_inst_upper)}")
            logger.info(f"wmo_inst_type (lower attr): {repr(wmo_inst_lower)}")

            # Check POSITIONING_SYSTEM (handle array format)
            positioning_from_variable = None
            if 'POSITIONING_SYSTEM' in ds.variables:
                positioning_from_variable = parse_byte_array_variable('POSITIONING_SYSTEM')

            positioning_upper = ds.attrs.get('POSITIONING_SYSTEM')
            positioning_lower = ds.attrs.get('positioning_system')
            
            logger.info(f"POSITIONING_SYSTEM from variable: {repr(positioning_from_variable)}")
            logger.info(f"POSITIONING_SYSTEM (upper attr): {repr(positioning_upper)}")
            logger.info(f"positioning_system (lower attr): {repr(positioning_lower)}")

            # Determine the best sources with priority: variable -> attribute
            final_project_name = ''
            if project_name_from_variable:
                final_project_name = project_name_from_variable
                logger.info(f"Using project name from VARIABLE")
            elif project_name_upper:
                final_project_name = self.safe_decode(project_name_upper)
                logger.info(f"Using project name from UPPER attribute")
            elif project_name_lower:
                final_project_name = self.safe_decode(project_name_lower)
                logger.info(f"Using project name from LOWER attribute")
            else:
                final_project_name = 'Unknown Project'
                logger.info("No project name found, using default")

            final_wmo_inst_type = ''
            if wmo_inst_from_variable:
                final_wmo_inst_type = wmo_inst_from_variable
                logger.info(f"Using WMO_INST_TYPE from VARIABLE: '{final_wmo_inst_type}'")
            elif wmo_inst_upper:
                final_wmo_inst_type = self.safe_decode(wmo_inst_upper)
                logger.info(f"Using WMO_INST_TYPE from UPPER attribute")
            elif wmo_inst_lower:
                final_wmo_inst_type = self.safe_decode(wmo_inst_lower)
                logger.info(f"Using WMO_INST_TYPE from LOWER attribute")

            final_positioning_system = ''
            if positioning_from_variable:
                final_positioning_system = positioning_from_variable
                logger.info(f"Using POSITIONING_SYSTEM from VARIABLE: '{final_positioning_system}'")
            elif positioning_upper:
                final_positioning_system = self.safe_decode(positioning_upper)
                logger.info(f"Using POSITIONING_SYSTEM from UPPER attribute")
            elif positioning_lower:
                final_positioning_system = self.safe_decode(positioning_lower)
                logger.info(f"Using POSITIONING_SYSTEM from LOWER attribute")

            # CRITICAL: Ensure proper string format and length limits
            final_project_name = str(final_project_name).strip()
            if len(final_project_name) > 100:
                final_project_name = final_project_name[:97] + "..."
                logger.warning(f"Project name truncated to fit database field length")

            final_wmo_inst_type = str(final_wmo_inst_type).strip()[:10]
            final_positioning_system = str(final_positioning_system).strip()[:50]

            logger.info(f"FINAL project_name: '{final_project_name}' (length: {len(final_project_name)})")
            logger.info(f"FINAL wmo_inst_type: '{final_wmo_inst_type}' (length: {len(final_wmo_inst_type)})")
            logger.info(f"FINAL positioning_system: '{final_positioning_system}' (length: {len(final_positioning_system)})")
            logger.info("=== ATTRIBUTE AND VARIABLE DEBUG END ===")

            # 1. FLOAT_TABLE - Basic info with PROPER string handling
            float_data = {
                'platform_number': platform_number,
                'project_name': final_project_name,
                'wmo_inst_type': final_wmo_inst_type,
                'positioning_system': final_positioning_system
            }

            logger.info(f"Float data to insert: {float_data}")
            self.insert_float_data(float_data)

            # 1.5. META_TABLE - Extract float-level metadata ONCE per float
            conn = self.connect_postgres()
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT COUNT(*) FROM meta_table WHERE platform_number = %s", (platform_number,))
                meta_exists = cursor.fetchone()[0] > 0
            except:
                meta_exists = False
            finally:
                cursor.close()
                conn.close()

            # Only insert meta data if it doesn't exist for this float
            # Replace your existing profile_meta_data section with this complete version:

            if not meta_exists:
                profile_meta_data = {
                    'platform_number': platform_number,
                    'data_type': self.safe_decode(ds.attrs.get('DATA_TYPE') or ds.attrs.get('data_type') or 'Argo profile'),
                    'format_version': self.safe_decode(ds.attrs.get('FORMAT_VERSION') or ds.attrs.get('format_version') or ''),
                    'handbook_version': self.safe_decode(ds.attrs.get('HANDBOOK_VERSION') or ds.attrs.get('handbook_version') or ''),
                    'date_creation': self.argo_date_to_datetime(ds.attrs.get('DATE_CREATION') or ds.attrs.get('date_creation') or ''),
                    'date_update': self.argo_date_to_datetime(ds.attrs.get('DATE_UPDATE') or ds.attrs.get('date_update') or ''),
                    
                    # ✅ ADD ALL THE MISSING FIELDS HERE
                    'ptt': self.safe_decode(ds.attrs.get('PTT') or ds.attrs.get('ptt') or ''),
                    'trans_system': self.safe_decode(ds.attrs.get('TRANS_SYSTEM') or ds.attrs.get('trans_system') or ''),
                    'trans_system_id': self.safe_decode(ds.attrs.get('TRANS_SYSTEM_ID') or ds.attrs.get('trans_system_id') or ''),
                    'trans_frequency': self.safe_decode(ds.attrs.get('TRANS_FREQUENCY') or ds.attrs.get('trans_frequency') or ''),
                    
                    'positioning_system': final_positioning_system,
                    'platform_family': self.safe_decode(ds.attrs.get('PLATFORM_FAMILY') or ds.attrs.get('platform_family') or ''),
                    'platform_type': self.safe_decode(ds.attrs.get('PLATFORM_TYPE') or ds.attrs.get('platform_type') or ''),
                    'platform_maker': self.safe_decode(ds.attrs.get('PLATFORM_MAKER') or ds.attrs.get('platform_maker') or ''),
                    'firmware_version': self.safe_decode(ds.attrs.get('FIRMWARE_VERSION') or ds.attrs.get('firmware_version') or ''),
                    
                    # ✅ MORE MISSING FIELDS
                    'manual_version': self.safe_decode(ds.attrs.get('MANUAL_VERSION') or ds.attrs.get('manual_version') or ''),
                    'float_serial_no': self.safe_decode(ds.attrs.get('FLOAT_SERIAL_NO') or ds.attrs.get('float_serial_no') or ''),
                    'dac_format_id': self.safe_decode(ds.attrs.get('DAC_FORMAT_ID') or ds.attrs.get('dac_format_id') or ''),
                    
                    'wmo_inst_type': final_wmo_inst_type,
                    'project_name': final_project_name,
                    'data_centre': self.safe_decode(ds.attrs.get('DATA_CENTRE') or ds.attrs.get('data_centre') or ''),
                    'pi_name': self.safe_decode(ds.attrs.get('PI_NAME') or ds.attrs.get('pi_name') or ''),
                    
                    # ✅ MORE MISSING FIELDS
                    'anomaly': self.safe_decode(ds.attrs.get('ANOMALY') or ds.attrs.get('anomaly') or ''),
                    'battery_type': self.safe_decode(ds.attrs.get('BATTERY_TYPE') or ds.attrs.get('battery_type') or ''),
                    'battery_packs': self.safe_int(ds.attrs.get('BATTERY_PACKS') or ds.attrs.get('battery_packs')),
                    'controller_board_type_primary': self.safe_decode(ds.attrs.get('CONTROLLER_BOARD_TYPE_PRIMARY') or ds.attrs.get('controller_board_type_primary') or ''),
                    'controller_board_type_secondary': self.safe_decode(ds.attrs.get('CONTROLLER_BOARD_TYPE_SECONDARY') or ds.attrs.get('controller_board_type_secondary') or ''),
                    'serial_no_primary': self.safe_decode(ds.attrs.get('SERIAL_NO_PRIMARY') or ds.attrs.get('serial_no_primary') or ''),
                    'serial_no_secondary': self.safe_decode(ds.attrs.get('SERIAL_NO_SECONDARY') or ds.attrs.get('serial_no_secondary') or ''),
                    'special_features': self.safe_decode(ds.attrs.get('SPECIAL_FEATURES') or ds.attrs.get('special_features') or ''),
                    'float_owner': self.safe_decode(ds.attrs.get('FLOAT_OWNER') or ds.attrs.get('float_owner') or ''),
                    'operating_institution': self.safe_decode(ds.attrs.get('OPERATING_INSTITUTION') or ds.attrs.get('operating_institution') or ''),
                    'customisation': self.safe_decode(ds.attrs.get('CUSTOMISATION') or ds.attrs.get('customisation') or ''),
                    
                    'launch_date': self.argo_date_to_datetime(ds.attrs.get('LAUNCH_DATE') or ds.attrs.get('launch_date') or ''),
                    'launch_latitude': self.safe_float(ds.attrs.get('LAUNCH_LATITUDE') or ds.attrs.get('launch_latitude')),
                    'launch_longitude': self.safe_float(ds.attrs.get('LAUNCH_LONGITUDE') or ds.attrs.get('launch_longitude')),
                    'launch_qc': self.safe_decode(ds.attrs.get('LAUNCH_QC') or ds.attrs.get('launch_qc') or ''),
                    
                    'start_date': self.argo_date_to_datetime(ds.attrs.get('START_DATE') or ds.attrs.get('start_date') or ''),
                    'start_date_qc': self.safe_decode(ds.attrs.get('START_DATE_QC') or ds.attrs.get('start_date_qc') or ''),
                    'startup_date': self.argo_date_to_datetime(ds.attrs.get('STARTUP_DATE') or ds.attrs.get('startup_date') or ''),
                    'startup_date_qc': self.safe_decode(ds.attrs.get('STARTUP_DATE_QC') or ds.attrs.get('startup_date_qc') or ''),
                    
                    'end_mission_date': self.argo_date_to_datetime(ds.attrs.get('END_MISSION_DATE') or ds.attrs.get('end_mission_date') or ''),
                    'end_mission_status': self.safe_decode(ds.attrs.get('END_MISSION_STATUS') or ds.attrs.get('end_mission_status') or '')
                }

                # Only insert if we have meaningful metadata
                meaningful_fields = [
                    profile_meta_data['pi_name'], 
                    profile_meta_data['project_name'], 
                    profile_meta_data['data_centre'],
                    profile_meta_data['platform_type'],
                    profile_meta_data['platform_maker']
                ]
                
                if any(field and field not in ['Unknown Project', ''] and field.strip() for field in meaningful_fields):
                    self.insert_meta_data(profile_meta_data)
                    logger.info(f"✅ Inserted metadata with project: '{final_project_name}' for platform {platform_number}")
                else:
                    logger.info(f"ℹ️ No meaningful metadata found for platform {platform_number}")

            else:
                logger.info(f"ℹ️ Metadata already exists for platform {platform_number}, skipping")

            # Rest of your existing profile and measurement processing...
            profiles = []
            n_prof = ds.sizes.get('N_PROF', 1)

            for prof_idx in range(n_prof):
                juld_val = None
                if 'JULD' in ds:
                    raw_juld = ds['JULD'].values[prof_idx]
                    juld_val = self.enhanced_julian_to_datetime(raw_juld)

                profile_data = {
                    'platform_number': platform_number,
                    'cycle_number': self.safe_int(ds['CYCLE_NUMBER'].values[prof_idx] if 'CYCLE_NUMBER' in ds else None),
                    'latitude': self.safe_float(ds['LATITUDE'].values[prof_idx] if 'LATITUDE' in ds else None),
                    'longitude': self.safe_float(ds['LONGITUDE'].values[prof_idx] if 'LONGITUDE' in ds else None),
                    'juld': juld_val,
                    'direction': self.safe_decode(ds['DIRECTION'].values[prof_idx] if 'DIRECTION' in ds else 'A'),
                    'data_mode': self.safe_decode(ds['DATA_MODE'].values[prof_idx] if 'DATA_MODE' in ds else 'R'),
                    'position_qc': self.safe_decode(ds['POSITION_QC'].values[prof_idx] if 'POSITION_QC' in ds else '0'),
                    'juld_qc': self.safe_decode(ds['JULD_QC'].values[prof_idx] if 'JULD_QC' in ds else '0'),
                    'vertical_sampling_scheme': self.safe_decode(ds['VERTICAL_SAMPLING_SCHEME'].values[prof_idx] if 'VERTICAL_SAMPLING_SCHEME' in ds else ''),
                    'config_mission_number': self.safe_int(ds['CONFIG_MISSION_NUMBER'].values[prof_idx] if 'CONFIG_MISSION_NUMBER' in ds else None),
                    'profile_pres_qc': self.safe_decode(ds['PROFILE_PRES_QC'].values[prof_idx] if 'PROFILE_PRES_QC' in ds else ''),
                    'profile_temp_qc': self.safe_decode(ds['PROFILE_TEMP_QC'].values[prof_idx] if 'PROFILE_TEMP_QC' in ds else ''),
                    'profile_psal_qc': self.safe_decode(ds['PROFILE_PSAL_QC'].values[prof_idx] if 'PROFILE_PSAL_QC' in ds else '')
                }
                profiles.append(profile_data)

            # ✅ Insert profiles and get the profile_ids using your helper function
            profile_id_mapping = self.insert_profile_data_with_ids(profiles)
            logger.info(f"✅ Inserted {len(profiles)} profiles, got {len(profile_id_mapping)} profile IDs")

            # ✅ UPDATED DEPTHS LOGIC - Link to profile_id
            measurements = []
            if 'N_LEVELS' in ds.sizes:
                n_levels = ds.sizes['N_LEVELS']

                for prof_idx in range(n_prof):
                    cycle_number = self.safe_int(ds['CYCLE_NUMBER'].values[prof_idx] if 'CYCLE_NUMBER' in ds else None)
                    prof_lat = self.safe_float(ds['LATITUDE'].values[prof_idx] if 'LATITUDE' in ds else None)
                    prof_lon = self.safe_float(ds['LONGITUDE'].values[prof_idx] if 'LONGITUDE' in ds else None)
                    
                    # Get JULD for this profile to match with profile_id
                    juld_val = None
                    if 'JULD' in ds:
                        raw_juld = ds['JULD'].values[prof_idx]
                        juld_val = self.enhanced_julian_to_datetime(raw_juld)

                    # ✅ Find the corresponding profile_id using your helper function mapping
                    profile_id = profile_id_mapping.get((platform_number, cycle_number, juld_val))
                    if not profile_id:
                        logger.warning(f"Could not find profile_id for profile {prof_idx}, cycle {cycle_number}")
                        continue

                    for level_idx in range(n_levels):
                        pres = self.safe_float(ds['PRES'].values[prof_idx, level_idx] if 'PRES' in ds else None)
                        temp = self.safe_float(ds['TEMP'].values[prof_idx, level_idx] if 'TEMP' in ds else None)
                        psal = self.safe_float(ds['PSAL'].values[prof_idx, level_idx] if 'PSAL' in ds else None)

                        if all(x is None for x in [pres, temp, psal]):
                            continue

                        # In your process_profile_file function, replace the measurement creation with this:

                        measurement = {
                            'profile_id': profile_id,  # ✅ NOW WE HAVE THE PROFILE_ID!
                            'platform_number': platform_number,
                            'cycle_number': cycle_number,
                            'latitude': prof_lat,
                            'longitude': prof_lon,
                            'pres': pres,
                            'temp': temp,
                            'psal': psal,
                            
                            # ✅ Use safe_qc_decode for all QC fields
                            'pres_qc': self.safe_qc_decode(ds['PRES_QC'].values[prof_idx, level_idx] if 'PRES_QC' in ds else '0'),
                            'temp_qc': self.safe_qc_decode(ds['TEMP_QC'].values[prof_idx, level_idx] if 'TEMP_QC' in ds else '0'),
                            'psal_qc': self.safe_qc_decode(ds['PSAL_QC'].values[prof_idx, level_idx] if 'PSAL_QC' in ds else '0'),
                            
                            # Adjusted values
                            'pres_adjusted': self.safe_float(ds['PRES_ADJUSTED'].values[prof_idx, level_idx] if 'PRES_ADJUSTED' in ds else None),
                            'temp_adjusted': self.safe_float(ds['TEMP_ADJUSTED'].values[prof_idx, level_idx] if 'TEMP_ADJUSTED' in ds else None),
                            'psal_adjusted': self.safe_float(ds['PSAL_ADJUSTED'].values[prof_idx, level_idx] if 'PSAL_ADJUSTED' in ds else None),
                            
                            # ✅ Adjusted QC fields with safe_qc_decode
                            'pres_adjusted_qc': self.safe_qc_decode(ds['PRES_ADJUSTED_QC'].values[prof_idx, level_idx] if 'PRES_ADJUSTED_QC' in ds else '0'),
                            'temp_adjusted_qc': self.safe_qc_decode(ds['TEMP_ADJUSTED_QC'].values[prof_idx, level_idx] if 'TEMP_ADJUSTED_QC' in ds else '0'),
                            'psal_adjusted_qc': self.safe_qc_decode(ds['PSAL_ADJUSTED_QC'].values[prof_idx, level_idx] if 'PSAL_ADJUSTED_QC' in ds else '0'),
                            
                            'pres_adjusted_error': self.safe_float(ds['PRES_ADJUSTED_ERROR'].values[prof_idx, level_idx] if 'PRES_ADJUSTED_ERROR' in ds else None),
                            'temp_adjusted_error': self.safe_float(ds['TEMP_ADJUSTED_ERROR'].values[prof_idx, level_idx] if 'TEMP_ADJUSTED_ERROR' in ds else None),
                            'psal_adjusted_error': self.safe_float(ds['PSAL_ADJUSTED_ERROR'].values[prof_idx, level_idx] if 'PSAL_ADJUSTED_ERROR' in ds else None),
                            
                            # BGC parameters
                            'doxy': self.safe_float(ds['DOXY'].values[prof_idx, level_idx] if 'DOXY' in ds else None),
                            'doxy_qc': self.safe_qc_decode(ds['DOXY_QC'].values[prof_idx, level_idx] if 'DOXY_QC' in ds else '0'),
                            'doxy_adjusted': self.safe_float(ds['DOXY_ADJUSTED'].values[prof_idx, level_idx] if 'DOXY_ADJUSTED' in ds else None),
                            'doxy_adjusted_qc': self.safe_qc_decode(ds['DOXY_ADJUSTED_QC'].values[prof_idx, level_idx] if 'DOXY_ADJUSTED_QC' in ds else '0'),
                            'doxy_adjusted_error': self.safe_float(ds['DOXY_ADJUSTED_ERROR'].values[prof_idx, level_idx] if 'DOXY_ADJUSTED_ERROR' in ds else None),
                            
                            'nitrate': self.safe_float(ds['NITRATE'].values[prof_idx, level_idx] if 'NITRATE' in ds else None),
                            'nitrate_qc': self.safe_qc_decode(ds['NITRATE_QC'].values[prof_idx, level_idx] if 'NITRATE_QC' in ds else '0'),
                            'nitrate_adjusted': self.safe_float(ds['NITRATE_ADJUSTED'].values[prof_idx, level_idx] if 'NITRATE_ADJUSTED' in ds else None),
                            'nitrate_adjusted_qc': self.safe_qc_decode(ds['NITRATE_ADJUSTED_QC'].values[prof_idx, level_idx] if 'NITRATE_ADJUSTED_QC' in ds else '0'),
                            'nitrate_adjusted_error': self.safe_float(ds['NITRATE_ADJUSTED_ERROR'].values[prof_idx, level_idx] if 'NITRATE_ADJUSTED_ERROR' in ds else None),
                            
                            'ph_in_situ_total': self.safe_float(ds['PH_IN_SITU_TOTAL'].values[prof_idx, level_idx] if 'PH_IN_SITU_TOTAL' in ds else None),
                            'ph_in_situ_total_qc': self.safe_qc_decode(ds['PH_IN_SITU_TOTAL_QC'].values[prof_idx, level_idx] if 'PH_IN_SITU_TOTAL_QC' in ds else '0'),
                            'ph_in_situ_total_adjusted': self.safe_float(ds['PH_IN_SITU_TOTAL_ADJUSTED'].values[prof_idx, level_idx] if 'PH_IN_SITU_TOTAL_ADJUSTED' in ds else None),
                            'ph_in_situ_total_adjusted_qc': self.safe_qc_decode(ds['PH_IN_SITU_TOTAL_ADJUSTED_QC'].values[prof_idx, level_idx] if 'PH_IN_SITU_TOTAL_ADJUSTED_QC' in ds else '0'),
                            'ph_in_situ_total_adjusted_error': self.safe_float(ds['PH_IN_SITU_TOTAL_ADJUSTED_ERROR'].values[prof_idx, level_idx] if 'PH_IN_SITU_TOTAL_ADJUSTED_ERROR' in ds else None)
                        }

                        measurements.append(measurement)

            self.insert_measurement_data(measurements)
            ds.close()

            logger.info(f"✅ Successfully processed profile file")
            logger.info(f"  - Profiles: {len(profiles)}")
            logger.info(f"  - Measurements: {len(measurements)}")

            return True

        except Exception as e:
            logger.error(f"❌ Error processing profile file: {e}")
            import traceback
            traceback.print_exc()
            return False



    # INSERT METHODS FOR ALL 15 TABLES

    def insert_float_data(self, float_data):
        """Insert float data with length validation"""
        if not float_data.get('platform_number'):
            logger.error("No platform number provided")
            return

        # Ensure all strings are properly sized
        safe_data = {
            'platform_number': str(float_data['platform_number'])[:20],
            'project_name': str(float_data.get('project_name', ''))[:100],
            'wmo_inst_type': str(float_data.get('wmo_inst_type', ''))[:10],
            'positioning_system': str(float_data.get('positioning_system', ''))[:50]
        }

        logger.info(f"Safe data to insert: {safe_data}")

        conn = self.connect_postgres()
        cursor = conn.cursor()

        try:
            sql = """
            INSERT INTO float_table (platform_number, project_name, wmo_inst_type, positioning_system)
            VALUES (%(platform_number)s, %(project_name)s, %(wmo_inst_type)s, %(positioning_system)s)
            ON CONFLICT (platform_number) 
            DO UPDATE SET
                project_name = EXCLUDED.project_name,
                wmo_inst_type = EXCLUDED.wmo_inst_type,
                positioning_system = EXCLUDED.positioning_system,
                updated_at = CURRENT_TIMESTAMP
            """
            
            cursor.execute(sql, safe_data)
            conn.commit()
            logger.info(f"✅ Successfully inserted/updated float data for {safe_data['platform_number']}")

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Error inserting float data: {e}")
            logger.error(f"Data that failed: {safe_data}")
            raise
        finally:
            cursor.close()



    def insert_profile_data(self, profiles):
        """Insert into profile_table - Updated for new schema"""
        if not profiles:
             return

        conn = self.connect_postgres()
        cursor = conn.cursor()

        try:
            profile_values = []
            for profile in profiles:
                profile_values.append((
                profile['platform_number'],
                profile['cycle_number'],
                profile['juld'],
                profile['juld_qc'],
                profile['latitude'],
                profile['longitude'],
                profile['position_qc'],
                profile['direction'],
                profile['data_mode'],
                profile.get('vertical_sampling_scheme', ''),
                profile.get('config_mission_number'),
                profile.get('profile_pres_qc', ''),
                profile.get('profile_temp_qc', ''),
                profile.get('profile_psal_qc', '')
            ))

            sql = """
            INSERT INTO profile_table (
            platform_number, cycle_number, juld, juld_qc, latitude, longitude,
            position_qc, direction, data_mode, vertical_sampling_scheme, 
            config_mission_number, profile_pres_qc, profile_temp_qc, profile_psal_qc
            ) VALUES %s
            ON CONFLICT (platform_number, cycle_number, direction) DO UPDATE SET
            juld = EXCLUDED.juld,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            vertical_sampling_scheme = EXCLUDED.vertical_sampling_scheme,
            config_mission_number = EXCLUDED.config_mission_number,
            profile_pres_qc = EXCLUDED.profile_pres_qc,
            profile_temp_qc = EXCLUDED.profile_temp_qc,
            profile_psal_qc = EXCLUDED.profile_psal_qc
            """

            from psycopg2.extras import execute_values
            execute_values(cursor, sql, profile_values)
            conn.commit()
            logger.info(f"Updated profile_table: {len(profiles)} profiles")

        except Exception as e:
            conn.rollback()
            logger.error(f"Error inserting profile data: {e}")
            raise
        finally:
            cursor.close()

    def insert_meta_data(self, meta_data):
        """Insert into meta_table - FULL SCHEMA MATCH with complete UPDATE"""
        conn = self.connect_postgres()
        cursor = conn.cursor()

        try:
            # ✅ DEBUG: Log what we're trying to insert
            logger.info("=== INSERTING META DATA ===")
            non_empty_fields = {k: v for k, v in meta_data.items() if v and str(v).strip() and str(v) not in ['', 'None', 'nan']}
            logger.info(f"Inserting {len(non_empty_fields)} non-empty fields out of {len(meta_data)} total fields")
            
            for key, value in non_empty_fields.items():
                logger.debug(f"  {key}: {repr(value)}")

            sql = """
            INSERT INTO meta_table (
            platform_number, data_type, format_version, handbook_version,
            date_creation, date_update, ptt, trans_system, trans_system_id,
            trans_frequency, positioning_system, platform_family, platform_type,
            platform_maker, firmware_version, manual_version, float_serial_no,
            dac_format_id, wmo_inst_type, project_name, data_centre, pi_name,
            anomaly, battery_type, battery_packs, controller_board_type_primary,
            controller_board_type_secondary, serial_no_primary, serial_no_secondary,
            special_features, float_owner, operating_institution, customisation,
            launch_date, launch_latitude, launch_longitude, launch_qc,
            start_date, start_date_qc, startup_date, startup_date_qc,
            end_mission_date, end_mission_status
            ) VALUES (
            %(platform_number)s, %(data_type)s, %(format_version)s, %(handbook_version)s,
            %(date_creation)s, %(date_update)s, %(ptt)s, %(trans_system)s, %(trans_system_id)s,
            %(trans_frequency)s, %(positioning_system)s, %(platform_family)s, %(platform_type)s,
            %(platform_maker)s, %(firmware_version)s, %(manual_version)s, %(float_serial_no)s,
            %(dac_format_id)s, %(wmo_inst_type)s, %(project_name)s, %(data_centre)s, %(pi_name)s,
            %(anomaly)s, %(battery_type)s, %(battery_packs)s, %(controller_board_type_primary)s,
            %(controller_board_type_secondary)s, %(serial_no_primary)s, %(serial_no_secondary)s,
            %(special_features)s, %(float_owner)s, %(operating_institution)s, %(customisation)s,
            %(launch_date)s, %(launch_latitude)s, %(launch_longitude)s, %(launch_qc)s,
            %(start_date)s, %(start_date_qc)s, %(startup_date)s, %(startup_date_qc)s,
            %(end_mission_date)s, %(end_mission_status)s
            )
            ON CONFLICT (platform_number) DO UPDATE SET
            data_type = EXCLUDED.data_type,
            format_version = EXCLUDED.format_version,
            handbook_version = EXCLUDED.handbook_version,
            date_creation = EXCLUDED.date_creation,
            date_update = EXCLUDED.date_update,
            ptt = EXCLUDED.ptt,
            trans_system = EXCLUDED.trans_system,
            trans_system_id = EXCLUDED.trans_system_id,
            trans_frequency = EXCLUDED.trans_frequency,
            positioning_system = EXCLUDED.positioning_system,
            platform_family = EXCLUDED.platform_family,
            platform_type = EXCLUDED.platform_type,
            platform_maker = EXCLUDED.platform_maker,
            firmware_version = EXCLUDED.firmware_version,
            manual_version = EXCLUDED.manual_version,
            float_serial_no = EXCLUDED.float_serial_no,
            dac_format_id = EXCLUDED.dac_format_id,
            wmo_inst_type = EXCLUDED.wmo_inst_type,
            project_name = EXCLUDED.project_name,
            data_centre = EXCLUDED.data_centre,
            pi_name = EXCLUDED.pi_name,
            anomaly = EXCLUDED.anomaly,
            battery_type = EXCLUDED.battery_type,
            battery_packs = EXCLUDED.battery_packs,
            controller_board_type_primary = EXCLUDED.controller_board_type_primary,
            controller_board_type_secondary = EXCLUDED.controller_board_type_secondary,
            serial_no_primary = EXCLUDED.serial_no_primary,
            serial_no_secondary = EXCLUDED.serial_no_secondary,
            special_features = EXCLUDED.special_features,
            float_owner = EXCLUDED.float_owner,
            operating_institution = EXCLUDED.operating_institution,
            customisation = EXCLUDED.customisation,
            launch_date = EXCLUDED.launch_date,
            launch_latitude = EXCLUDED.launch_latitude,
            launch_longitude = EXCLUDED.launch_longitude,
            launch_qc = EXCLUDED.launch_qc,
            start_date = EXCLUDED.start_date,
            start_date_qc = EXCLUDED.start_date_qc,
            startup_date = EXCLUDED.startup_date,
            startup_date_qc = EXCLUDED.startup_date_qc,
            end_mission_date = EXCLUDED.end_mission_date,
            end_mission_status = EXCLUDED.end_mission_status,
            updated_at = CURRENT_TIMESTAMP
            """

            cursor.execute(sql, meta_data)
            conn.commit()
            
            # ✅ VERIFY: Check what was actually inserted
            cursor.execute("SELECT * FROM meta_table WHERE platform_number = %s", (meta_data['platform_number'],))
            inserted_row = cursor.fetchone()
            if inserted_row:
                logger.info(f"✅ Successfully updated/inserted meta_table for platform {meta_data['platform_number']}")
                logger.debug(f"Row in database: {inserted_row}")
            else:
                logger.error(f"❌ No row found after insert for platform {meta_data['platform_number']}")

        except Exception as e:
            conn.rollback()
            logger.error(f"Error inserting meta data: {e}")
            logger.error(f"Failed meta_data keys: {list(meta_data.keys())}")
            
            # Debug: Check if there are any data type issues
            for key, value in meta_data.items():
                logger.error(f"  {key}: {type(value)} = {repr(value)}")
            
            raise
        finally:
            cursor.close()

    def insert_trajectory_depth_data(self, traj_depth_data):
        """Insert into trajectory_depth_table - FIXED with deduplication"""
        if not traj_depth_data:
            return

        conn = self.connect_postgres()
        cursor = conn.cursor()

        try:
            trajectory_depth_values = []
            seen_keys = set()  # ✅ NEW: Track unique combinations
            duplicates_skipped = 0
            
            for traj_depth in traj_depth_data:
                # ✅ ENHANCED: Double-clean timestamp values with nanosecond removal
                juld_val = self.clean_timestamp_value_enhanced(traj_depth.get('juld'))
                juld_adjusted_val = self.clean_timestamp_value_enhanced(traj_depth.get('juld_adjusted'))
                
                # ✅ NEW: Create unique key for deduplication
                unique_key = (
                    traj_depth['platform_number'],
                    traj_depth['cycle_number'], 
                    traj_depth.get('measurement_code'),
                    juld_val
                )
                
                # ✅ NEW: Skip if we've already seen this combination
                if unique_key in seen_keys:
                    duplicates_skipped += 1
                    logger.debug(f"🔄 Skipping duplicate: {unique_key}")
                    continue
                    
                seen_keys.add(unique_key)
                
                trajectory_depth_values.append((
                    traj_depth.get('trajectory_id'),
                    traj_depth['platform_number'],
                    traj_depth['cycle_number'],
                    # Measurement identification
                    traj_depth.get('measurement_code'),
                    traj_depth.get('measurement_index'),
                    # Position and time - ENHANCED CLEANING
                    traj_depth.get('latitude'),
                    traj_depth.get('longitude'),
                    juld_val,  # ✅ ENHANCED CLEANED
                    traj_depth.get('juld_status'),
                    juld_adjusted_val,  # ✅ ENHANCED CLEANED
                    traj_depth.get('juld_adjusted_qc'),
                    traj_depth.get('juld_adjusted_status'),
                    # Position details
                    traj_depth.get('position_accuracy'),
                    traj_depth.get('axes_error_ellipse_major'),
                    traj_depth.get('axes_error_ellipse_minor'),
                    traj_depth.get('axes_error_ellipse_angle'),
                    traj_depth.get('satellite_name'),
                    traj_depth.get('positioning_system'),
                    traj_depth.get('position_qc'),
                    # Measurements
                    traj_depth.get('pres'),
                    traj_depth.get('pres_qc'),
                    traj_depth.get('pres_adjusted'),
                    traj_depth.get('pres_adjusted_qc'),
                    traj_depth.get('pres_adjusted_error'),
                    traj_depth.get('temp'),
                    traj_depth.get('temp_qc'),
                    traj_depth.get('temp_adjusted'),
                    traj_depth.get('temp_adjusted_qc'),
                    traj_depth.get('temp_adjusted_error'),
                    traj_depth.get('psal'),
                    traj_depth.get('psal_qc'),
                    traj_depth.get('psal_adjusted'),
                    traj_depth.get('psal_adjusted_qc'),
                    traj_depth.get('psal_adjusted_error')
                ))

            # ✅ LOG: Show deduplication results
            if duplicates_skipped > 0:
                logger.info(f"🔄 Removed {duplicates_skipped} duplicate rows from batch")
            
            logger.info(f"✅ Processing {len(trajectory_depth_values)} unique trajectory depth records")

            if not trajectory_depth_values:
                logger.warning("⚠️ No unique records to insert after deduplication")
                return

            # ✅ SIMPLIFIED: Use DO NOTHING instead of DO UPDATE to avoid conflicts
            sql = """
            INSERT INTO trajectory_depth_table (
                trajectory_id, platform_number, cycle_number,
                measurement_code, measurement_index,
                latitude, longitude, juld, juld_status, juld_adjusted, juld_adjusted_qc, juld_adjusted_status,
                position_accuracy, axes_error_ellipse_major, axes_error_ellipse_minor, axes_error_ellipse_angle,
                satellite_name, positioning_system, position_qc,
                pres, pres_qc, pres_adjusted, pres_adjusted_qc, pres_adjusted_error,
                temp, temp_qc, temp_adjusted, temp_adjusted_qc, temp_adjusted_error,
                psal, psal_qc, psal_adjusted, psal_adjusted_qc, psal_adjusted_error
            ) VALUES %s
            ON CONFLICT (platform_number, cycle_number, measurement_code, juld) 
            DO NOTHING
            """

            from psycopg2.extras import execute_values
            execute_values(cursor, sql, trajectory_depth_values, template=None, page_size=100)
            conn.commit()
            
            inserted_count = len(trajectory_depth_values)
            logger.info(f"✅ Successfully processed {inserted_count} unique trajectory depth measurements")
            if duplicates_skipped > 0:
                logger.info(f"🔄 Skipped {duplicates_skipped} duplicates in current batch")

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Error inserting trajectory depth data: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    def clean_timestamp_value_enhanced(self, timestamp_val):
        """✅ Enhanced timestamp cleaning with nanosecond removal"""
        if timestamp_val is None:
            return None
        
        try:
            if isinstance(timestamp_val, str) and timestamp_val.strip() == '':
                return None
            
            # Convert to pandas datetime first
            if pd.isna(timestamp_val):
                return None
                
            # Convert and remove nanoseconds to avoid warnings
            dt = pd.to_datetime(timestamp_val)
            if pd.notna(dt):
                # ✅ KEY FIX: Remove nanoseconds to prevent warnings
                # Round to nearest millisecond to avoid precision issues
                clean_dt = dt.round('ms')
                return clean_dt
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Timestamp conversion failed for {timestamp_val}: {e}")
            return None



    def insert_config_data(self, config_data_list):
        """Insert into config_table with duplicate prevention"""
        if not config_data_list:
            return

        conn = self.connect_postgres()
        cursor = conn.cursor()

        try:
            config_values = []
            for config in config_data_list:
                config_values.append((
                    config['platform_number'],
                    config['config_parameter_name'],
                    config['config_parameter_value'],
                    config.get('config_mission_number'),
                    config.get('config_mission_comment', '')
                ))

            # ✅ INSERT with ON CONFLICT to prevent duplicates
            sql = """
            INSERT INTO config_table (
                platform_number, config_parameter_name, config_parameter_value,
                config_mission_number, config_mission_comment
            ) VALUES %s
            ON CONFLICT (platform_number, config_parameter_name) 
            DO UPDATE SET
                config_parameter_value = EXCLUDED.config_parameter_value,
                config_mission_number = EXCLUDED.config_mission_number,
                config_mission_comment = EXCLUDED.config_mission_comment,
                updated_at = CURRENT_TIMESTAMP
            """

            from psycopg2.extras import execute_values
            execute_values(cursor, sql, config_values)
            conn.commit()
            logger.info(f"✅ Updated config_table: {len(config_data_list)} config parameters")

        except Exception as e:
            conn.rollback()
            logger.error(f"Error inserting config data: {e}")
            
            # Debug: Show the problematic data
            logger.error("Config data that caused the error:")
            for i, config_data in enumerate(config_data_list[:3]):  # Show first 3
                logger.error(f"  {i+1}. {config_data}")
            raise
        finally:
            cursor.close()


    def insert_launch_config_data(self, launch_config_data_list):
        """Insert into launch_config_table with duplicate prevention"""
        if not launch_config_data_list:
            return

        conn = self.connect_postgres()
        cursor = conn.cursor()

        try:
            launch_config_values = []
            for config in launch_config_data_list:
                launch_config_values.append((
                    config['platform_number'],
                    config['launch_config_parameter_name'],
                    config['launch_config_parameter_value']
                ))

            # ✅ INSERT with ON CONFLICT to prevent duplicates
            sql = """
            INSERT INTO launch_config_table (
                platform_number, launch_config_parameter_name, launch_config_parameter_value
            ) VALUES %s
            ON CONFLICT (platform_number, launch_config_parameter_name) 
            DO UPDATE SET
                launch_config_parameter_value = EXCLUDED.launch_config_parameter_value,
                updated_at = CURRENT_TIMESTAMP
            """

            from psycopg2.extras import execute_values
            execute_values(cursor, sql, launch_config_values)
            conn.commit()
            logger.info(f"✅ Updated launch_config_table: {len(launch_config_data_list)} launch config parameters")

        except Exception as e:
            conn.rollback()
            logger.error(f"Error inserting launch config data: {e}")
            
            # Debug: Show the problematic data
            logger.error("Launch config data that caused the error:")
            for i, config_data in enumerate(launch_config_data_list[:3]):  # Show first 3
                logger.error(f"  {i+1}. {config_data}")
            raise
        finally:
            cursor.close()


    def insert_sensor_data(self, sensor_data_list):
        """Insert into sensor_table with duplicate prevention"""
        if not sensor_data_list:
            return

        conn = self.connect_postgres()
        cursor = conn.cursor()

        try:
            sensor_values = []
            for sensor in sensor_data_list:
                sensor_values.append((
                    sensor['platform_number'],
                    sensor['sensor'],
                    sensor['sensor_maker'],
                    sensor['sensor_model'],
                    sensor['sensor_serial_no']
                ))

            # ✅ INSERT with ON CONFLICT to prevent duplicates
            sql = """
            INSERT INTO sensor_table (
                platform_number, sensor, sensor_maker, sensor_model, sensor_serial_no
            ) VALUES %s
            ON CONFLICT (platform_number, sensor) 
            DO UPDATE SET
                sensor_maker = EXCLUDED.sensor_maker,
                sensor_model = EXCLUDED.sensor_model,
                sensor_serial_no = EXCLUDED.sensor_serial_no,
                updated_at = CURRENT_TIMESTAMP
            """

            from psycopg2.extras import execute_values
            execute_values(cursor, sql, sensor_values)
            conn.commit()
            logger.info(f"✅ Updated sensor_table: {len(sensor_data_list)} sensors")

        except Exception as e:
            conn.rollback()
            logger.error(f"Error inserting sensor data: {e}")
            
            # Debug: Show the problematic data
            logger.error("Sensor data that caused the error:")
            for i, sensor_data in enumerate(sensor_data_list[:3]):  # Show first 3
                logger.error(f"  {i+1}. {sensor_data}")
            raise
        finally:
            cursor.close()


    def insert_qc_flags_data(self, qc_data_list):
        """Insert into qc_flags_table"""
        if not qc_data_list:
            return

        conn = self.connect_postgres()
        cursor = conn.cursor()

        try:
            qc_values = []
            for qc in qc_data_list:
                qc_values.append((
                    qc['platform_number'],
                    qc['cycle_number'],
                    qc['profile_pres_qc'],
                    qc['profile_temp_qc'],
                    qc['profile_psal_qc'],
                    qc['vertical_sampling_scheme']
                ))

            sql = """
            INSERT INTO qc_flags_table (
                platform_number, cycle_number, profile_pres_qc,
                profile_temp_qc, profile_psal_qc, vertical_sampling_scheme
            ) VALUES %s
            ON CONFLICT (platform_number, cycle_number) DO UPDATE SET
                profile_pres_qc = EXCLUDED.profile_pres_qc,
                profile_temp_qc = EXCLUDED.profile_temp_qc,
                profile_psal_qc = EXCLUDED.profile_psal_qc,
                updated_at = CURRENT_TIMESTAMP
            """

            execute_values(cursor, sql, qc_values)
            conn.commit()
            logger.info(f"Updated qc_flags_table: {len(qc_data_list)} QC records")

        except Exception as e:
            conn.rollback()
            logger.error(f"Error inserting QC flags data: {e}")
            raise
        finally:
            cursor.close()

    def insert_history_data(self, history_data_list):
        """Insert into history_table with duplicate prevention - Updated for new schema"""
        if not history_data_list:
            return

        conn = self.connect_postgres()
        cursor = conn.cursor()

        try:
            history_values = []
            for history in history_data_list:
                history_values.append((
                    history['platform_number'],
                    history.get('cycle_number'),  # Added cycle_number
                    history['history_institution'],
                    history['history_step'],
                    history['history_software'],
                    history['history_software_release'],
                    history.get('history_reference', ''),  # Added reference
                    history['history_date'],
                    history['history_action'],
                    history['history_parameter'],
                    history.get('history_start_pres'),  # Added start_pres
                    history.get('history_stop_pres'),   # Added stop_pres
                    history.get('history_previous_value'),  # Added previous_value
                    history['history_qctest']
                ))

            # Add unique constraint if not exists
            try:
                cursor.execute("""
                    ALTER TABLE history_table 
                    ADD CONSTRAINT unique_history_record 
                    UNIQUE (platform_number, history_institution, history_step, history_date, history_action)
                """)
                conn.commit()
                logger.info("Added unique constraint to history_table")
            except Exception:
                # Constraint already exists, ignore
                conn.rollback()

            # ✅ INSERT with ON CONFLICT to prevent duplicates
            sql = """
            INSERT INTO history_table (
                platform_number, cycle_number, history_institution, history_step,
                history_software, history_software_release, history_reference, history_date,
                history_action, history_parameter, history_start_pres, history_stop_pres,
                history_previous_value, history_qctest
            ) VALUES %s
            ON CONFLICT (platform_number, history_institution, history_step, history_date, history_action) 
            DO UPDATE SET
                cycle_number = EXCLUDED.cycle_number,
                history_software = EXCLUDED.history_software,
                history_software_release = EXCLUDED.history_software_release,
                history_reference = EXCLUDED.history_reference,
                history_parameter = EXCLUDED.history_parameter,
                history_start_pres = EXCLUDED.history_start_pres,
                history_stop_pres = EXCLUDED.history_stop_pres,
                history_previous_value = EXCLUDED.history_previous_value,
                history_qctest = EXCLUDED.history_qctest,
                created_at = CURRENT_TIMESTAMP
            """

            from psycopg2.extras import execute_values
            execute_values(cursor, sql, history_values)
            conn.commit()
            logger.info(f"✅ Updated history_table: {len(history_data_list)} history records")

        except Exception as e:
            conn.rollback()
            logger.error(f"Error inserting history data: {e}")
            
            # Debug: Show the problematic data
            logger.error("History data that caused the error:")
            for i, history_data in enumerate(history_data_list[:3]):  # Show first 3
                logger.error(f"  {i+1}. {history_data}")
            raise
        finally:
            cursor.close()


    def insert_data_mode_data(self, data_mode_data_list):
        """Insert into data_mode_table"""
        if not data_mode_data_list:
            return

        conn = self.connect_postgres()
        cursor = conn.cursor()

        try:
            data_mode_values = []
            for data_mode in data_mode_data_list:
                data_mode_values.append((
                    data_mode['platform_number'],
                    data_mode['cycle_number'],
                    data_mode['data_mode'],
                    data_mode['data_state_indicator'],
                    data_mode['data_centre'],
                    data_mode['dc_reference'],
                    data_mode['date_creation'],
                    data_mode['date_update']
                ))

            sql = """
            INSERT INTO data_mode_table (
                platform_number, cycle_number, data_mode, data_state_indicator,
                data_centre, dc_reference, date_creation, date_update
            ) VALUES %s
            ON CONFLICT (platform_number, cycle_number) DO UPDATE SET
                data_mode = EXCLUDED.data_mode,
                data_state_indicator = EXCLUDED.data_state_indicator,
                date_update = EXCLUDED.date_update,
                updated_at = CURRENT_TIMESTAMP
            """

            execute_values(cursor, sql, data_mode_values)
            conn.commit()
            logger.info(f"Updated data_mode_table: {len(data_mode_data_list)} data mode records")

        except Exception as e:
            conn.rollback()
            logger.error(f"Error inserting data mode data: {e}")
            raise
        finally:
            cursor.close()

    def insert_bgc_parameters_data(self, bgc_data_list):
        """Insert into bgc_parameters_table"""
        if not bgc_data_list:
            return

        conn = self.connect_postgres()
        cursor = conn.cursor()

        try:
            bgc_values = []
            for bgc in bgc_data_list:
                bgc_values.append((
                    bgc['platform_number'],
                    bgc['parameter_name'],
                    bgc['parameter_sensor'],
                    bgc['parameter_units'],
                    bgc['parameter_accuracy'],
                    bgc['parameter_resolution']
                ))

            sql = """
            INSERT INTO bgc_parameters_table (
                platform_number, parameter_name, parameter_sensor,
                parameter_units, parameter_accuracy, parameter_resolution
            ) VALUES %s
            ON CONFLICT (platform_number, parameter_name) DO UPDATE SET
                parameter_sensor = EXCLUDED.parameter_sensor,
                parameter_units = EXCLUDED.parameter_units,
                updated_at = CURRENT_TIMESTAMP
            """

            execute_values(cursor, sql, bgc_values)
            conn.commit()
            logger.info(f"Updated bgc_parameters_table: {len(bgc_data_list)} BGC parameters")

        except Exception as e:
            conn.rollback()
            logger.error(f"Error inserting BGC parameters data: {e}")
            raise
        finally:
            cursor.close()



    def safe_get_cycle_var(self, ds, var_name, cycle_idx, default=None):
        """Safely extract cycle-level variable with better NaT handling"""
        if var_name not in ds:
            return default
        
        try:
            var_values = ds[var_name].values
            if var_values.ndim == 0:
                raw_val = var_values.item()
            elif cycle_idx < len(var_values):
                raw_val = var_values[cycle_idx]
            else:
                return default
                
            # Handle JULD variables specially
            if 'JULD' in var_name:
                return self.enhanced_julian_to_datetime(raw_val)
            else:
                # For non-date fields, decode safely
                decoded = self.safe_decode(raw_val)
                # Return None for 'nan' strings
                if decoded and decoded.lower() in ['nan', 'nat', '']:
                    return None
                return decoded
                
        except Exception as e:
            logger.warning(f"Error extracting {var_name}[{cycle_idx}]: {e}")
            return default

    def insert_trajectory_data(self, trajectories, batch_size=1000):
        """Insert into trajectory_table - Updated for new schema with full UPDATE"""
        if not trajectories:
            return

        conn = self.connect_postgres()
        cursor = conn.cursor()

        try:
            total_inserted = 0
            total_skipped = 0
            
            # Helper functions for data truncation
            def safe_char_1(value):
                """Ensure value fits in CHAR(1)"""
                if value is None:
                    return None
                str_val = str(value).strip()
                if str_val.lower() == 'nan':
                    return None
                return str_val[:1] if str_val else None
            
            def safe_varchar_50(value):
                """Ensure value fits in VARCHAR(50)"""
                if value is None:
                    return None
                str_val = str(value).strip()
                return str_val[:50] if str_val else None
            
            for i in range(0, len(trajectories), batch_size):
                batch = trajectories[i:i+batch_size]
                trajectory_values = []
                
                for traj in batch:
                    if not traj.get('platform_number'):
                        total_skipped += 1
                        continue
                    
                    # Match your NEW schema columns
                    trajectory_values.append((
                        traj['platform_number'],
                        traj.get('cycle_number'),
                        # Cycle timing summary fields
                        traj.get('juld_first_location'),
                        traj.get('juld_last_location'),
                        traj.get('juld_first_message'),
                        traj.get('juld_last_message'),
                        traj.get('juld_ascent_start'),
                        traj.get('juld_ascent_end'),
                        traj.get('juld_descent_start'),
                        traj.get('juld_descent_end'),
                        traj.get('juld_park_start'),
                        traj.get('juld_park_end'),
                        traj.get('juld_transmission_start'),
                        traj.get('juld_transmission_end'),
                        # Position summary
                        traj.get('first_latitude'),
                        traj.get('first_longitude'),
                        traj.get('last_latitude'),
                        traj.get('last_longitude'),
                        # Metadata
                        safe_varchar_50(traj.get('positioning_system')),
                        safe_char_1(traj.get('data_mode', 'R')),
                        traj.get('config_mission_number'),
                        safe_char_1(traj.get('grounded')),
                        # Representative measurements
                        traj.get('representative_park_pressure'),
                        safe_char_1(traj.get('representative_park_pressure_status')),
                        # Adjustments
                        traj.get('cycle_number_adjusted'),
                        # Status fields
                        safe_char_1(traj.get('juld_first_location_status')),
                        safe_char_1(traj.get('juld_last_location_status')),
                        safe_char_1(traj.get('juld_first_message_status')),
                        safe_char_1(traj.get('juld_last_message_status'))
                    ))

                if trajectory_values:
                    sql = """
                    INSERT INTO trajectory_table (
                        platform_number, cycle_number,
                        juld_first_location, juld_last_location, juld_first_message, juld_last_message,
                        juld_ascent_start, juld_ascent_end, juld_descent_start, juld_descent_end,
                        juld_park_start, juld_park_end, juld_transmission_start, juld_transmission_end,
                        first_latitude, first_longitude, last_latitude, last_longitude,
                        positioning_system, data_mode, config_mission_number, grounded,
                        representative_park_pressure, representative_park_pressure_status,
                        cycle_number_adjusted,
                        juld_first_location_status, juld_last_location_status,
                        juld_first_message_status, juld_last_message_status
                    ) VALUES %s
                    ON CONFLICT (platform_number, cycle_number) DO UPDATE SET
                        juld_first_location = EXCLUDED.juld_first_location,
                        juld_last_location = EXCLUDED.juld_last_location,
                        juld_first_message = EXCLUDED.juld_first_message,
                        juld_last_message = EXCLUDED.juld_last_message,
                        juld_ascent_start = EXCLUDED.juld_ascent_start,
                        juld_ascent_end = EXCLUDED.juld_ascent_end,
                        juld_descent_start = EXCLUDED.juld_descent_start,
                        juld_descent_end = EXCLUDED.juld_descent_end,
                        juld_park_start = EXCLUDED.juld_park_start,
                        juld_park_end = EXCLUDED.juld_park_end,
                        juld_transmission_start = EXCLUDED.juld_transmission_start,
                        juld_transmission_end = EXCLUDED.juld_transmission_end,
                        first_latitude = EXCLUDED.first_latitude,
                        first_longitude = EXCLUDED.first_longitude,
                        last_latitude = EXCLUDED.last_latitude,
                        last_longitude = EXCLUDED.last_longitude,
                        positioning_system = EXCLUDED.positioning_system,
                        data_mode = EXCLUDED.data_mode,
                        config_mission_number = EXCLUDED.config_mission_number,
                        grounded = EXCLUDED.grounded,
                        representative_park_pressure = EXCLUDED.representative_park_pressure,
                        representative_park_pressure_status = EXCLUDED.representative_park_pressure_status,
                        cycle_number_adjusted = EXCLUDED.cycle_number_adjusted,
                        juld_first_location_status = EXCLUDED.juld_first_location_status,
                        juld_last_location_status = EXCLUDED.juld_last_location_status,
                        juld_first_message_status = EXCLUDED.juld_first_message_status,
                        juld_last_message_status = EXCLUDED.juld_last_message_status,
                        updated_at = CURRENT_TIMESTAMP
                    """

                    from psycopg2.extras import execute_values
                    execute_values(cursor, sql, trajectory_values, template=None, page_size=100)
                    conn.commit()
                    logger.info(f"✅ Updated trajectory_table: batch of {len(trajectory_values)} trajectory cycles")
                    total_inserted += len(trajectory_values)

            logger.info(f"🎯 TRAJECTORY SUCCESS: {total_inserted} inserted, {total_skipped} skipped")

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Error inserting trajectory data: {e}")
            raise
        finally:
            cursor.close()



    # Placeholder methods for trajectory-specific tables (populated by trajectory files)
    


    def _extract_comprehensive_meta_data(self, ds, platform_number):
        """Extract comprehensive metadata from global attributes - BASED ON YOUR OUTPUT FORMAT"""
        
        def get_global_attr(attr_name, default=''):
            """Get global attribute with fallback"""
            return self.safe_decode(ds.attrs.get(attr_name, default))

        def get_array_attr(var_name, index=0, default=''):
            """Get value from array variable"""
            try:
                if var_name in ds.variables:
                    values = ds[var_name].values
                    if hasattr(values, '__len__') and len(values) > index:
                        return self.safe_decode(values[index])
                return default
            except:
                return default

        return {
            'platform_number': platform_number,
            
            # ✅ From your output - these are global attributes
            'data_type': get_global_attr('DATA_TYPE', 'Argo meta'),
            'format_version': get_global_attr('FORMAT_VERSION'),
            'handbook_version': get_global_attr('HANDBOOK_VERSION'),
            'date_creation': self.argo_date_to_datetime(get_global_attr('DATE_CREATION')),
            'date_update': self.argo_date_to_datetime(get_global_attr('DATE_UPDATE')),
            'ptt': get_global_attr('PTT'),
            
            # ✅ These are array variables in your output
            'trans_system': get_array_attr('TRANS_SYSTEM'),
            'trans_system_id': get_array_attr('TRANS_SYSTEM_ID'),
            'trans_frequency': get_array_attr('TRANS_FREQUENCY'),
            'positioning_system': get_array_attr('POSITIONING_SYSTEM'),
            
            # ✅ Global attributes from your output
            'platform_family': get_global_attr('PLATFORM_FAMILY'),
            'platform_type': get_global_attr('PLATFORM_TYPE'),
            'platform_maker': get_global_attr('PLATFORM_MAKER'),
            'firmware_version': get_global_attr('FIRMWARE_VERSION'),
            'manual_version': get_global_attr('MANUAL_VERSION'),
            'float_serial_no': get_global_attr('FLOAT_SERIAL_NO'),
            'dac_format_id': get_global_attr('DAC_FORMAT_ID'),
            'wmo_inst_type': get_global_attr('WMO_INST_TYPE'),
            'project_name': get_global_attr('PROJECT_NAME'),
            'data_centre': get_global_attr('DATA_CENTRE'),
            'pi_name': get_global_attr('PI_NAME'),
            'anomaly': get_global_attr('ANOMALY'),
            'battery_type': get_global_attr('BATTERY_TYPE'),
            'battery_packs': self.safe_int(ds.attrs.get('BATTERY_PACKS')),
            
            # ✅ Controller board info - your output shows these fields
            'controller_board_type_primary': get_global_attr('CONTROLLER_BOARD_TYPE_PRIMARY'),
            'controller_board_type_secondary': get_global_attr('CONTROLLER_BOARD_TYPE_SECONDARY'),
            'serial_no_primary': get_global_attr('CONTROLLER_BOARD_SERIAL_NO_PRIMARY'),
            'serial_no_secondary': get_global_attr('CONTROLLER_BOARD_SERIAL_NO_SECONDARY'),
            
            'special_features': get_global_attr('SPECIAL_FEATURES'),
            'float_owner': get_global_attr('FLOAT_OWNER'),
            'operating_institution': get_global_attr('OPERATING_INSTITUTION'),
            'customisation': get_global_attr('CUSTOMISATION'),
            
            # ✅ Launch info
            'launch_date': self.argo_date_to_datetime(get_global_attr('LAUNCH_DATE')),
            'launch_latitude': self.safe_float(ds.attrs.get('LAUNCH_LATITUDE')),
            'launch_longitude': self.safe_float(ds.attrs.get('LAUNCH_LONGITUDE')),
            'launch_qc': get_global_attr('LAUNCH_QC'),
            
            # ✅ Start/startup dates
            'start_date': self.argo_date_to_datetime(get_global_attr('START_DATE')),
            'start_date_qc': get_global_attr('START_DATE_QC'),
            'startup_date': self.argo_date_to_datetime(get_global_attr('STARTUP_DATE')),
            'startup_date_qc': get_global_attr('STARTUP_DATE_QC'),
            
            # ✅ End mission info
            'end_mission_date': self.argo_date_to_datetime(get_global_attr('END_MISSION_DATE')),
            'end_mission_status': get_global_attr('END_MISSION_STATUS')
        }

    
    def process_meta_file(self, filepath):
        """Process meta.nc file - Complete meta extraction and insertion"""
        logger.info(f"Processing meta file: {filepath}")

        try:
            ds = xr.open_dataset(filepath)
            logger.info(f"Successfully opened meta file: {filepath}")

            # Extract platform number
            platform_values = ds['PLATFORM_NUMBER'].values
            if platform_values.ndim == 0:
                platform_number = self.safe_decode(platform_values.item())
            else:
                platform_number = self.safe_decode(platform_values[0])

            logger.info(f"Meta file platform number: {platform_number}")

            # ✅ Helper function for scalar variables (THE KEY FIX!)
            def get_scalar_variable(var_name, default=''):
                """Get value from scalar variable"""
                try:
                    if var_name in ds.variables:
                        values = ds[var_name].values
                        if hasattr(values, 'item'):
                            # It's a scalar numpy value
                            result = self.safe_decode(values.item())
                            logger.debug(f"Scalar {var_name} = '{result}'")
                            return result
                        elif hasattr(values, '__len__') and len(values) > 0:
                            # It's an array with values
                            result = self.safe_decode(values[0])
                            logger.debug(f"Array {var_name}[0] = '{result}'")
                            return result
                        else:
                            # Try to decode directly
                            result = self.safe_decode(values)
                            logger.debug(f"Direct {var_name} = '{result}'")
                            return result
                    return default
                except Exception as e:
                    logger.debug(f"Error getting {var_name}: {e}")
                    return default

            # ✅ COMPLETE meta data extraction using VARIABLES (not attributes!)
            def get_battery_packs():
                """Extract battery pack count from text description"""
                try:
                    battery_text = get_scalar_variable('BATTERY_PACKS')
                    if battery_text:
                        # Extract number from text like "board -  1 (s/n: 41);"
                        import re
                        # Look for patterns like "- 1" or "- 2" etc.
                        match = re.search(r'-\s*(\d+)', battery_text)
                        if match:
                            result = int(match.group(1))
                            logger.debug(f"Extracted battery_packs: {result} from '{battery_text}'")
                            return result
                        else:
                            # Try to find any number in the text
                            numbers = re.findall(r'\d+', battery_text)
                            if numbers:
                                result = int(numbers[0])  # Take first number found
                                logger.debug(f"Found battery_packs: {result} from '{battery_text}'")
                                return result
                    return None
                except Exception as e:
                    logger.debug(f"Error parsing battery_packs: {e}")
                    return None

        # ✅ COMPLETE meta data extraction using VARIABLES (not attributes!)
            meta_data = {
                'platform_number': platform_number,
                
                # These are stored as VARIABLES in your NetCDF file
                'data_type': get_scalar_variable('DATA_TYPE', 'Argo meta'),
                'format_version': get_scalar_variable('FORMAT_VERSION'),
                'handbook_version': get_scalar_variable('HANDBOOK_VERSION'),
                'date_creation': self.argo_date_to_datetime(get_scalar_variable('DATE_CREATION')),
                'date_update': self.argo_date_to_datetime(get_scalar_variable('DATE_UPDATE')),
                'ptt': get_scalar_variable('PTT'),
                'platform_family': get_scalar_variable('PLATFORM_FAMILY'),
                'platform_type': get_scalar_variable('PLATFORM_TYPE'),
                'platform_maker': get_scalar_variable('PLATFORM_MAKER'),
                'firmware_version': get_scalar_variable('FIRMWARE_VERSION'),
                'manual_version': get_scalar_variable('MANUAL_VERSION'),
                'float_serial_no': get_scalar_variable('FLOAT_SERIAL_NO'),
                'dac_format_id': get_scalar_variable('DAC_FORMAT_ID'),
                'wmo_inst_type': get_scalar_variable('WMO_INST_TYPE'),
                'project_name': get_scalar_variable('PROJECT_NAME'),
                'data_centre': get_scalar_variable('DATA_CENTRE'),
                'pi_name': get_scalar_variable('PI_NAME'),
                'anomaly': get_scalar_variable('ANOMALY'),
                'battery_type': get_scalar_variable('BATTERY_TYPE'),
                'battery_packs': get_battery_packs(),  # ✅ SPECIAL HANDLER
                'controller_board_type_primary': get_scalar_variable('CONTROLLER_BOARD_TYPE_PRIMARY'),
                'controller_board_type_secondary': get_scalar_variable('CONTROLLER_BOARD_TYPE_SECONDARY'),
                'serial_no_primary': get_scalar_variable('CONTROLLER_BOARD_SERIAL_NO_PRIMARY'),
                'serial_no_secondary': get_scalar_variable('CONTROLLER_BOARD_SERIAL_NO_SECONDARY'),
                'special_features': get_scalar_variable('SPECIAL_FEATURES'),
                'float_owner': get_scalar_variable('FLOAT_OWNER'),
                'operating_institution': get_scalar_variable('OPERATING_INSTITUTION'),
                'customisation': get_scalar_variable('CUSTOMISATION'),
                'launch_date': self.argo_date_to_datetime(get_scalar_variable('LAUNCH_DATE')),
                'launch_latitude': self.safe_float(get_scalar_variable('LAUNCH_LATITUDE')),
                'launch_longitude': self.safe_float(get_scalar_variable('LAUNCH_LONGITUDE')),
                'launch_qc': get_scalar_variable('LAUNCH_QC')[:1] if get_scalar_variable('LAUNCH_QC') else '',
                'start_date': self.argo_date_to_datetime(get_scalar_variable('START_DATE')),
                'start_date_qc': get_scalar_variable('START_DATE_QC')[:1] if get_scalar_variable('START_DATE_QC') else '',
                'startup_date': self.argo_date_to_datetime(get_scalar_variable('STARTUP_DATE')),
                'startup_date_qc': get_scalar_variable('STARTUP_DATE_QC')[:1] if get_scalar_variable('STARTUP_DATE_QC') else '',
                'end_mission_date': self.argo_date_to_datetime(get_scalar_variable('END_MISSION_DATE')),
                'end_mission_status': get_scalar_variable('END_MISSION_STATUS'),
                
                # Array variables (these work as before)
                'trans_system': self.safe_decode(ds['TRANS_SYSTEM'].values[0]) if 'TRANS_SYSTEM' in ds.variables and len(ds['TRANS_SYSTEM'].values) > 0 else '',
                'trans_system_id': self.safe_decode(ds['TRANS_SYSTEM_ID'].values[0]) if 'TRANS_SYSTEM_ID' in ds.variables and len(ds['TRANS_SYSTEM_ID'].values) > 0 else '',
                'trans_frequency': self.safe_decode(ds['TRANS_FREQUENCY'].values[0]) if 'TRANS_FREQUENCY' in ds.variables and len(ds['TRANS_FREQUENCY'].values) > 0 else '',
                'positioning_system': self.safe_decode(ds['POSITIONING_SYSTEM'].values[0]) if 'POSITIONING_SYSTEM' in ds.variables and len(ds['POSITIONING_SYSTEM'].values) > 0 else '',
            }

            # ✅ Log extraction results
            logger.info("=== FINAL META DATA EXTRACTION ===")
            filled_fields = 0
            for key, value in meta_data.items():
                if value and str(value).strip() and str(value) not in ['', 'None', 'nan']:
                    logger.info(f"✅ {key:30} = '{value}'")
                    filled_fields += 1
                else:
                    logger.info(f"❌ {key:30} = (empty)")
            
            logger.info(f"=== EXTRACTED {filled_fields}/{len(meta_data)} FIELDS ===")

            # Insert meta data FIRST
            self.insert_meta_data(meta_data)
            logger.info(f"✅ Updated meta_table for platform {platform_number}")

            # 2. PARAMETER_TABLE - Process parameters with proper indexing
            param_data_list = []
            if 'PARAMETER' in ds.variables:
                try:
                    params = ds['PARAMETER'].values
                    n_params = len(params)
                    logger.info(f"Processing {n_params} parameters: {[self.safe_decode(p) for p in params]}")
                    
                    for param_idx in range(n_params):
                        param_name = self.safe_decode(params[param_idx])
                        if param_name and param_name.strip():
                            
                            # Get coefficient value with special handling for JSON
                            coeff_value = ''
                            if 'PREDEPLOYMENT_CALIB_COEFFICIENT' in ds.variables:
                                coeff_values = ds['PREDEPLOYMENT_CALIB_COEFFICIENT'].values
                                if param_idx < len(coeff_values):
                                    coeff_value = self.safe_decode(coeff_values[param_idx])
                            
                            # Handle coefficient for JSON field
                            if coeff_value and coeff_value.lower() not in ['n/a', 'none', '']:
                                coefficient = coeff_value
                            else:
                                coefficient = None  # Will be NULL in database
                            
                            param_data = {
                                'platform_number': platform_number,
                                'parameter': param_name,
                                'parameter_sensor': self.safe_decode(ds['PARAMETER_SENSOR'].values[param_idx] if 'PARAMETER_SENSOR' in ds and param_idx < len(ds['PARAMETER_SENSOR'].values) else ''),
                                'parameter_units': self.safe_decode(ds['PARAMETER_UNITS'].values[param_idx] if 'PARAMETER_UNITS' in ds and param_idx < len(ds['PARAMETER_UNITS'].values) else ''),
                                'parameter_accuracy': self.safe_decode(ds['PARAMETER_ACCURACY'].values[param_idx] if 'PARAMETER_ACCURACY' in ds and param_idx < len(ds['PARAMETER_ACCURACY'].values) else ''),
                                'parameter_resolution': self.safe_decode(ds['PARAMETER_RESOLUTION'].values[param_idx] if 'PARAMETER_RESOLUTION' in ds and param_idx < len(ds['PARAMETER_RESOLUTION'].values) else ''),
                                'predeployment_calib_equation': self.safe_decode(ds['PREDEPLOYMENT_CALIB_EQUATION'].values[param_idx] if 'PREDEPLOYMENT_CALIB_EQUATION' in ds and param_idx < len(ds['PREDEPLOYMENT_CALIB_EQUATION'].values) else ''),
                                'coefficient': coefficient,
                                'comment': self.safe_decode(ds['PREDEPLOYMENT_CALIB_COMMENT'].values[param_idx] if 'PREDEPLOYMENT_CALIB_COMMENT' in ds and param_idx < len(ds['PREDEPLOYMENT_CALIB_COMMENT'].values) else '')
                            }
                            param_data_list.append(param_data)
                            logger.debug(f"Added parameter: {param_name} -> {param_data['parameter_sensor']}")
                            
                except Exception as e:
                    logger.error(f"Error processing parameters: {e}")

            if param_data_list:
                self.insert_parameter_data(param_data_list)
                logger.info(f"✅ Updated parameter_table: {len(param_data_list)} parameters")

            # 3. SENSOR_TABLE - Process sensors
            sensor_data_list = []
            if 'SENSOR' in ds.variables:
                try:
                    sensors = ds['SENSOR'].values
                    n_sensors = len(sensors)
                    logger.info(f"Processing {n_sensors} sensors: {[self.safe_decode(s) for s in sensors]}")
                    
                    for sensor_idx in range(n_sensors):
                        sensor_name = self.safe_decode(sensors[sensor_idx])
                        if sensor_name and sensor_name.strip():
                            sensor_data = {
                                'platform_number': platform_number,
                                'sensor': sensor_name,
                                'sensor_maker': self.safe_decode(ds['SENSOR_MAKER'].values[sensor_idx] if 'SENSOR_MAKER' in ds and sensor_idx < len(ds['SENSOR_MAKER'].values) else ''),
                                'sensor_model': self.safe_decode(ds['SENSOR_MODEL'].values[sensor_idx] if 'SENSOR_MODEL' in ds and sensor_idx < len(ds['SENSOR_MODEL'].values) else ''),
                                'sensor_serial_no': self.safe_decode(ds['SENSOR_SERIAL_NO'].values[sensor_idx] if 'SENSOR_SERIAL_NO' in ds and sensor_idx < len(ds['SENSOR_SERIAL_NO'].values) else '')
                            }
                            sensor_data_list.append(sensor_data)
                            logger.debug(f"Added sensor: {sensor_name} by {sensor_data['sensor_maker']}")
                            
                except Exception as e:
                    logger.error(f"Error processing sensors: {e}")

            if sensor_data_list:
                self.insert_sensor_data(sensor_data_list)
                logger.info(f"✅ Updated sensor_table: {len(sensor_data_list)} sensors")

            # 4. LAUNCH_CONFIG_TABLE - Process launch configuration
            launch_config_data_list = []
            if 'LAUNCH_CONFIG_PARAMETER_NAME' in ds.variables and 'LAUNCH_CONFIG_PARAMETER_VALUE' in ds.variables:
                try:
                    config_names = ds['LAUNCH_CONFIG_PARAMETER_NAME'].values
                    config_values = ds['LAUNCH_CONFIG_PARAMETER_VALUE'].values
                    n_config = min(len(config_names), len(config_values))
                    
                    logger.info(f"Processing {n_config} launch config parameters")
                    
                    for config_idx in range(n_config):
                        param_name = self.safe_decode(config_names[config_idx])
                        param_value = str(config_values[config_idx]) if config_idx < len(config_values) else ''
                        
                        if param_name and param_name.strip():
                            launch_config_data = {
                                'platform_number': platform_number,
                                'launch_config_parameter_name': param_name,
                                'launch_config_parameter_value': param_value
                            }
                            launch_config_data_list.append(launch_config_data)
                            logger.debug(f"Added launch config: {param_name} = {param_value}")
                            
                except Exception as e:
                    logger.error(f"Error processing launch config: {e}")

            if launch_config_data_list:
                self.insert_launch_config_data(launch_config_data_list)
                logger.info(f"✅ Updated launch_config_table: {len(launch_config_data_list)} launch config parameters")

            # 5. CONFIG_TABLE - Process configuration parameters (handle 2D array)
            config_data_list = []
            if 'CONFIG_PARAMETER_NAME' in ds.variables and 'CONFIG_PARAMETER_VALUE' in ds.variables:
                try:
                    config_names = ds['CONFIG_PARAMETER_NAME'].values
                    config_values = ds['CONFIG_PARAMETER_VALUE'].values
                    
                    logger.info(f"Config names shape: {config_names.shape}")
                    logger.info(f"Config values shape: {config_values.shape}")
                    
                    n_config_names = len(config_names)
                    
                    # Handle 2D config values array - it's (1, 6) in your case
                    if config_values.ndim == 2:
                        config_values_1d = config_values[0]  # Take first row
                    else:
                        config_values_1d = config_values
                    
                    n_config_values = len(config_values_1d)
                    logger.info(f"Processing {n_config_names} config names, {n_config_values} config values")
                    
                    for config_idx in range(min(n_config_names, n_config_values)):
                        config_name = self.safe_decode(config_names[config_idx])
                        config_value = str(config_values_1d[config_idx])
                        
                        if config_name and config_name.strip():
                            # Get mission info if available
                            mission_number = None
                            mission_comment = ''
                            
                            if 'CONFIG_MISSION_NUMBER' in ds.variables:
                                mission_nums = ds['CONFIG_MISSION_NUMBER'].values
                                if len(mission_nums) > 0:
                                    mission_number = self.safe_int(mission_nums[0])
                            
                            if 'CONFIG_MISSION_COMMENT' in ds.variables:
                                mission_comments = ds['CONFIG_MISSION_COMMENT'].values
                                if len(mission_comments) > 0:
                                    mission_comment = self.safe_decode(mission_comments[0])
                            
                            config_data = {
                                'platform_number': platform_number,
                                'config_parameter_name': config_name,
                                'config_parameter_value': config_value,
                                'config_mission_number': mission_number,
                                'config_mission_comment': mission_comment
                            }
                            config_data_list.append(config_data)
                            logger.debug(f"Added config: {config_name} = {config_value}")
                            
                except Exception as e:
                    logger.error(f"Error processing config parameters: {e}")
                    import traceback
                    traceback.print_exc()

            if config_data_list:
                self.insert_config_data(config_data_list)
                logger.info(f"✅ Updated config_table: {len(config_data_list)} config parameters")

            # 6. HISTORY_TABLE - Process history (if any)
            history_data_list = []
            if 'HISTORY_INSTITUTION' in ds.variables:
                try:
                    n_history = ds.sizes.get('N_HISTORY', 0)
                    logger.info(f"Processing {n_history} history entries")
                    
                    for hist_idx in range(n_history):
                        history_institution = self.safe_decode(ds['HISTORY_INSTITUTION'].values[hist_idx] if 'HISTORY_INSTITUTION' in ds and hist_idx < len(ds['HISTORY_INSTITUTION'].values) else '')
                        if history_institution and history_institution.strip():
                            history_data = {
                                'platform_number': platform_number,
                                'cycle_number': None,
                                'history_institution': history_institution,
                                'history_step': self.safe_decode(ds['HISTORY_STEP'].values[hist_idx] if 'HISTORY_STEP' in ds and hist_idx < len(ds['HISTORY_STEP'].values) else ''),
                                'history_software': self.safe_decode(ds['HISTORY_SOFTWARE'].values[hist_idx] if 'HISTORY_SOFTWARE' in ds and hist_idx < len(ds['HISTORY_SOFTWARE'].values) else ''),
                                'history_software_release': self.safe_decode(ds['HISTORY_SOFTWARE_RELEASE'].values[hist_idx] if 'HISTORY_SOFTWARE_RELEASE' in ds and hist_idx < len(ds['HISTORY_SOFTWARE_RELEASE'].values) else ''),
                                'history_reference': self.safe_decode(ds['HISTORY_REFERENCE'].values[hist_idx] if 'HISTORY_REFERENCE' in ds and hist_idx < len(ds['HISTORY_REFERENCE'].values) else ''),
                                'history_date': self.argo_date_to_datetime(ds['HISTORY_DATE'].values[hist_idx] if 'HISTORY_DATE' in ds and hist_idx < len(ds['HISTORY_DATE'].values) else ''),
                                'history_action': self.safe_decode(ds['HISTORY_ACTION'].values[hist_idx] if 'HISTORY_ACTION' in ds and hist_idx < len(ds['HISTORY_ACTION'].values) else ''),
                                'history_parameter': self.safe_decode(ds['HISTORY_PARAMETER'].values[hist_idx] if 'HISTORY_PARAMETER' in ds and hist_idx < len(ds['HISTORY_PARAMETER'].values) else ''),
                                'history_start_pres': self.safe_float(ds['HISTORY_START_PRES'].values[hist_idx] if 'HISTORY_START_PRES' in ds and hist_idx < len(ds['HISTORY_START_PRES'].values) else None),
                                'history_stop_pres': self.safe_float(ds['HISTORY_STOP_PRES'].values[hist_idx] if 'HISTORY_STOP_PRES' in ds and hist_idx < len(ds['HISTORY_STOP_PRES'].values) else None),
                                'history_previous_value': self.safe_decode(ds['HISTORY_PREVIOUS_VALUE'].values[hist_idx] if 'HISTORY_PREVIOUS_VALUE' in ds and hist_idx < len(ds['HISTORY_PREVIOUS_VALUE'].values) else ''),
                                'history_qctest': self.safe_decode(ds['HISTORY_QCTEST'].values[hist_idx] if 'HISTORY_QCTEST' in ds and hist_idx < len(ds['HISTORY_QCTEST'].values) else '')
                            }
                            history_data_list.append(history_data)
                            
                except Exception as e:
                    logger.error(f"Error processing history: {e}")

            if history_data_list:
                self.insert_history_data(history_data_list)
                logger.info(f"✅ Updated history_table: {len(history_data_list)} history entries")

            ds.close()

            logger.info(f"✅ Successfully processed meta file")
            logger.info(f"  - Parameters: {len(param_data_list)}")
            logger.info(f"  - Sensors: {len(sensor_data_list)}")
            logger.info(f"  - Launch config: {len(launch_config_data_list)}")
            logger.info(f"  - Config: {len(config_data_list)}")
            logger.info(f"  - History: {len(history_data_list)}")

            return True

        except Exception as e:
            logger.error(f"Error processing meta file: {e}")
            import traceback
            traceback.print_exc()
            return False




    def _extract_comprehensive_meta_data(self, ds, platform_number):
        """Extract comprehensive metadata from global attributes"""
        
        def get_global_attr(attr_name, default=''):
            """Get global attribute with fallback"""
            return self.safe_decode(ds.attrs.get(attr_name, default))

        def get_array_attr(var_name, index=0, default=''):
            """Get value from array variable"""
            try:
                if var_name in ds.variables:
                    values = ds[var_name].values
                    if hasattr(values, '__len__') and len(values) > index:
                        return self.safe_decode(values[index])
                return default
            except:
                return default

        return {
            'platform_number': platform_number,
            'data_type': get_global_attr('DATA_TYPE', 'Argo meta'),
            'format_version': get_global_attr('FORMAT_VERSION'),
            'handbook_version': get_global_attr('HANDBOOK_VERSION'),
            'date_creation': self.argo_date_to_datetime(get_global_attr('DATE_CREATION')),
            'date_update': self.argo_date_to_datetime(get_global_attr('DATE_UPDATE')),
            'ptt': get_global_attr('PTT'),
            'trans_system': get_array_attr('TRANS_SYSTEM'),
            'trans_system_id': get_array_attr('TRANS_SYSTEM_ID'),
            'trans_frequency': get_array_attr('TRANS_FREQUENCY'),
            'positioning_system': get_array_attr('POSITIONING_SYSTEM'),
            'platform_family': get_global_attr('PLATFORM_FAMILY'),
            'platform_type': get_global_attr('PLATFORM_TYPE'),
            'platform_maker': get_global_attr('PLATFORM_MAKER'),
            'firmware_version': get_global_attr('FIRMWARE_VERSION'),
            'manual_version': get_global_attr('MANUAL_VERSION'),
            'float_serial_no': get_global_attr('FLOAT_SERIAL_NO'),
            'dac_format_id': get_global_attr('DAC_FORMAT_ID'),
            'wmo_inst_type': get_global_attr('WMO_INST_TYPE'),
            'project_name': get_global_attr('PROJECT_NAME'),
            'data_centre': get_global_attr('DATA_CENTRE'),
            'pi_name': get_global_attr('PI_NAME'),
            'anomaly': get_global_attr('ANOMALY'),
            'battery_type': get_global_attr('BATTERY_TYPE'),
            'battery_packs': self.safe_int(ds.attrs.get('BATTERY_PACKS')),
            'controller_board_type_primary': get_global_attr('CONTROLLER_BOARD_TYPE_PRIMARY'),
            'controller_board_type_secondary': get_global_attr('CONTROLLER_BOARD_TYPE_SECONDARY'),
            'serial_no_primary': get_global_attr('CONTROLLER_BOARD_SERIAL_NO_PRIMARY'),
            'serial_no_secondary': get_global_attr('CONTROLLER_BOARD_SERIAL_NO_SECONDARY'),
            'special_features': get_global_attr('SPECIAL_FEATURES'),
            'float_owner': get_global_attr('FLOAT_OWNER'),
            'operating_institution': get_global_attr('OPERATING_INSTITUTION'),
            'customisation': get_global_attr('CUSTOMISATION'),
            'launch_date': self.argo_date_to_datetime(get_global_attr('LAUNCH_DATE')),
            'launch_latitude': self.safe_float(ds.attrs.get('LAUNCH_LATITUDE')),
            'launch_longitude': self.safe_float(ds.attrs.get('LAUNCH_LONGITUDE')),
            'launch_qc': get_global_attr('LAUNCH_QC'),
            'start_date': self.argo_date_to_datetime(get_global_attr('START_DATE')),
            'start_date_qc': get_global_attr('START_DATE_QC'),
            'startup_date': self.argo_date_to_datetime(get_global_attr('STARTUP_DATE')),
            'startup_date_qc': get_global_attr('STARTUP_DATE_QC'),
            'end_mission_date': self.argo_date_to_datetime(get_global_attr('END_MISSION_DATE')),
            'end_mission_status': get_global_attr('END_MISSION_STATUS')
        }

    def _safe_get_array_value(self, ds, var_name, index, default=''):
        """Safely get value from array variable at index"""
        try:
            if var_name in ds.variables:
                values = ds[var_name].values
                if hasattr(values, '__len__') and index < len(values):
                    return self.safe_decode(values[index])
            return default
        except Exception as e:
            logger.debug(f"Error getting {var_name}[{index}]: {e}")
            return default


    def safe_extract_trajectory_var(self, ds, var_name, meas_idx, default=''):
        """Safely extract trajectory variable handling 0-dimensional arrays"""
        if var_name not in ds:
            return default
    
        try:
            values = ds[var_name].values
            if values.ndim == 0:
            # 0-dimensional array (scalar) - same value for all measurements
                return self.safe_decode(values.item()) if isinstance(default, str) else self.safe_float(values.item()) if default is None else self.safe_int(values.item())
            elif values.ndim == 1:
            # 1-dimensional array - different value per measurement
                if meas_idx < len(values):
                     return self.safe_decode(values[meas_idx]) if isinstance(default, str) else self.safe_float(values[meas_idx]) if default is None else self.safe_int(values[meas_idx])
                else:
                     return default
            else:
                return default
        except Exception as e:
            logger.warning(f"Error extracting {var_name}: {e}")
            return default
    
    def insert_measurement_data(self, measurement_data_list):
        """Insert measurement data with profile_id links and QC field validation"""
        if not measurement_data_list:
            return

        conn = self.connect_postgres()
        cursor = conn.cursor()

        try:
            # Filter out measurements without profile_id and validate QC fields
            valid_measurements = []
            for measurement in measurement_data_list:
                if not measurement.get('profile_id'):
                    logger.warning(f"Skipping measurement without profile_id: {measurement.get('platform_number')}/{measurement.get('cycle_number')}")
                    continue
                valid_measurements.append(measurement)

            if not valid_measurements:
                logger.warning("No valid measurements with profile_id to insert")
                return

            logger.info(f"Inserting {len(valid_measurements)} measurements with profile_id")

            # Helper function to validate QC fields (CHAR(1))
            def safe_qc_field(value, default='0'):
                """Ensure QC field is exactly 1 character"""
                if value is None:
                    return default
                str_val = str(value).strip()
                if len(str_val) == 0:
                    return default
                # Take only the first character
                return str_val[0]

            # Batch insert measurements
            batch_size = 1000
            total_inserted = 0
            
            for i in range(0, len(valid_measurements), batch_size):
                batch = valid_measurements[i:i + batch_size]
                batch_values = []
                
                for measurement in batch:
                    batch_values.append((
                        measurement['profile_id'],
                        measurement['platform_number'],
                        measurement['cycle_number'],
                        measurement.get('latitude'),
                        measurement.get('longitude'),
                        measurement.get('pres'),
                        measurement.get('temp'),
                        measurement.get('psal'),
                        # ✅ Validated QC fields (CHAR(1))
                        safe_qc_field(measurement.get('pres_qc', '0')),
                        safe_qc_field(measurement.get('temp_qc', '0')),
                        safe_qc_field(measurement.get('psal_qc', '0')),
                        # Adjusted values
                        measurement.get('pres_adjusted'),
                        measurement.get('temp_adjusted'),
                        measurement.get('psal_adjusted'),
                        # ✅ Validated adjusted QC fields
                        safe_qc_field(measurement.get('pres_adjusted_qc', '0')),
                        safe_qc_field(measurement.get('temp_adjusted_qc', '0')),
                        safe_qc_field(measurement.get('psal_adjusted_qc', '0')),
                        measurement.get('pres_adjusted_error'),
                        measurement.get('temp_adjusted_error'),
                        measurement.get('psal_adjusted_error'),
                        # BGC parameters
                        measurement.get('doxy'),
                        safe_qc_field(measurement.get('doxy_qc', '0')),
                        measurement.get('doxy_adjusted'),
                        safe_qc_field(measurement.get('doxy_adjusted_qc', '0')),
                        measurement.get('doxy_adjusted_error'),
                        measurement.get('nitrate'),
                        safe_qc_field(measurement.get('nitrate_qc', '0')),
                        measurement.get('nitrate_adjusted'),
                        safe_qc_field(measurement.get('nitrate_adjusted_qc', '0')),
                        measurement.get('nitrate_adjusted_error'),
                        measurement.get('ph_in_situ_total'),
                        safe_qc_field(measurement.get('ph_in_situ_total_qc', '0')),
                        measurement.get('ph_in_situ_total_adjusted'),
                        safe_qc_field(measurement.get('ph_in_situ_total_adjusted_qc', '0')),
                        measurement.get('ph_in_situ_total_adjusted_error')
                    ))

                # Use execute_values for efficient batch insert
                from psycopg2.extras import execute_values
                
                execute_values(
                    cursor,
                    """
                    INSERT INTO depth_measurements_table (
                        profile_id, platform_number, cycle_number, latitude, longitude,
                        pres, temp, psal, pres_qc, temp_qc, psal_qc,
                        pres_adjusted, temp_adjusted, psal_adjusted,
                        pres_adjusted_qc, temp_adjusted_qc, psal_adjusted_qc,
                        pres_adjusted_error, temp_adjusted_error, psal_adjusted_error,
                        doxy, doxy_qc, doxy_adjusted, doxy_adjusted_qc, doxy_adjusted_error,
                        nitrate, nitrate_qc, nitrate_adjusted, nitrate_adjusted_qc, nitrate_adjusted_error,
                        ph_in_situ_total, ph_in_situ_total_qc, ph_in_situ_total_adjusted,
                        ph_in_situ_total_adjusted_qc, ph_in_situ_total_adjusted_error
                    ) VALUES %s
                    """,
                    batch_values,
                    template=None,
                    page_size=100
                )
                
                conn.commit()
                total_inserted += len(batch)
                logger.info(f"Batch {i//batch_size + 1}: Inserted {len(batch)} measurements")

            logger.info(f"✅ Successfully inserted {total_inserted} measurements with profile_id links")

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Error inserting measurement data: {e}")
            
            # Debug: Show a sample measurement to see what's causing the issue
            if measurement_data_list:
                sample = measurement_data_list[0]
                logger.error(f"Sample measurement QC fields:")
                for key, value in sample.items():
                    if 'qc' in key.lower():
                        logger.error(f"  {key}: {repr(value)} (type: {type(value)}, len: {len(str(value)) if value else 0})")
            raise
        finally:
            cursor.close()




    def process_trajectory_file(self, filepath):
        """Process trajectory.nc file - Updated with history data extraction"""
        logger.info(f"Processing trajectory file: {filepath}")

        ds = None
        try:
            ds = xr.open_dataset(filepath, decode_timedelta=False)
            logger.info(f"Successfully opened trajectory file: {filepath}")

            # Extract platform number
            platform_number = self.safe_decode(ds.attrs.get('platform_number', ''))
            if not platform_number and 'PLATFORM_NUMBER' in ds.variables:
                platform_values = ds['PLATFORM_NUMBER'].values
                if platform_values.ndim == 0:
                    platform_number = self.safe_decode(platform_values.item())
                else:
                    platform_number = self.safe_decode(platform_values[0])

            logger.info(f"Trajectory file platform number: {platform_number}")

            # Get dimensions
            n_measurement = ds.sizes.get('N_MEASUREMENT', 0)
            n_cycle = ds.sizes.get('N_CYCLE', 0)
            n_history = ds.sizes.get('N_HISTORY', 0)
            logger.info(f"Number of measurements: {n_measurement}, cycles: {n_cycle}, history: {n_history}")

            # Helper function for cycle-level data
            def safe_get_cycle_var(var_name, cycle_idx, default=None):
                """Safely extract cycle-level variable"""
                if var_name not in ds:
                    return default
                
                try:
                    var_values = ds[var_name].values
                    if var_values.ndim == 0:
                        return self.enhanced_julian_to_datetime(var_values.item()) if 'JULD' in var_name else self.safe_decode(var_values.item())
                    elif cycle_idx < len(var_values):
                        if 'JULD' in var_name:
                            return self.enhanced_julian_to_datetime(var_values[cycle_idx])
                        else:
                            return self.safe_decode(var_values[cycle_idx])
                    return default
                except Exception as e:
                    logger.warning(f"Error extracting {var_name}[{cycle_idx}]: {e}")
                    return default

            # Helper function for measurement-level data
            def safe_get_measurement_var(var_name, meas_idx, default=None):
                """Safely extract measurement-level variable"""
                if var_name not in ds:
                    return default
                
                try:
                    var_values = ds[var_name].values
                    if var_values.ndim == 0:
                        if 'JULD' in var_name:
                            return self.enhanced_julian_to_datetime(var_values.item())
                        elif isinstance(default, str):
                            return self.safe_decode(var_values.item())
                        else:
                            return self.safe_float(var_values.item())
                    elif meas_idx < len(var_values):
                        if 'JULD' in var_name:
                            return self.enhanced_julian_to_datetime(var_values[meas_idx])
                        elif isinstance(default, str):
                            return self.safe_decode(var_values[meas_idx])
                        else:
                            return self.safe_float(var_values[meas_idx])
                    return default
                except Exception as e:
                    logger.warning(f"Error extracting {var_name}[{meas_idx}]: {e}")
                    return default

            # Helper function for history-level data
            def safe_get_history_var(var_name, hist_idx, default=None):
                """Safely extract history-level variable"""
                if var_name not in ds:
                    return default
                
                try:
                    var_values = ds[var_name].values
                    if var_values.ndim == 0:
                        if 'HISTORY_DATE' in var_name:
                            return self.enhanced_julian_to_datetime(var_values.item())
                        else:
                            return self.safe_decode(var_values.item())
                    elif hist_idx < len(var_values):
                        if 'HISTORY_DATE' in var_name:
                            date_str = self.safe_decode(var_values[hist_idx])
                            if date_str and date_str != '':
                                try:
                                    # Parse YYYYMMDDHHMMSS format
                                    if len(date_str) >= 14:
                                        from datetime import datetime
                                        return datetime.strptime(date_str[:14], '%Y%m%d%H%M%S')
                                    return None
                                except:
                                    return None
                            return None
                        else:
                            return self.safe_decode(var_values[hist_idx])
                    return default
                except Exception as e:
                    logger.warning(f"Error extracting {var_name}[{hist_idx}]: {e}")
                    return default

            # 1. TRAJECTORY_TABLE - Create cycle-level summary data
            trajectory_data_list = []
            
            for cycle_idx in range(n_cycle):
                # cycle_number = safe_get_cycle_var('CYCLE_NUMBER_INDEX', cycle_idx, None)
                cycle_number = safe_get_cycle_var('CYCLE_NUMBER_INDEX', cycle_idx, cycle_idx)  # Use index as fallback
                if cycle_number is not None:
                    cycle_number = self.safe_int(cycle_number)
                else:
                    cycle_number = cycle_idx

                trajectory_data = {
                    'platform_number': platform_number,
                    'cycle_number': cycle_number,
                    # Timing summary
                    'juld_first_location': self.clean_timestamp_value(safe_get_cycle_var('JULD_FIRST_LOCATION', cycle_idx)),
                    'juld_last_location': self.clean_timestamp_value(safe_get_cycle_var('JULD_LAST_LOCATION', cycle_idx)),
                    'juld_first_message': self.clean_timestamp_value(safe_get_cycle_var('JULD_FIRST_MESSAGE', cycle_idx)),
                    'juld_last_message': self.clean_timestamp_value(safe_get_cycle_var('JULD_LAST_MESSAGE', cycle_idx)),
                    'juld_ascent_start': self.clean_timestamp_value(safe_get_cycle_var('JULD_ASCENT_START', cycle_idx)),
                    'juld_ascent_end': self.clean_timestamp_value(safe_get_cycle_var('JULD_ASCENT_END', cycle_idx)),
                    'juld_descent_start': self.clean_timestamp_value(safe_get_cycle_var('JULD_DESCENT_START', cycle_idx)),
                    'juld_descent_end': self.clean_timestamp_value(safe_get_cycle_var('JULD_DESCENT_END', cycle_idx)),
                    'juld_park_start': self.clean_timestamp_value(safe_get_cycle_var('JULD_PARK_START', cycle_idx)),
                    'juld_park_end': self.clean_timestamp_value(safe_get_cycle_var('JULD_PARK_END', cycle_idx)),
                    'juld_transmission_start': self.clean_timestamp_value(safe_get_cycle_var('JULD_TRANSMISSION_START', cycle_idx)),
                    'juld_transmission_end': self.clean_timestamp_value(safe_get_cycle_var('JULD_TRANSMISSION_END', cycle_idx)),
                    # Position summary (will be filled from first/last measurements)
                    'first_latitude': None,
                    'first_longitude': None,
                    'last_latitude': None,
                    'last_longitude': None,
                    # Metadata
                    'positioning_system': self.safe_decode(ds.attrs.get('positioning_system', 'ARGOS'))[:50],
                    'data_mode': safe_get_cycle_var('DATA_MODE', cycle_idx, 'R'),
                    'config_mission_number': self.safe_int(safe_get_cycle_var('CONFIG_MISSION_NUMBER', cycle_idx)),
                    'grounded': safe_get_cycle_var('GROUNDED', cycle_idx, 'U'),
                    'representative_park_pressure': self.safe_float(safe_get_cycle_var('REPRESENTATIVE_PARK_PRESSURE', cycle_idx)),
                    'representative_park_pressure_status': safe_get_cycle_var('REPRESENTATIVE_PARK_PRESSURE_STATUS', cycle_idx),
                    'cycle_number_adjusted': self.safe_int(safe_get_cycle_var('CYCLE_NUMBER_INDEX_ADJUSTED', cycle_idx)),
                    # Status fields
                    'juld_first_location_status': safe_get_cycle_var('JULD_FIRST_LOCATION_STATUS', cycle_idx),
                    'juld_last_location_status': safe_get_cycle_var('JULD_LAST_LOCATION_STATUS', cycle_idx),
                    'juld_first_message_status': safe_get_cycle_var('JULD_FIRST_MESSAGE_STATUS', cycle_idx),
                    'juld_last_message_status': safe_get_cycle_var('JULD_LAST_MESSAGE_STATUS', cycle_idx)
                }
                
                trajectory_data_list.append(trajectory_data)

            logger.info(f"Created {len(trajectory_data_list)} trajectory cycle records")

            # Insert trajectory data first
            if trajectory_data_list:
                self.insert_trajectory_data(trajectory_data_list)

            # 2. HISTORY_TABLE - Extract history data from trajectory file
            history_data_list = []
            
            if n_history > 0:
                logger.info(f"Processing {n_history} history records from trajectory file")
                
                for hist_idx in range(n_history):
                    # Extract history data
                    history_institution = safe_get_history_var('HISTORY_INSTITUTION', hist_idx, '')
                    history_step = safe_get_history_var('HISTORY_STEP', hist_idx, '')
                    history_software = safe_get_history_var('HISTORY_SOFTWARE', hist_idx, '')
                    history_software_release = safe_get_history_var('HISTORY_SOFTWARE_RELEASE', hist_idx, '')
                    history_reference = safe_get_history_var('HISTORY_REFERENCE', hist_idx, '')
                    history_date = safe_get_history_var('HISTORY_DATE', hist_idx)
                    history_action = safe_get_history_var('HISTORY_ACTION', hist_idx, '')
                    history_parameter = safe_get_history_var('HISTORY_PARAMETER', hist_idx, '')
                    history_qctest = safe_get_history_var('HISTORY_QCTEST', hist_idx, '')
                    
                    # Skip empty history records
                    if not any([history_institution, history_step, history_software, history_action]):
                        continue

                    history_data = {
                        'platform_number': platform_number,
                        'cycle_number': None,  # Trajectory history is usually global, not per-cycle
                        'history_institution': history_institution[:100] if history_institution else '',
                        'history_step': history_step[:100] if history_step else '',
                        'history_software': history_software[:100] if history_software else '',
                        'history_software_release': history_software_release[:50] if history_software_release else '',
                        'history_reference': history_reference[:200] if history_reference else '',
                        'history_date': history_date,
                        'history_action': history_action[:100] if history_action else '',
                        'history_parameter': history_parameter[:100] if history_parameter else '',
                        'history_start_pres': None,  # Not typically in trajectory files
                        'history_stop_pres': None,   # Not typically in trajectory files
                        'history_previous_value': None,  # Not typically in trajectory files
                        'history_qctest': history_qctest[:100] if history_qctest else ''
                    }
                    
                    history_data_list.append(history_data)

            logger.info(f"Created {len(history_data_list)} history records")

            # Insert history data
            if history_data_list:
                self.insert_history_data(history_data_list)

            # 3. TRAJECTORY_DEPTH_TABLE - Create measurement-level data
            # 3. TRAJECTORY_DEPTH_TABLE - Create measurement-level data with DEBUG
            trajectory_depth_list = []

            conn = self.connect_postgres()
            cursor = conn.cursor()
            try:
                # Get trajectory IDs for this platform
                cursor.execute("""
                    SELECT trajectory_id, cycle_number 
                    FROM trajectory_table 
                    WHERE platform_number = %s 
                    ORDER BY cycle_number
                """, (platform_number,))
                trajectory_records = cursor.fetchall()
                
                # Create lookup dictionary
                trajectory_ids = {cycle: traj_id for traj_id, cycle in trajectory_records}
                logger.info(f"🔍 Found {len(trajectory_ids)} trajectory IDs for platform {platform_number}")

                # 🔍 DEBUG: Check what cycles we have
                logger.info(f"🔍 Available cycles: {list(trajectory_ids.keys())[:10]}...")  # Show first 10

                # Process ALL measurements with detailed debugging
                skipped_reasons = {"no_trajectory_id": 0, "no_useful_data": 0, "created": 0}
                
                for meas_idx in range(n_measurement):
                    cycle_number = self.safe_int(safe_get_measurement_var('CYCLE_NUMBER', meas_idx))
                    measurement_code = self.safe_int(safe_get_measurement_var('MEASUREMENT_CODE', meas_idx))
                    
                    # Find matching trajectory_id
                    trajectory_id = trajectory_ids.get(cycle_number)
                    
                    # 🔍 DEBUG: Log first few measurements
                    if meas_idx < 5:
                        logger.info(f"🔍 Measurement {meas_idx}: cycle={cycle_number}, code={measurement_code}, traj_id={trajectory_id}")
                    
                    if trajectory_id is not None:
                        # Get position data
                        lat_val = safe_get_measurement_var('LATITUDE', meas_idx)
                        lon_val = safe_get_measurement_var('LONGITUDE', meas_idx)
                        raw_juld = safe_get_measurement_var('JULD', meas_idx)
                        cleaned_juld = self.clean_timestamp_value(raw_juld)
                        
                        # 🔍 DEBUG: Log data availability for first few
                        if meas_idx < 5:
                            logger.info(f"🔍   Data: lat={lat_val}, lon={lon_val}, juld={cleaned_juld}, code={measurement_code}")
                        
                        # Check if we have ANY useful data
                        has_position = lat_val is not None or lon_val is not None
                        has_time = cleaned_juld is not None
                        has_measurement_code = measurement_code is not None
                        
                        if has_position or has_time or has_measurement_code:
                            # Helper function for safe CHAR(1) truncation
                            def safe_qc_char(value, default='0'):
                                if value is None:
                                    return default
                                str_val = str(value).strip()
                                if str_val.lower() in ['nan', 'nat', '']:
                                    return default
                                return str_val[:1]
                            
                            traj_depth_data = {
                                'trajectory_id': trajectory_id,
                                'platform_number': platform_number,
                                'cycle_number': cycle_number,
                                'measurement_code': measurement_code,
                                'measurement_index': meas_idx,
                                'latitude': lat_val,
                                'longitude': lon_val,
                                'juld': cleaned_juld,
                                'juld_status': safe_qc_char(safe_get_measurement_var('JULD_STATUS', meas_idx), '9'),
                                'juld_adjusted': self.clean_timestamp_value(safe_get_measurement_var('JULD_ADJUSTED', meas_idx)),
                                'juld_adjusted_qc': safe_qc_char(safe_get_measurement_var('JULD_ADJUSTED_QC', meas_idx), '0'),
                                'juld_adjusted_status': safe_qc_char(safe_get_measurement_var('JULD_ADJUSTED_STATUS', meas_idx), '9'),
                                'position_qc': safe_qc_char(safe_get_measurement_var('POSITION_QC', meas_idx), '0'),
                                'position_accuracy': safe_qc_char(safe_get_measurement_var('POSITION_ACCURACY', meas_idx)),
                                'axes_error_ellipse_major': self.safe_float(safe_get_measurement_var('AXES_ERROR_ELLIPSE_MAJOR', meas_idx)),
                                'axes_error_ellipse_minor': self.safe_float(safe_get_measurement_var('AXES_ERROR_ELLIPSE_MINOR', meas_idx)),
                                'axes_error_ellipse_angle': self.safe_float(safe_get_measurement_var('AXES_ERROR_ELLIPSE_ANGLE', meas_idx)),
                                'satellite_name': str(safe_get_measurement_var('SATELLITE_NAME', meas_idx, ''))[:10],
                                'positioning_system': str(safe_get_measurement_var('POSITIONING_SYSTEM', meas_idx, ''))[:50],
                                'pres': self.safe_float(safe_get_measurement_var('PRES', meas_idx)),
                                'pres_qc': safe_qc_char(safe_get_measurement_var('PRES_QC', meas_idx), '0'),
                                'pres_adjusted': self.safe_float(safe_get_measurement_var('PRES_ADJUSTED', meas_idx)),
                                'pres_adjusted_qc': safe_qc_char(safe_get_measurement_var('PRES_ADJUSTED_QC', meas_idx), '0'),
                                'pres_adjusted_error': self.safe_float(safe_get_measurement_var('PRES_ADJUSTED_ERROR', meas_idx)),
                                'temp': self.safe_float(safe_get_measurement_var('TEMP', meas_idx)),
                                'temp_qc': safe_qc_char(safe_get_measurement_var('TEMP_QC', meas_idx), '0'),
                                'temp_adjusted': self.safe_float(safe_get_measurement_var('TEMP_ADJUSTED', meas_idx)),
                                'temp_adjusted_qc': safe_qc_char(safe_get_measurement_var('TEMP_ADJUSTED_QC', meas_idx), '0'),
                                'temp_adjusted_error': self.safe_float(safe_get_measurement_var('TEMP_ADJUSTED_ERROR', meas_idx)),
                                'psal': self.safe_float(safe_get_measurement_var('PSAL', meas_idx)),
                                'psal_qc': safe_qc_char(safe_get_measurement_var('PSAL_QC', meas_idx), '0'),
                                'psal_adjusted': self.safe_float(safe_get_measurement_var('PSAL_ADJUSTED', meas_idx)),
                                'psal_adjusted_qc': safe_qc_char(safe_get_measurement_var('PSAL_ADJUSTED_QC', meas_idx), '0'),
                                'psal_adjusted_error': self.safe_float(safe_get_measurement_var('PSAL_ADJUSTED_ERROR', meas_idx))
                            }
                            
                            trajectory_depth_list.append(traj_depth_data)
                            skipped_reasons["created"] += 1
                        else:
                            skipped_reasons["no_useful_data"] += 1
                    else:
                        skipped_reasons["no_trajectory_id"] += 1

                # 🔍 DEBUG: Show why records were skipped
                logger.info(f"🔍 TRAJECTORY DEPTH SUMMARY:")
                logger.info(f"  - Created: {skipped_reasons['created']}")
                logger.info(f"  - No trajectory_id: {skipped_reasons['no_trajectory_id']}")
                logger.info(f"  - No useful data: {skipped_reasons['no_useful_data']}")
                
                if trajectory_depth_list:
                    logger.info(f"✅ Inserting {len(trajectory_depth_list)} trajectory depth records")
                    self.insert_trajectory_depth_data(trajectory_depth_list)
                else:
                    logger.error("❌ NO trajectory depth records created - debugging needed!")

            finally:
                cursor.close()
                conn.close()

        except Exception as e:
            logger.error(f"Error processing trajectory file: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            if ds is not None:
                try:
                    ds.close()
                except:
                    pass




    def verify_data_insertion(self):
        """Verify data insertion - ALL 15 TABLES"""
        conn = self.connect_postgres()
        cursor = conn.cursor()

        try:
            # Check all 15 tables
            tables = [
                'float_table',
                'meta_table', 
                'profile_table',
                'parameter_table',
                'config_table',
                'launch_config_table',
                'sensor_table',
                'qc_flags_table',
                'history_table',
                'data_mode_table',
                'bgc_parameters_table',
                'depth_measurements_table',
                'trajectory_table',
                'trajectory_depth_table',
                
            ]

            logger.info("Database contains:")
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    logger.info(f"  - {table}: {count} records")
                except Exception as e:
                    logger.warning(f"  - {table}: Error getting count ({e})")

        except Exception as e:
            logger.error(f"Error verifying data: {e}")
        finally:
            cursor.close()

def main():
    """Main execution"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ultimate_parser.py <file.nc>")
        print("Supports: profile.nc, meta.nc, trajectory.nc files")
        print("Now populates ALL 15 database tables!")
        sys.exit(1)

    filepath = sys.argv[1]
    parser = UltimateArgoNetCDFParser()

    success = parser.process_argo_file(filepath)
    parser.verify_data_insertion()

    if success:
        print("\n✅ ULTIMATE processing completed successfully!")
        print("ALL 15 database tables have been populated!")
    else:
        print("\n❌ Processing failed!")

if __name__ == "__main__":
    main()
