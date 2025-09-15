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

def parse_argo_meta_file(filepath):
    """Complete ARGO Meta File Parser - FIXED VERSION"""
    
    print("=" * 100)
    print("🔍 COMPLETE ARGO META NETCDF DATASET EXPLORATION")
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
    
    # 3. CATEGORIZE VARIABLES
    platform_vars = []
    parameter_vars = []
    sensor_vars = []
    config_vars = []
    launch_config_vars = []
    history_vars = []
    calib_vars = []
    other_vars = []
    
    for var_name in ds.variables:
        var_upper = var_name.upper()
        if any(x in var_upper for x in ['PLATFORM', 'PROJECT', 'PI_', 'DATA_', 'WMO', 'BATTERY', 'FLOAT', 'LAUNCH_DATE', 'LAUNCH_LAT', 'LAUNCH_LON']):
            platform_vars.append(var_name)
        elif var_upper.startswith('PARAMETER'):
            parameter_vars.append(var_name)
        elif var_upper.startswith('SENSOR'):
            sensor_vars.append(var_name)
        elif var_upper.startswith('CONFIG') and not var_upper.startswith('CONFIG_'):
            config_vars.append(var_name)
        elif var_upper.startswith('LAUNCH_CONFIG'):
            launch_config_vars.append(var_name)
        elif var_upper.startswith('HISTORY'):
            history_vars.append(var_name)
        elif any(x in var_upper for x in ['CALIB', 'COEF', 'EQUATION']):
            calib_vars.append(var_name)
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
                    
                    print(f"📌 {var_name:30} | Shape: {str(var.shape):15}")
                    print(f"   {'':30} | Description: {description}")
                    print(f"   {'':30} | Values: {format_value_display(values)}")
                    print()
                except Exception as e:
                    print(f"📌 {var_name:30} | ERROR: {e}")
                    print()
    
    # Display all categories
    display_variable_category("PLATFORM & METADATA VARIABLES", platform_vars, "🏢")
    display_variable_category("PARAMETER VARIABLES", parameter_vars, "🔬")
    display_variable_category("SENSOR VARIABLES", sensor_vars, "🛠️")
    display_variable_category("LAUNCH CONFIG VARIABLES", launch_config_vars, "⚙️")
    display_variable_category("CONFIG VARIABLES", config_vars, "📋")
    display_variable_category("HISTORY VARIABLES", history_vars, "📜")
    display_variable_category("CALIBRATION VARIABLES", calib_vars, "🔧")
    display_variable_category("OTHER VARIABLES", other_vars, "📦")
    
    # 5. DETAILED ANALYSIS OF KEY ARRAYS
    print(f"\n🎯 DETAILED ARRAY ANALYSIS:")
    print("-" * 80)
    
    try:
        # Analyze Parameters
        if 'PARAMETER' in ds.variables and 'PARAMETER_SENSOR' in ds.variables:
            print("🔬 PARAMETER-SENSOR MAPPING:")
            params = safe_decode(ds['PARAMETER'].values)
            sensors = safe_decode(ds['PARAMETER_SENSOR'].values)
            
            if isinstance(params, list) and isinstance(sensors, list):
                for i, (param, sensor) in enumerate(zip(params, sensors)):
                    print(f"   {i+1:2}. {param:15} → {sensor}")
            print()
    except Exception as e:
        print(f"Error analyzing parameters: {e}")
    
    try:
        # Analyze Sensors
        if 'SENSOR' in ds.variables:
            print("🛠️  SENSOR DETAILS:")
            sensors = safe_decode(ds['SENSOR'].values)
            sensor_makers = safe_decode(ds['SENSOR_MAKER'].values) if 'SENSOR_MAKER' in ds.variables else []
            sensor_models = safe_decode(ds['SENSOR_MODEL'].values) if 'SENSOR_MODEL' in ds.variables else []
            
            if isinstance(sensors, list):
                for i, sensor in enumerate(sensors):
                    maker = sensor_makers[i] if i < len(sensor_makers) else 'Unknown'
                    model = sensor_models[i] if i < len(sensor_models) else 'Unknown'
                    print(f"   {i+1:2}. {sensor:20} | Maker: {maker:15} | Model: {model}")
            print()
    except Exception as e:
        print(f"Error analyzing sensors: {e}")
    
    try:
        # Analyze Launch Config
        if 'LAUNCH_CONFIG_PARAMETER_NAME' in ds.variables:
            print("⚙️  LAUNCH CONFIGURATION:")
            config_names = safe_decode(ds['LAUNCH_CONFIG_PARAMETER_NAME'].values)
            config_values = safe_decode(ds['LAUNCH_CONFIG_PARAMETER_VALUE'].values) if 'LAUNCH_CONFIG_PARAMETER_VALUE' in ds.variables else []
            
            if isinstance(config_names, list):
                for i, name in enumerate(config_names):
                    value = config_values[i] if i < len(config_values) else 'No value'
                    print(f"   {name:30} = {value}")
            print()
    except Exception as e:
        print(f"Error analyzing launch config: {e}")
    
    # 6. SUMMARY STATISTICS
    print(f"\n📊 SUMMARY STATISTICS:")
    print("-" * 80)
    print(f"Platform Variables:      {len(platform_vars)}")
    print(f"Parameter Variables:     {len(parameter_vars)}")
    print(f"Sensor Variables:        {len(sensor_vars)}")
    print(f"Launch Config Variables: {len(launch_config_vars)}")
    print(f"Config Variables:        {len(config_vars)}")
    print(f"History Variables:       {len(history_vars)}")
    print(f"Calibration Variables:   {len(calib_vars)}")
    print(f"Other Variables:         {len(other_vars)}")
    print(f"Total Variables:         {len(ds.variables)}")
    
    ds.close()
    print("\n✅ Meta file analysis complete!")

# Usage
if __name__ == "__main__":
    # Replace with your meta file path
    meta_file_path = "13859_meta.nc"
    parse_argo_meta_file(meta_file_path)
