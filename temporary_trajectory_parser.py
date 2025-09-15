import xarray as xr
import numpy as np
from datetime import datetime


def safe_decode(value):
    """Safely decode bytes to string with proper handling"""
    if value is None:
        return ''
    
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='ignore').strip()
    elif isinstance(value, np.bytes_):
        return str(value, 'utf-8', errors='ignore').strip()
    elif isinstance(value, np.ndarray):
        if value.dtype.kind in ['S', 'U', 'O']:  # String types
            if value.size == 1:
                item = value.item()
                if isinstance(item, bytes):
                    return item.decode('utf-8', errors='ignore').strip()
                else:
                    return str(item).strip()
            else:
                # Handle arrays of strings
                decoded_items = []
                for item in value.flat:
                    if isinstance(item, bytes):
                        decoded_items.append(item.decode('utf-8', errors='ignore').strip())
                    else:
                        decoded_items.append(str(item).strip())
                return decoded_items
        else:
            # Numeric arrays
            if value.size == 1:
                return value.item()
            else:
                return value.tolist()
    elif hasattr(value, 'item'):
        item_val = value.item()
        if isinstance(item_val, bytes):
            return item_val.decode('utf-8', errors='ignore').strip()
        else:
            return item_val
    else:
        return str(value).strip() if value else ''


def format_value_display(value, max_items=5):
    """Format values for nice display - FIXED VERSION"""
    try:
        # Handle None or empty values
        if value is None or value == '':
            return 'None'
        
        # Handle scalars (single values)
        if np.isscalar(value) or (hasattr(value, 'shape') and value.shape == ()):
            return str(value)
        
        # Handle lists and arrays
        if isinstance(value, (list, tuple)):
            if len(value) > max_items:
                preview = value[:max_items]
                return f"{preview}... ({len(value)} total items)"
            else:
                return str(value)
        
        # Handle numpy arrays
        elif isinstance(value, np.ndarray):
            if value.size == 1:
                return str(value.item())
            elif value.size > max_items:
                preview = value.flat[:max_items]
                return f"{list(preview)}... ({value.size} total items)"
            else:
                return str(value.tolist())
        
        # Handle other types
        else:
            return str(value)
            
    except Exception as e:
        return f"Error displaying value: {e}"


