#!/usr/bin/env python3
"""
Enhanced Argo Float Dashboard - Fixed Version
"""
import logging
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import pandas as pd
import psycopg2
from configparser import ConfigParser
import requests
import json
import tempfile
import os
import re
from typing import Dict, Any, List, Tuple, Optional

# Import your backend and file processor
try:
    from client import ArgoQueryClient, format_response
    from process import process_argo_file
    from graphgenerator import ArgoGraphGenerator
except ImportError as e:
    st.error(f"Please ensure required files are present: {e}")
    st.stop()

class EnhancedArgoStreamlitDashboard:
    """Enhanced Streamlit dashboard - fixed version"""

    def __init__(self):
        self.setup_page_config()
        self.client = self.initialize_backend()
        self.graph_generator = ArgoGraphGenerator(self.get_database_connection)

    def setup_page_config(self):
        """Configure Streamlit page with enhanced styling"""
        st.set_page_config(
            page_title="🌊 Argo Float Explorer",
            page_icon="🌊",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Enhanced Custom CSS
        st.markdown("""
        <style>
        .main-header {
            font-size: 3.5rem;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 2rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }
        .metric-container {
            background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%);
            padding: 1.5rem;
            border-radius: 15px;
            border-left: 5px solid #1f77b4;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        .metric-container:hover {
            transform: translateY(-2px);
        }
        .chat-container {
            background: linear-gradient(135deg, #ffffff 0%, #f8fbff 100%);
            padding: 2rem;
            border-radius: 20px;
            border: 1px solid #e1ecf4;
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }
        .chat-message-user {
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 20px 20px 5px 20px;
            margin: 0.5rem 0;
            max-width: 80%;
            margin-left: auto;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .chat-message-ai {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            color: #333;
            padding: 1rem 1.5rem;
            border-radius: 20px 20px 20px 5px;
            margin: 0.5rem 0;
            max-width: 80%;
            border-left: 4px solid #1f77b4;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .upload-container {
            background: linear-gradient(135deg, #e8f5e8 0%, #f0f8f0 100%);
            padding: 2rem;
            border-radius: 20px;
            border: 2px dashed #28a745;
            text-align: center;
            margin: 1rem 0;
        }
        .upload-container:hover {
            border-color: #20c997;
            background: linear-gradient(135deg, #d4edda 0%, #f0f8f0 100%);
        }
        .graph-container {
            background: linear-gradient(135deg, #fff3cd 0%, #fef8e5 100%);
            padding: 2rem;
            border-radius: 20px;
            border: 2px solid #ffc107;
            margin: 1rem 0;
        }
        .stButton > button {
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 0.5rem 2rem;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        .sidebar .stButton > button {
            width: 100%;
            margin-bottom: 0.5rem;
        }
        </style>
        """, unsafe_allow_html=True)

    def initialize_backend(self):
        """Initialize backend client"""
        PERPLEXITY_API_KEY = "UR KEY"
        try:
            return ArgoQueryClient(PERPLEXITY_API_KEY)
        except Exception as e:
            st.error(f"Backend initialization failed: {e}")
            return None

    def get_database_connection(self):
        """Get database connection for graph generator"""
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                user="postgres", 
                password="newpassword",
                database="argo_floats"
            )
            return conn
        except Exception as e:
            st.error(f"Database connection error: {e}")
            return None

    def get_database_data(self, query):
        """Execute SQL query"""
        try:
            conn = self.get_database_connection()
            result_df = pd.read_sql_query(query, conn)
            conn.close()
            return result_df
        except Exception as e:
            st.error(f"Database error: {e}")
            return pd.DataFrame()

    def render_header(self):
        """Render enhanced main header"""
        st.markdown('<h1 class="main-header">🌊 Argo Float Explorer Dashboard</h1>', 
                   unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h3 style="color: #6c757d; font-weight: 300;">
                AI-Powered Oceanographic Data Analysis & Management System
            </h3>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

    def render_overview_metrics(self):
        """Render enhanced key metrics"""
        col1, col2, col3, col4 = st.columns(4)

        # Get metrics from database
        float_count = self.get_database_data("SELECT COUNT(*) FROM float_table")
        profile_count = self.get_database_data("SELECT COUNT(*) FROM profile_table")  
        measurement_count = self.get_database_data("SELECT COUNT(*) FROM depth_measurements_table")

        with col1:
            count_val = float_count.iloc[0, 0] if not float_count.empty else "N/A"
            st.metric("🎈 Active Floats", count_val, delta="Real-time")

        with col2:
            profile_val = profile_count.iloc[0, 0] if not profile_count.empty else "N/A"
            st.metric("📊 Total Profiles", profile_val, delta="Updated")

        with col3:  
            if not measurement_count.empty and measurement_count.iloc[0, 0]:
                measure_val = f"{measurement_count.iloc[0, 0]:,}"
            else:
                measure_val = "N/A"
            st.metric("🌊 Measurements", measure_val, delta="Scientific Data")

        with col4:
            st.metric("🗺️ Ocean Coverage", "All Oceans", delta="Global")

    def render_full_width_map(self):
        """Render full-width interactive map"""
        st.subheader("🗺️ Global Float Locations & Trajectories")

        positions_query = """
        SELECT DISTINCT 
            p.platform_number,
            p.latitude,
            p.longitude,
            p.cycle_number,
            p.juld,
            COALESCE(m.platform_type, 'Unknown') as platform_type
        FROM profile_table p
        LEFT JOIN meta_table m ON p.platform_number = m.platform_number
        WHERE p.latitude IS NOT NULL AND p.longitude IS NOT NULL
        ORDER BY p.platform_number, p.cycle_number
        """

        positions_df = self.get_database_data(positions_query)

        if not positions_df.empty:
            center_lat = positions_df['latitude'].mean()
            center_lon = positions_df['longitude'].mean()

            m = folium.Map(
                location=[center_lat, center_lon], 
                zoom_start=3,
                width='100%',
                height='600px',
                tiles='CartoDB positron'
            )

            folium.TileLayer(
                'OpenStreetMap',
                name='Detailed View',
                overlay=False,
                control=True
            ).add_to(m)

            colors = ['#FF4444', '#4444FF', '#44FF44', '#FF44FF', '#FFFF44', '#FF8800', '#8800FF']

            for i, float_id in enumerate(positions_df['platform_number'].unique()):
                float_data = positions_df[positions_df['platform_number'] == float_id]
                color = colors[i % len(colors)]

                trajectory_points = [(row['latitude'], row['longitude']) 
                                   for _, row in float_data.iterrows()]

                if len(trajectory_points) > 1:
                    folium.PolyLine(
                        trajectory_points,
                        color=color,
                        weight=4,
                        opacity=0.8,
                        popup=f"🎈 Float {float_id} Trajectory ({len(trajectory_points)} points)",
                        tooltip=f"Float {float_id}"
                    ).add_to(m)

                latest_pos = float_data.iloc[-1]
                folium.Marker(
                    [latest_pos['latitude'], latest_pos['longitude']],
                    popup=folium.Popup(f"""
                    <div style="font-family: Arial; width: 200px;">
                        <h4 style="color: #1f77b4; margin: 0;">🎈 Float {latest_pos['platform_number']}</h4>
                        <hr style="margin: 5px 0;">
                        <b>Type:</b> {latest_pos['platform_type']}<br>
                        <b>Cycle:</b> {latest_pos['cycle_number']}<br>
                        <b>Date:</b> {latest_pos['juld']}<br>
                        <b>Location:</b> {latest_pos['latitude']:.3f}°, {latest_pos['longitude']:.3f}°
                    </div>
                    """, max_width=250),
                    tooltip=f"Float {latest_pos['platform_number']} - {latest_pos['platform_type']}",
                    icon=folium.Icon(
                        color='red' if i % 2 == 0 else 'blue', 
                        icon='tint',
                        prefix='fa'
                    )
                ).add_to(m)

            folium.LayerControl().add_to(m)
            st_folium(m, width=None, height=600)
        else:
            st.warning("No position data available for mapping")

    def render_graph_generator(self):
        """Render graph generator section"""
        st.markdown("""
        <div class="graph-container">
            <h2 style="color: #e67e22; margin-bottom: 1rem;">📊 Natural Language Graph Generator</h2>
            <p style="color: #6c757d; margin-bottom: 1.5rem;">
                Create professional oceanographic charts using simple natural language descriptions
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 💬 Graph Request")

        col1, col2 = st.columns([4, 1])

        with col1:
            custom_request = st.text_input(
                "Describe the graph you want:",
                placeholder="e.g., scatter plot of temp vs salinity for float 1900122",
                label_visibility="collapsed"
            )

        with col2:
            if st.button("📊 Generate", use_container_width=True):
                graph_request = custom_request

        if 'graph_request' in locals() and graph_request:
            st.markdown("---")
            self.graph_generator.generate_graph(graph_request)

        with st.expander("💡 Graph Request Examples", expanded=False):
            st.markdown("""
            **Profile Plots:**
            - `temperature vs pressure for float 13859`
            - `salinity vs depth for float 1900122`
            - `pressure profile for float 13859`

            **Time Series:**
            - `surface temperature over time`
            - `temp vs date`

            **Analysis:**
            - `scatter plot of temp vs salinity for float 1900122`
            - `histogram of temperature`
            - `temp vs pressure below 500 dbar`

            **Supported Variables:**
            - Temperature: `temp`, `temperature`
            - Salinity: `sal`, `salinity` 
            - Pressure/Depth: `press`, `pressure`, `depth`
            - Time: `time`, `date`
            """)

    def render_enhanced_ai_chat(self):
        """Render enhanced AI chat interface"""
        st.markdown("""
        <div class="chat-container">
            <h2 style="color: #1f77b4; margin-bottom: 1rem;">🤖 AI Assistant</h2>
            <p style="color: #6c757d; margin-bottom: 1.5rem;">
                Ask questions about your Argo float data using natural language. 
                The AI will generate SQL queries and provide direct answers.
            </p>
        </div>
        """, unsafe_allow_html=True)

        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = [
                {
                    'role': 'ai', 
                    'content': '👋 Welcome! I can help you explore your oceanographic data. Try asking: "What is the platform type of float 1900122?" or "How many floats are there?"'
                }
            ]

        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_history:
                if message['role'] == 'user':
                    st.markdown(f"""
                    <div class="chat-message-user">
                        <strong>You:</strong> {message['content']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message-ai">
                        <strong>🤖 AI Assistant:</strong><br>{message['content']}
                    </div>
                    """, unsafe_allow_html=True)

                    if 'sql' in message:
                        with st.expander("🔍 View Generated SQL Query", expanded=False):
                            st.code(message['sql'], language='sql')

        st.markdown("### 💬 Ask a Question")

        col1, col2 = st.columns([4, 1])

        with col1:
            user_query = st.text_input(
                "Your question:",
                placeholder="e.g., What is the platform type of float 13859?",
                label_visibility="collapsed"
            )

        with col2:
            send_button = st.button("🚀 Send", use_container_width=True)

        if send_button and user_query:
            graph_keywords = ['graph', 'plot', 'chart', 'vs', 'versus', 'histogram', 'scatter']
            if any(keyword in user_query.lower() for keyword in graph_keywords):
                st.session_state.chat_history.append({'role': 'user', 'content': user_query})

                st.session_state.chat_history.append({
                    'role': 'ai', 
                    'content': f"I'll generate a graph for you: {user_query}"
                })

                st.rerun()

                with st.spinner("🔄 Generating graph..."):
                    self.graph_generator.generate_graph(user_query)

            else:
                st.session_state.chat_history.append({'role': 'user', 'content': user_query})

                if self.client:
                    with st.spinner("🔄 Processing your query..."):
                        try:
                            result = self.client.process_query(user_query)
                            response = format_response(result)

                            ai_message = {'role': 'ai', 'content': response}
                            if result.get('sql_query'):
                                ai_message['sql'] = result['sql_query']

                            st.session_state.chat_history.append(ai_message)
                            st.rerun()

                        except Exception as e:
                            error_message = f"❌ Sorry, I encountered an error: {str(e)}"
                            st.session_state.chat_history.append({'role': 'ai', 'content': error_message})
                            st.rerun()
                else:
                    st.error("AI backend not available")

    def detect_file_type(self, filename):
        """Detect Argo file type from filename"""
        filename_lower = filename.lower()
        
        if 'meta' in filename_lower or '_meta.nc' in filename_lower:
            return "📋 Meta File"
        elif 'prof' in filename_lower or 'profile' in filename_lower or '_prof.nc' in filename_lower:
            return "📊 Profile File"
        elif 'traj' in filename_lower or 'trajectory' in filename_lower:
            return "🛰️ Trajectory File"
        else:
            return "❓ Unknown Type"

    def render_file_upload_section(self):
        """Render enhanced file upload section"""
        st.markdown("""
        <div class="upload-container">
            <h2 style="color: #28a745; margin-bottom: 1rem;">📂 File Ingestion System</h2>
            <p style="color: #6c757d; margin-bottom: 1.5rem;">
                Upload Argo NetCDF files (.nc) to automatically parse and integrate into the database
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("📚 Supported File Types", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                **📊 Profile Files**
                - `*_prof.nc`
                - `*profile*.nc`
                - Contains: Temperature, Salinity, Pressure measurements
                """)
            
            with col2:
                st.markdown("""
                **📋 Meta Files**
                - `*_meta.nc`
                - `*meta*.nc` 
                - Contains: Float metadata, sensors, parameters
                """)
            
            with col3:
                st.markdown("""
                **🛰️ Trajectory Files**
                - `*_traj.nc`
                - `*trajectory*.nc`
                - Contains: Float movement data
                """)

        uploaded_file = st.file_uploader(
            "Choose an Argo NetCDF file",
            type=['nc'],
            help="Upload prof.nc, meta.nc, traj.nc, or other Argo NetCDF files"
        )

        if uploaded_file is not None:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("📄 File Name", uploaded_file.name)

            with col2:
                file_size = len(uploaded_file.getvalue()) / 1024
                st.metric("📏 File Size", f"{file_size:.1f} KB")

            with col3:
                st.metric("📋 File Type", self.detect_file_type(uploaded_file.name))
                
            with col4:
                st.metric("📅 Format", "NetCDF")

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🚀 Process File", use_container_width=True, type="primary"):
                    self.process_uploaded_file(uploaded_file)

        if 'processing_history' in st.session_state and st.session_state.processing_history:
            st.markdown("### 📊 Processing History")
            
            history_df = pd.DataFrame(st.session_state.processing_history)
            
            def color_status(val):
                if '✅' in val:
                    return 'background-color: #d4edda; color: #155724'
                elif '❌' in val:
                    return 'background-color: #f8d7da; color: #721c24'
                return ''
            
            styled_df = history_df.style.applymap(color_status, subset=['status'])
            
            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True
            )
            
            if st.button("🗑️ Clear History"):
                st.session_state.processing_history = []
                st.rerun()

    def process_uploaded_file(self, uploaded_file):
        """Process uploaded file with proper file handling"""
        temp_filepath = None
        try:
            # Get original filename
            original_filename = uploaded_file.name
            temp_dir = tempfile.gettempdir()
            temp_filepath = os.path.join(temp_dir, original_filename)
            
            # Write file with original name
            with open(temp_filepath, 'wb') as f:
                f.write(uploaded_file.getvalue())

            with st.spinner(f"🔄 Processing {uploaded_file.name}..."):
                # Process with original filename
                result = process_argo_file(temp_filepath, verify=True, verbose=False)

            # Clean up - MOVED AFTER SUCCESS CHECK
            if 'processing_history' not in st.session_state:
                st.session_state.processing_history = []

            import datetime
            history_entry = {
                'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'filename': uploaded_file.name,
                'status': '✅ Success' if result['success'] else '❌ Failed',
                'details': 'Processed successfully' if result['success'] else result.get('error', 'Unknown error')
            }
            st.session_state.processing_history.append(history_entry)

            if result['success']:
                st.success(f"✅ Successfully processed {uploaded_file.name}!")
                
                with st.expander("📋 Processing Details", expanded=True):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write("**File Information:**")
                        st.write(f"• Original Name: {original_filename}")
                        st.write(f"• File Type: {self.detect_file_type(original_filename)}")
                        st.write(f"• Status: ✅ Processed")
                        st.write(f"• Verification: {'✅ Passed' if result.get('verification_result') else '⚠️ Skipped'}")

                    with col2:
                        st.write("**Processing Results:**")
                        if 'tables_updated' in result:
                            for table, count in result['tables_updated'].items():
                                st.write(f"• {table}: {count} records")
                        else:
                            st.write("• Data inserted into database")
                            st.write("• Refresh dashboard to see updates")

                st.balloons()
            else:
                st.error(f"❌ Failed to process {uploaded_file.name}")
                st.error(f"Error: {result.get('error', 'Unknown error')}")
                
                with st.expander("🔍 Debug Information", expanded=False):
                    st.write(f"**Original filename:** {original_filename}")
                    st.write(f"**Detected file type:** {self.detect_file_type(original_filename)}")
                    if 'traceback' in result:
                        st.code(result['traceback'], language='python')

        except Exception as e:
            st.error(f"❌ Processing error: {str(e)}")
            
            with st.expander("🔍 Error Details", expanded=False):
                import traceback
                st.code(traceback.format_exc(), language='python')
        
        finally:
            # ALWAYS clean up the temp file in the finally block
            if temp_filepath and os.path.exists(temp_filepath):
                try:
                    # Add a small delay to ensure file is closed
                    import time
                    time.sleep(0.1)
                    os.unlink(temp_filepath)
                    logger.info(f"Cleaned up temporary file: {temp_filepath}")
                except Exception as cleanup_error:
                    logger.warning(f"Could not clean up temp file {temp_filepath}: {cleanup_error}")


    def render_profile_plots(self):
        """Render temperature/salinity profiles"""
        st.subheader("📈 Temperature & Salinity Profiles")

        floats_df = self.get_database_data("SELECT DISTINCT platform_number FROM float_table ORDER BY platform_number")

        if not floats_df.empty:
            selected_float = st.selectbox("Select Float:", floats_df['platform_number'].tolist())

            if selected_float:
                col1, col2 = st.columns(2)

                with col1:
                    temp_query = f"""
                    SELECT pres, temp, temp_qc 
                    FROM depth_measurements_table 
                    WHERE platform_number = '{selected_float}' 
                    AND temp IS NOT NULL AND temp_qc = '1'
                    ORDER BY pres
                    """
                    temp_df = self.get_database_data(temp_query)

                    if not temp_df.empty:
                        fig_temp = px.line(temp_df, x='temp', y='pres', 
                                         title=f'Temperature Profile - Float {selected_float}',
                                         labels={'temp': 'Temperature (°C)', 'pres': 'Pressure (dbar)'})
                        fig_temp.update_yaxes(autorange="reversed")
                        st.plotly_chart(fig_temp, use_container_width=True)
                    else:
                        st.info("No temperature data available for this float")

                with col2:
                    sal_query = f"""
                    SELECT pres, psal, psal_qc
                    FROM depth_measurements_table 
                    WHERE platform_number = '{selected_float}'
                    AND psal IS NOT NULL AND psal_qc = '1' 
                    ORDER BY pres
                    """
                    sal_df = self.get_database_data(sal_query)

                    if not sal_df.empty:
                        fig_sal = px.line(sal_df, x='psal', y='pres',
                                        title=f'Salinity Profile - Float {selected_float}',
                                        labels={'psal': 'Salinity (PSU)', 'pres': 'Pressure (dbar)'})
                        fig_sal.update_yaxes(autorange="reversed")
                        st.plotly_chart(fig_sal, use_container_width=True)
                    else:
                        st.info("No salinity data available for this float")
        else:
            st.warning("No floats found")

    def render_time_series(self):
        """Render time series plots"""
        st.subheader("📊 Time Series Analysis")

        surface_query = """
        SELECT 
            p.juld::date as date,
            AVG(d.temp) as avg_surface_temp,
            COUNT(*) as measurement_count
        FROM depth_measurements_table d
        JOIN profile_table p ON d.platform_number = p.platform_number AND d.cycle_number = p.cycle_number
        WHERE d.pres < 10 AND d.temp IS NOT NULL AND d.temp_qc = '1'
        GROUP BY p.juld::date
        ORDER BY date
        """

        ts_df = self.get_database_data(surface_query)

        if not ts_df.empty:
            fig_ts = px.line(ts_df, x='date', y='avg_surface_temp',
                           title='Surface Temperature Time Series',
                           labels={'avg_surface_temp': 'Temperature (°C)', 'date': 'Date'})
            st.plotly_chart(fig_ts, use_container_width=True)
        else:
            st.info("No time series data available")

    def render_sidebar(self):
        """Render simplified sidebar"""
        st.sidebar.markdown("## 🌊 Dashboard Controls")

        st.sidebar.markdown("### 🔌 System Status")
        try:
            conn = self.get_database_connection()
            if conn:
                st.sidebar.success("✅ Database Connected")
                conn.close()
            else:
                st.sidebar.error("❌ Database Connection Failed")
        except:
            st.sidebar.error("❌ Database Connection Failed")

        st.sidebar.markdown("### 🔧 Data Management")

        if st.sidebar.button("📥 Export Comprehensive Data"):
            st.sidebar.info("🔄 Generating comprehensive export...")

            comprehensive_query = """
            SELECT 
                f.platform_number,
                COALESCE(f.project_name, 'Unknown') as project_name,
                COALESCE(m.platform_type, 'Unknown') as platform_type,
                COALESCE(m.platform_maker, 'Unknown') as platform_maker,
                p.cycle_number,
                p.juld as profile_date,
                p.latitude,
                p.longitude,
                COUNT(d.measurement_id) as total_measurements,
                ROUND(AVG(d.temp), 2) as avg_temperature,
                ROUND(AVG(d.psal), 2) as avg_salinity,
                ROUND(MIN(d.pres), 2) as min_pressure,
                ROUND(MAX(d.pres), 2) as max_pressure
            FROM profile_table p
            LEFT JOIN float_table f ON p.platform_number = f.platform_number
            LEFT JOIN meta_table m ON p.platform_number = m.platform_number
            LEFT JOIN depth_measurements_table d ON p.platform_number = d.platform_number AND p.cycle_number = d.cycle_number
            GROUP BY 
                f.platform_number, f.project_name,
                m.platform_type, m.platform_maker,
                p.cycle_number, p.juld, p.latitude, p.longitude
            ORDER BY f.platform_number, p.cycle_number
            """

            comprehensive_df = self.get_database_data(comprehensive_query)

            if not comprehensive_df.empty:
                csv = comprehensive_df.to_csv(index=False)
                st.sidebar.download_button(
                    label="💾 Download Comprehensive Export",
                    data=csv,
                    file_name="argo_comprehensive_export.csv",
                    mime="text/csv"
                )
                st.sidebar.success(f"✅ Export ready! {len(comprehensive_df)} records")
            else:
                st.sidebar.warning("No data to export")

        if st.sidebar.button("🔄 Refresh Dashboard"):
            st.cache_data.clear()
            st.rerun()

    def run(self):
        """Run the complete enhanced dashboard"""
        self.render_header()
        self.render_overview_metrics()

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🗺️ Global Map", 
            "📈 Profiles", 
            "📊 Time Series", 
            "🤖 AI Assistant",
            "📂 File Upload",
            "📊 Graph Generator"
        ])

        with tab1:
            self.render_full_width_map()

        with tab2:
            self.render_profile_plots()

        with tab3:
            self.render_time_series()

        with tab4:
            self.render_enhanced_ai_chat()

        with tab5:
            self.render_file_upload_section()

        with tab6:
            self.render_graph_generator()

        self.render_sidebar()

def main():
    """Main entry point"""
    try:
        dashboard = EnhancedArgoStreamlitDashboard()
        dashboard.run()
    except Exception as e:
        st.error(f"Dashboard error: {e}")
        st.info("Please check that all required files are present and configured correctly")

if __name__ == "__main__":
    main()
