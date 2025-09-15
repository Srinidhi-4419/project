#!/usr/bin/env python3
"""
Super Fixed Argo Graph Generator - Bulletproof Float Filtering
This version will DEFINITELY filter to only the requested float
"""

import re
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
from configparser import ConfigParser
import streamlit as st
from typing import Dict, Any, List, Tuple, Optional

class ArgoGraphGenerator:
    """Super fixed graph generator with bulletproof float filtering"""

    def __init__(self, db_connection_func):
        self.get_db_connection = db_connection_func

        # Variable mappings
        self.variable_mappings = {
            'temp': 'temp', 'temperature': 'temp',
            'sal': 'psal', 'salinity': 'psal',
            'press': 'pres', 'pressure': 'pres', 'depth': 'pres',
            'time': 'juld', 'date': 'juld',
            'lat': 'latitude', 'latitude': 'latitude',
            'lon': 'longitude', 'longitude': 'longitude',
            'cycle': 'cycle_number', 'float': 'platform_number'
        }

        # Unit mappings for labels
        self.unit_mappings = {
            'temp': 'Temperature (°C)', 'pres': 'Pressure (dbar)',
            'psal': 'Salinity (PSU)', 'juld': 'Date',
            'latitude': 'Latitude (°)', 'longitude': 'Longitude (°)',
            'cycle_number': 'Cycle Number', 'platform_number': 'Float ID'
        }

    def execute_query(self, sql_query: str) -> pd.DataFrame:
        """Execute SQL query and return DataFrame"""
        try:
            conn = self.get_db_connection()
            df = pd.read_sql_query(sql_query, conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"Database query error: {e}")
            return pd.DataFrame()

    def extract_float_numbers(self, request: str) -> List[str]:
        """Extract ALL float numbers from request - BULLETPROOF VERSION"""
        request_clean = request.strip()
        float_numbers = []

        # Super comprehensive patterns
        patterns = [
            r'\bfor\s+(\d{4,7})\b',           # "for 1900122"
            r'\bfloat\s+(\d{4,7})\b',        # "float 1900122"  
            r'\bplatform\s+(\d{4,7})\b',     # "platform 1900122"
            r'\b(\d{7})\b',                   # "1900122" (7-digit standalone)
            r'\b(\d{5})\b'                    # "13859" (5-digit standalone)
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, request_clean, re.IGNORECASE)
            for match in matches:
                float_num = match.group(1)
                if float_num not in float_numbers:
                    float_numbers.append(float_num)

        return float_numbers

    def parse_graph_request(self, request: str) -> Dict[str, Any]:
        """Parse request with SUPER STRICT float filtering"""
        request_lower = request.lower().strip()

        # Detect graph type
        graph_type = 'scatter' if 'scatter' in request_lower else 'line'

        # Extract variables
        x_var, y_var = self.extract_variables(request_lower)

        # Extract float numbers - MULTIPLE DETECTION METHODS
        float_numbers = self.extract_float_numbers(request)

        # Show what we detected
        if float_numbers:
            st.success(f"🎯 **Detected Float Filter(s):** {float_numbers}")
            st.info(f"📊 **Will show ONLY data from these floats**")
        else:
            st.warning("⚠️ **No specific float detected** - showing all floats")

        return {
            'graph_type': graph_type,
            'x_variable': x_var,
            'y_variable': y_var,
            'float_filter': float_numbers[0] if float_numbers else None,  # Use first detected
            'all_float_filters': float_numbers,
            'title': self.generate_title(request, x_var, y_var, float_numbers)
        }

    def extract_variables(self, request: str) -> Tuple[str, str]:
        """Extract variables from request"""

        # Temperature vs Salinity
        if 'temp' in request and 'sal' in request:
            return 'temp', 'psal'

        # Temperature vs Pressure/Depth
        elif 'temp' in request and ('press' in request or 'depth' in request):
            return 'temp', 'pres'

        # Salinity vs Pressure/Depth  
        elif 'sal' in request and ('press' in request or 'depth' in request):
            return 'psal', 'pres'

        # Default
        else:
            return 'temp', 'psal'

    def generate_title(self, request: str, x_var: str, y_var: str, float_numbers: List[str]) -> str:
        """Generate title with float info"""
        x_label = self.unit_mappings.get(x_var, x_var.title())
        y_label = self.unit_mappings.get(y_var, y_var.title())

        if 'scatter' in request.lower():
            base_title = f"{y_label} vs {x_label} (Scatter Plot)"
        else:
            base_title = f"{y_label} vs {x_label}"

        if float_numbers:
            if len(float_numbers) == 1:
                base_title += f" - Float {float_numbers[0]}"
            else:
                base_title += f" - Floats {', '.join(float_numbers)}"

        return base_title

    def build_sql_query(self, params: Dict[str, Any]) -> str:
        """Build SQL with SUPER STRICT float filtering"""
        x_var = params['x_variable']
        y_var = params['y_variable']
        float_filter = params['float_filter']

        # Base query for depth measurements
        base_query = f"""
        SELECT d.{x_var}, d.{y_var}, d.platform_number
        FROM depth_measurements_table d
        WHERE d.{x_var} IS NOT NULL 
          AND d.{y_var} IS NOT NULL
        """

        # Add quality control
        if x_var in ['temp', 'psal']:
            base_query += f" AND d.{x_var}_qc = '1'"
        if y_var in ['temp', 'psal']:
            base_query += f" AND d.{y_var}_qc = '1'"

        # SUPER STRICT FLOAT FILTERING
        if float_filter:
            base_query += f" AND d.platform_number = '{float_filter}'"
            st.success(f"✅ **SQL Filter Applied:** AND platform_number = '{float_filter}'")

        base_query += f" ORDER BY d.{x_var} LIMIT 1000"

        return base_query

    def create_graph(self, params: Dict[str, Any], data: pd.DataFrame):
        """Create graph with data validation"""
        if data.empty:
            st.error("❌ No data found after filtering!")
            if params['float_filter']:
                st.info(f"💡 Float {params['float_filter']} might not have {params['x_variable']}/{params['y_variable']} data")
            return None

        # VALIDATE FLOAT FILTERING
        unique_floats = data['platform_number'].unique()
        expected_float = params['float_filter']

        if expected_float and expected_float not in unique_floats:
            st.error(f"❌ **FILTERING FAILED!** Expected float {expected_float} but got {list(unique_floats)}")
            return None

        if expected_float and len(unique_floats) > 1:
            st.error(f"❌ **MULTIPLE FLOATS DETECTED!** Expected only {expected_float} but got {list(unique_floats)}")
            # FORCE filter the data
            data = data[data['platform_number'] == expected_float]
            unique_floats = data['platform_number'].unique()
            st.success(f"✅ **FORCED FILTERING:** Now showing only {list(unique_floats)}")

        # Show final data summary
        st.success(f"📊 **Final Data:** {len(data)} points from float(s): {list(unique_floats)}")

        x_var = params['x_variable']
        y_var = params['y_variable']
        graph_type = params['graph_type']
        title = params['title']

        x_label = self.unit_mappings.get(x_var, x_var.title())
        y_label = self.unit_mappings.get(y_var, y_var.title())

        if graph_type == 'scatter':
            fig = px.scatter(data, x=x_var, y=y_var, 
                           title=title, 
                           labels={x_var: x_label, y_var: y_label},
                           color='platform_number' if len(unique_floats) > 1 else None)
        else:
            fig = px.line(data, x=x_var, y=y_var, 
                        title=title, 
                        labels={x_var: x_label, y_var: y_label},
                        color='platform_number' if len(unique_floats) > 1 else None)

        if y_var == 'pres':
            fig.update_yaxes(autorange="reversed")

        return fig

    def generate_graph(self, request: str):
        """Main method with bulletproof filtering"""
        st.markdown(f"### 🔍 Processing Request: *{request}*")

        try:
            # Parse request
            params = self.parse_graph_request(request)

            # Build and show SQL
            sql_query = self.build_sql_query(params)

            with st.expander("📋 SQL Query Used", expanded=False):
                st.code(sql_query, language='sql')

            # Execute query
            data = self.execute_query(sql_query)

            if data.empty:
                st.error(f"❌ No data found for float {params['float_filter']}")
                return None

            # Create graph with validation
            fig = self.create_graph(params, data)

            if fig:
                st.plotly_chart(fig, use_container_width=True)
                return fig

        except Exception as e:
            st.error(f"❌ Error generating graph: {e}")
            return None