def parse_argo_trajectory_file(filepath):
    """Complete ARGO Trajectory File Parser"""
    
    print("=" * 100)
    print("🌊 COMPLETE ARGO TRAJECTORY NETCDF DATASET EXPLORATION")
    print("=" * 100)
    print(f"📁 File: {filepath}")
    
    # Load the NetCDF file
    ds = xr.open_dataset(filepath)
    
    # 1. BASIC DATASET INFO
    print(f"\n📊 DATASET OVERVIEW:")
    print(f"Dimensions: {dict(ds.dims)}")
    print(f"Total Variables: {len(ds.variables)}")
    
    # 2. GLOBAL ATTRIBUTES
    print(f"\n🌍 GLOBAL ATTRIBUTES:")
    print("-" * 80)
    for attr_name, attr_value in ds.attrs.items():
        decoded_value = safe_decode(attr_value)
        display_value = format_value_display(decoded_value)
        print(f"📌 {attr_name:30} = {display_value}")
    
    # 3. CATEGORIZE TRAJECTORY VARIABLES
    platform_vars = []
    trajectory_vars = []
    measurement_vars = []
    position_vars = []
    time_vars = []
    qc_vars = []
    config_vars = []
    technical_vars = []
    other_vars = []
    
    for var_name in ds.variables:
        var_upper = var_name.upper()
        if any(x in var_upper for x in ['PLATFORM', 'DATA_', 'FORMAT']):
            platform_vars.append(var_name)
        elif any(x in var_upper for x in ['TRAJ', 'CYCLE']):
            trajectory_vars.append(var_name)
        elif any(x in var_upper for x in ['PRES', 'TEMP', 'PSAL', 'MEAS']):
            measurement_vars.append(var_name)
        elif any(x in var_upper for x in ['LATITUDE', 'LONGITUDE', 'POSITION']):
            position_vars.append(var_name)
        elif any(x in var_upper for x in ['JULD', 'TIME']):
            time_vars.append(var_name)
        elif var_upper.endswith('_QC') or 'QC' in var_upper:
            qc_vars.append(var_name)
        elif var_upper.startswith('CONFIG'):
            config_vars.append(var_name)
        elif any(x in var_upper for x in ['TECHNICAL', 'GROUNDED']):
            technical_vars.append(var_name)
        else:
            other_vars.append(var_name)
    
    # 4. DISPLAY EACH CATEGORY WITH VALUES
    
    def display_variable_category(category_name, var_list, emoji):
        """Helper function to display a category of variables"""
        if not var_list:
            return
            
        print(f"\n{emoji} {category_name}:")
        print("-" * 80)
        for var_name in sorted(var_list):
            if var_name in ds.variables:
                try:
                    var = ds[var_name]
                    values = safe_decode(var.values)
                    description = var.attrs.get('long_name', var.attrs.get('standard_name', 'No description'))
                    units = var.attrs.get('units', 'No units')
                    
                    print(f"📌 {var_name:30} | Shape: {str(var.shape):15}")
                    print(f"   {'':30} | Description: {description}")
                    print(f"   {'':30} | Units: {units}")
                    print(f"   {'':30} | Values: {format_value_display(values)}")
                    print()
                except Exception as e:
                    print(f"📌 {var_name:30} | ERROR: {e}")
                    print()
    
    # Display all categories
    display_variable_category("PLATFORM & METADATA VARIABLES", platform_vars, "🏢")
    display_variable_category("TRAJECTORY VARIABLES", trajectory_vars, "🎯")
    display_variable_category("MEASUREMENT VARIABLES", measurement_vars, "🔬")
    display_variable_category("POSITION VARIABLES", position_vars, "🌍")
    display_variable_category("TIME VARIABLES", time_vars, "⏰")
    display_variable_category("QUALITY CONTROL VARIABLES", qc_vars, "✅")
    display_variable_category("CONFIG VARIABLES", config_vars, "📋")
    display_variable_category("TECHNICAL VARIABLES", technical_vars, "🔧")
    display_variable_category("OTHER VARIABLES", other_vars, "📦")
    
    # 5. DETAILED ANALYSIS OF KEY TRAJECTORY DATA
    print(f"\n🎯 DETAILED TRAJECTORY ANALYSIS:")
    print("-" * 80)
    
    try:
        # Analyze Platform Info
        if 'PLATFORM_NUMBER' in ds.variables:
            platform_number = safe_decode(ds['PLATFORM_NUMBER'].values)
            print(f"🏢 PLATFORM NUMBER: {platform_number}")
            print()
    except Exception as e:
        print(f"Error analyzing platform: {e}")
    
    try:
        # Analyze Trajectory Dimensions
        if 'N_MEASUREMENT' in ds.dims:
            n_measurements = ds.dims['N_MEASUREMENT']
            print(f"📊 TRAJECTORY MEASUREMENTS: {n_measurements} total measurements")
            
        if 'N_CYCLE' in ds.dims:
            n_cycles = ds.dims['N_CYCLE']
            print(f"📊 TRAJECTORY CYCLES: {n_cycles} total cycles")
            print()
    except Exception as e:
        print(f"Error analyzing trajectory dimensions: {e}")
    
    try:
        # Analyze Position Data
        if 'LATITUDE' in ds.variables and 'LONGITUDE' in ds.variables:
            print("🌍 POSITION DATA SAMPLE (first 5 points):")
            lat_data = ds['LATITUDE'].values
            lon_data = ds['LONGITUDE'].values
            
            for i in range(min(5, len(lat_data))):
                if not np.isnan(lat_data[i]) and not np.isnan(lon_data[i]):
                    print(f"   Point {i+1:2}: Lat {lat_data[i]:8.4f}°, Lon {lon_data[i]:8.4f}°")
            print()
    except Exception as e:
        print(f"Error analyzing position data: {e}")
    
    try:
        # Analyze Time Data
        if 'JULD' in ds.variables:
            print("⏰ TIME DATA SAMPLE (first 5 points):")
            time_data = ds['JULD'].values
            time_ref = ds['JULD'].attrs.get('units', 'days since 1950-01-01T00:00:00Z')
            
            print(f"   Time Reference: {time_ref}")
            for i in range(min(5, len(time_data))):
                if not np.isnan(time_data[i]):
                    print(f"   Time {i+1:2}: {time_data[i]:.6f}")
            print()
    except Exception as e:
        print(f"Error analyzing time data: {e}")
    
    try:
        # Analyze Measurement Data
        measurement_params = ['PRES', 'TEMP', 'PSAL']
        available_params = [param for param in measurement_params if param in ds.variables]
        
        if available_params:
            print("🔬 MEASUREMENT DATA SAMPLE (first 5 non-NaN values):")
            for param in available_params:
                param_data = ds[param].values
                valid_data = param_data[~np.isnan(param_data)]
                units = ds[param].attrs.get('units', 'unknown units')
                
                print(f"   {param:4} ({units}): ", end="")
                if len(valid_data) > 0:
                    sample_size = min(5, len(valid_data))
                    sample_values = [f"{val:.3f}" for val in valid_data[:sample_size]]
                    print(f"{', '.join(sample_values)}")
                else:
                    print("No valid data")
            print()
    except Exception as e:
        print(f"Error analyzing measurement data: {e}")
    
    try:
        # Analyze Configuration Parameters
        if 'CONFIG_MISSION_NUMBER' in ds.variables:
            print("📋 CONFIGURATION INFO:")
            config_mission = safe_decode(ds['CONFIG_MISSION_NUMBER'].values)
            print(f"   Mission Number: {format_value_display(config_mission)}")
            print()
    except Exception as e:
        print(f"Error analyzing configuration: {e}")
    
    # 6. SUMMARY STATISTICS
    print(f"\n📊 SUMMARY STATISTICS:")
    print("-" * 80)
    print(f"Platform Variables:      {len(platform_vars)}")
    print(f"Trajectory Variables:    {len(trajectory_vars)}")
    print(f"Measurement Variables:   {len(measurement_vars)}")
    print(f"Position Variables:      {len(position_vars)}")
    print(f"Time Variables:          {len(time_vars)}")
    print(f"Quality Control Variables: {len(qc_vars)}")
    print(f"Config Variables:        {len(config_vars)}")
    print(f"Technical Variables:     {len(technical_vars)}")
    print(f"Other Variables:         {len(other_vars)}")
    print(f"Total Variables:         {len(ds.variables)}")
    
    # 7. DATA QUALITY OVERVIEW
    print(f"\n✅ DATA QUALITY OVERVIEW:")
    print("-" * 80)
    
    # Check for key trajectory variables
    key_vars = ['LATITUDE', 'LONGITUDE', 'JULD', 'PRES']
    for var in key_vars:
        if var in ds.variables:
            data = ds[var].values
            valid_count = np.sum(~np.isnan(data))
            total_count = len(data)
            coverage = (valid_count / total_count) * 100 if total_count > 0 else 0
            print(f"   {var:10}: {valid_count:5}/{total_count:5} valid ({coverage:5.1f}% coverage)")
    
    ds.close()
    print("\n✅ Trajectory file analysis complete!")


# Usage
if __name__ == "__main__":
    # Replace with your trajectory file path
    trajectory_file_path = "13859_Rtraj.nc"
    parse_argo_trajectory_file(trajectory_file_path)
