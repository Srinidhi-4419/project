#!/usr/bin/env python3
"""
RAG-Enhanced Graph Generator for Argo Dashboard
"""

import re
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import numpy as np
from typing import Dict, Any, List, Optional, Union

class ArgoGraphGenerator:
    """RAG-Enhanced Graph Generator - Main class for dashboard"""
    
    def __init__(self, db_connection_func):
        self.get_db_connection = db_connection_func
        
        # Plot type detection patterns
        self.plot_types = {
            'scatter': ['scatter', 'point', 'correlation'],
            'line': ['line', 'profile', 'vs depth', 'vs pressure'],  
            'heatmap': ['heatmap', 'heat map', 'density'],
            'histogram': ['histogram', 'distribution', 'hist'],
            'box': ['box plot', 'box', 'quartile'],
            'bar': ['bar chart', 'bar', 'count by']
        }
        
        # Variable labels for proper axis naming
        self.label_mapping = {
            'temp': 'Temperature (°C)',
            'psal': 'Salinity (PSU)', 
            'pres': 'Pressure (dbar)',
            'latitude': 'Latitude (°)',
            'longitude': 'Longitude (°)',
            'juld': 'Date',
            'cycle_number': 'Cycle Number',
            'platform_number': 'Float ID'
        }
    
    def generate_graph(self, user_request: str):
        """Main method - integrates with RAG system for SQL generation"""
        st.markdown(f"### 🔍 Processing Request: *{user_request}*")
        
        try:
            # Check if RAG system is available
            if 'rag_system' not in st.session_state or st.session_state.rag_system is None:
                st.error("❌ RAG system not available. Please initialize it first.")
                return self.fallback_simple_generator(user_request)
            
            # 1. ✅ Use RAG system for SQL generation
            st.info("🧠 Using RAG system to generate SQL...")
            rag_result = st.session_state.rag_system.generate_enhanced_sql(
                user_request, 
                show_details=False
            )
            
            if not rag_result.get('success', False):
                st.error(f"❌ SQL generation failed: {rag_result.get('error', 'Unknown error')}")
                return self.fallback_simple_generator(user_request)
                
            sql_query = rag_result.get('sql_query', '')
            
            if not sql_query:
                st.error("❌ No SQL query generated")
                return self.fallback_simple_generator(user_request)
            
            # 2. ✅ Show generated SQL
            st.success("✅ SQL generated successfully!")
            with st.expander("📋 Generated SQL Query", expanded=False):
                st.code(sql_query, language='sql')
                
            # 3. ✅ Execute the SQL
            data = self.execute_query(sql_query)
            
            if data.empty:
                st.error("❌ No data returned from query")
                return None
                
            # 4. ✅ Detect plot type and create visualization
            plot_type = self.detect_plot_type(user_request)
            st.info(f"📊 Detected plot type: {plot_type}")
            
            # 5. ✅ Analyze data and create plot
            st.success(f"📈 Data columns: {list(data.columns)} ({len(data)} rows)")
            
            fig = self.create_smart_plot(data, plot_type, user_request)
            
            if fig:
                st.plotly_chart(fig, use_container_width=True)
                return fig
            else:
                st.error("❌ Failed to create plot")
                return None
                
        except Exception as e:
            st.error(f"❌ Error generating graph: {e}")
            return self.fallback_simple_generator(user_request)
    
    def fallback_simple_generator(self, user_request: str):
        """Fallback method when RAG system fails"""
        st.warning("⚠️ Using fallback simple graph generator...")
        
        # Extract float number if present
        float_match = re.search(r'\b(\d{5,7})\b', user_request)
        platform_filter = float_match.group(1) if float_match else None
        
        # Simple variable detection
        if 'temp' in user_request.lower() and 'sal' in user_request.lower():
            x_var, y_var = 'temp', 'psal'
        elif 'temp' in user_request.lower() and ('depth' in user_request.lower() or 'pres' in user_request.lower()):
            x_var, y_var = 'temp', 'pres'
        else:
            x_var, y_var = 'temp', 'psal'  # Default
        
        # Build simple SQL
        sql = f"""
        SELECT {x_var}, {y_var}, platform_number
        FROM depth_measurements_table 
        WHERE {x_var} IS NOT NULL AND {y_var} IS NOT NULL
        """
        
        if x_var in ['temp', 'psal']:
            sql += f" AND {x_var}_qc = '1'"
        if y_var in ['temp', 'psal']:
            sql += f" AND {y_var}_qc = '1'"
            
        if platform_filter:
            sql += f" AND platform_number = '{platform_filter}'"
            
        sql += f" ORDER BY {x_var} LIMIT 1000"
        
        # Execute and plot
        data = self.execute_query(sql)
        if not data.empty:
            plot_type = self.detect_plot_type(user_request)
            fig = self.create_simple_plot(data, x_var, y_var, plot_type)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
                return fig
        
        return None
    
    def detect_plot_type(self, request: str) -> str:
        """Detect plot type from user request"""
        request_lower = request.lower()
        
        for plot_type, keywords in self.plot_types.items():
            if any(keyword in request_lower for keyword in keywords):
                return plot_type
                
        # Smart defaults
        if 'vs depth' in request_lower or 'vs pressure' in request_lower:
            return 'line'
        elif 'distribution' in request_lower:
            return 'histogram' 
        else:
            return 'scatter'
    
    def create_smart_plot(self, data: pd.DataFrame, plot_type: str, original_request: str):
        """Create plot from RAG-generated data"""
        columns = data.columns.tolist()
        
        # Auto-detect variables from returned data
        x_var, y_var, color_var = self.analyze_columns(columns)
        
        if not x_var:
            st.error("❌ Could not determine variables for plotting")
            return None
        
        return self.create_plot(data, x_var, y_var, color_var, plot_type, original_request)
    
    def analyze_columns(self, columns: List[str]) -> tuple:
        """Analyze columns to determine best X, Y, and color variables"""
        x_var = y_var = color_var = None
        
        # Priority order for X variable
        x_priorities = ['temp', 'psal', 'latitude', 'longitude', 'juld']
        for var in x_priorities:
            if var in columns:
                x_var = var
                break
        
        # Priority order for Y variable (different from X)
        y_priorities = ['pres', 'psal', 'temp', 'latitude', 'longitude']
        for var in y_priorities:
            if var in columns and var != x_var:
                y_var = var
                break
        
        # Color variable
        if 'platform_number' in columns:
            color_var = 'platform_number'
        
        # Fallback to first numeric columns
        if not x_var:
            numeric_cols = [col for col in columns if data[col].dtype in ['int64', 'float64']]
            if numeric_cols:
                x_var = numeric_cols[0]
                if len(numeric_cols) > 1:
                    y_var = numeric_cols[1]
        
        return x_var, y_var, color_var
    
    def create_plot(self, data: pd.DataFrame, x_var: str, y_var: str, 
                   color_var: str, plot_type: str, original_request: str):
        """Create the actual plot"""
        try:
            # Generate title and labels
            title = self.generate_title(original_request, x_var, y_var)
            x_label = self.label_mapping.get(x_var, x_var.title())
            y_label = self.label_mapping.get(y_var, y_var.title()) if y_var else ""
            
            labels = {x_var: x_label}
            if y_var:
                labels[y_var] = y_label
            
            # Create appropriate plot
            if plot_type == 'scatter' and y_var:
                fig = px.scatter(data, x=x_var, y=y_var, color=color_var,
                               title=title, labels=labels)
                               
            elif plot_type == 'line' and y_var:
                fig = px.line(data, x=x_var, y=y_var, color=color_var,
                            title=title, labels=labels)
                            
            elif plot_type == 'histogram':
                fig = px.histogram(data, x=x_var, color=color_var,
                                 title=title, labels=labels)
                                 
            elif plot_type == 'box' and color_var:
                fig = px.box(data, x=color_var, y=x_var, title=title, labels=labels)
                
            elif plot_type == 'heatmap' and y_var and len(data) > 20:
                fig = px.density_heatmap(data, x=x_var, y=y_var, title=title, labels=labels)
                
            else:
                # Fallback to scatter or histogram
                if y_var:
                    fig = px.scatter(data, x=x_var, y=y_var, color=color_var,
                                   title=title, labels=labels)
                else:
                    fig = px.histogram(data, x=x_var, color=color_var,
                                     title=title, labels=labels)
            
            # Apply oceanographic conventions
            if y_var in ['pres', 'pressure', 'depth']:
                fig.update_yaxes(autorange="reversed")
            
            return fig
            
        except Exception as e:
            st.error(f"Plot creation error: {e}")
            return None
    
    def create_simple_plot(self, data: pd.DataFrame, x_var: str, y_var: str, plot_type: str):
        """Simple plot creation for fallback"""
        x_label = self.label_mapping.get(x_var, x_var.title())
        y_label = self.label_mapping.get(y_var, y_var.title())
        
        if plot_type == 'line':
            fig = px.line(data, x=x_var, y=y_var, 
                         labels={x_var: x_label, y_var: y_label})
        else:
            fig = px.scatter(data, x=x_var, y=y_var,
                           labels={x_var: x_label, y_var: y_label})
        
        if y_var == 'pres':
            fig.update_yaxes(autorange="reversed")
            
        return fig
    
    def execute_query(self, sql_query: str) -> pd.DataFrame:
        """Execute SQL query and return DataFrame"""
        try:
            conn = self.get_db_connection()
            if conn is None:
                st.error("❌ Database connection failed")
                return pd.DataFrame()
                
            df = pd.read_sql_query(sql_query, conn)
            conn.close()
            return df
            
        except Exception as e:
            st.error(f"❌ Database query error: {e}")
            return pd.DataFrame()
    
    def generate_title(self, request: str, x_var: str, y_var: str) -> str:
        """Generate appropriate plot title"""
        if len(request) < 60:
            return request.title()
        else:
            x_label = self.label_mapping.get(x_var, x_var.title())
            y_label = self.label_mapping.get(y_var, y_var.title()) if y_var else ''
            
            if y_var:
                return f"{y_label} vs {x_label}"
            else:
                return f"{x_label} Distribution"

# For backward compatibility, create an alias
RAGEnhancedGraphGenerator = ArgoGraphGenerator
