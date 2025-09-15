import xarray as xr
import numpy as np

# Load the NetCDF file
ds = xr.open_dataset("13859_meta.nc")
# print(ds["PROJECT_NAME"].values[:10])
# print(ds["WMO_INST_TYPE"].values[:10])
# print(ds["POSITIONING_SYSTEM"].values[:10])
print(ds["END_MISSION_DATE"].values)
print("="*80)
print("🔍 COMPLETE ARGO NETCDF DATASET EXPLORATION")
print("="*80)

# 1. BASIC DATASET INFO
print("\n📊 DATASET OVERVIEW:")
print(f"File: 1902676_meta.nc")
print(f"Dimensions: {dict(ds.dims)}")

# 2. ALL VARIABLES AND THEIR PROPERTIES
print("\n📋 ALL VARIABLES IN DATASET:")
print("-" * 60)

for var_name in ds.variables:
    var = ds[var_name]
    description = var.attrs.get('long_name', var.attrs.get('standard_name', 'No description'))
    units = var.attrs.get('units', 'No units')
    
    print(f"📌 {var_name:25} | Shape: {str(var.shape):15} | {description[:40]}...")
    print(f"   {'':25} | Dims:  {str(var.dims):15} | Units: {units}")
    print()

# 3. SINGLE PROFILE DATA EXTRACTION
print("\n" + "="*80)
print("🎯 SINGLE PROFILE DATA EXTRACTION (Profile Index 0)")
print("="*80)

def extract_profile_value(var, profile_idx=0):
    """Extract value for single profile"""
    try:
        if len(var.shape) == 0:  # Scalar
            return var.values.item() if hasattr(var.values, 'item') else var.values
        elif 'N_PROF' in var.dims:
            if len(var.shape) == 1:  # 1D with N_PROF
                return var.values[profile_idx]
            elif len(var.shape) == 2:  # 2D, likely N_PROF x N_LEVELS
                return var.values[profile_idx, :]
            else:  # Higher dimensions
                return var.values[profile_idx]
        else:
            return var.values  # No N_PROF dimension
    except Exception as e:
        return f"Error extracting: {e}"

def safe_decode(value):
    """Safely decode bytes to string"""
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='ignore').strip()
    elif isinstance(value, np.ndarray) and value.dtype.kind in ['S', 'U']:
        if value.size == 1:
            item = value.item()
            return item.decode('utf-8', errors='ignore').strip() if isinstance(item, bytes) else str(item).strip()
        else:
            return [item.decode('utf-8', errors='ignore').strip() if isinstance(item, bytes) else str(item).strip() 
                   for item in value.flat]
    else:
        return value

# Categorize variables
coordinate_vars = []
measurement_vars = []
qc_vars = []
metadata_vars = []
other_vars = []

for var_name in ds.variables:
    if var_name.endswith('_QC'):
        qc_vars.append(var_name)
    elif any(coord in var_name.upper() for coord in ['LAT', 'LON', 'JULD', 'PRES', 'CYCLE']):
        coordinate_vars.append(var_name)
    elif any(param in var_name.upper() for param in ['TEMP', 'PSAL', 'DOXY', 'NITRATE', 'PH', 'CHLA']):
        measurement_vars.append(var_name)
    elif any(meta in var_name.upper() for meta in ['PLATFORM', 'PROJECT', 'PI_', 'DATA_', 'HISTORY']):
        metadata_vars.append(var_name)
    else:
        other_vars.append(var_name)

# Display each category
print("\n🗺️  COORDINATE & POSITION VARIABLES:")
print("-" * 50)
for var_name in sorted(coordinate_vars):
    var = ds[var_name]
