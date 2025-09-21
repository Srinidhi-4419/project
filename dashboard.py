#!/usr/bin/env python3
"""
Enhanced Argo Float Dashboard - With RAG Integration
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

# Import your RAG system
try:
    from test_rag import EnhancedArgoRAGSystem  # Your RAG system
    from process import process_argo_file
    from graphgenerator import ArgoGraphGenerator
except ImportError as e:
    st.error(f"Please ensure required files are present: {e}")
    st.stop()

class EnhancedArgoStreamlitDashboard:
    """Enhanced Streamlit dashboard with RAG integration"""

    def __init__(self):
        self.setup_page_config()
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

    def get_database_connection(self):
        """Get database connection"""
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
        """Render RAG-enhanced graph generator"""
        st.markdown("""
        <div class="graph-container">
            <h2 style="color: #e67e22; margin-bottom: 1rem;">📊 RAG-Enhanced Graph Generator</h2>
            <p style="color: #6c757d; margin-bottom: 1.5rem;">
                Create advanced oceanographic visualizations using natural language with RAG-powered SQL generation
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 💬 Graph Request")
        
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_request = st.text_input(
                "Describe the graph you want:",
                placeholder="e.g., scatter plot of temperature vs salinity for float 1900122",
                label_visibility="collapsed"
            )
        
        with col2:
            generate_button = st.button("📊 Generate", use_container_width=True, type="primary")
        
        if generate_button and user_request:
            st.markdown("---")
            # ✅ CORRECT: Use your existing graph generator
            self.graph_generator.generate_graph(user_request)
        
        # Add examples
        with st.expander("💡 Example Requests", expanded=False):
            st.markdown("""
            **🔬 Oceanographic Analysis:**
            - `temperature vs depth profile for float 1900122`
            - `scatter plot of temperature vs salinity colored by depth`
            - `histogram of salinity measurements`
            - `line plot of surface temperature over time`
            
            **🌊 Advanced Queries:**
            - `heatmap of temperature by latitude and longitude`
            - `box plot of temperature distribution by float`
            - `correlation between temperature and salinity for all floats`
            - `time series of mixed layer depth variations`
            """)




    def render_enhanced_ai_chat(self):
        """Render enhanced AI chat interface with RAG integration"""
        st.markdown("""
        <div class="chat-container">
            <h2 style="color: #1f77b4; margin-bottom: 1rem;">🤖 Enhanced RAG AI Assistant</h2>
            <p style="color: #6c757d; margin-bottom: 1.5rem;">
                The AI uses advanced thinking-based analysis and generates sophisticated SQL queries.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Initialize RAG system if not already done
        if 'rag_system' not in st.session_state:
            with st.spinner("🔄 Initializing Enhanced RAG System..."):
                try:
                    PERPLEXITY_API_KEY = "ur key"
                    st.session_state.rag_system = EnhancedArgoRAGSystem(perplexity_api_key=PERPLEXITY_API_KEY)
                    st.success("✅ Enhanced RAG System initialized!")
                except Exception as e:
                    st.error(f"❌ Failed to initialize RAG system: {e}")
                    st.session_state.rag_system = None

        # Initialize chat history with simplified welcome message
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = [
                {
                    'role': 'ai', 
                    'content': """👋 Welcome to the Enhanced RAG Assistant!

    I can help you with both technical database queries and general oceanographic knowledge

    📚 General Knowledge:
    • "What is the Argo program?"
    • "How do Argo floats work?"
    • "Tell me about ocean temperature inversions" """
                }
            ]

        # Query classification indicator
        if 'last_query_type' in st.session_state:
            query_type = st.session_state.last_query_type
            if query_type == 'technical':
                st.info("🔬 **Last Query Type:** Technical (Database Analysis)")
            elif query_type == 'general':
                st.info("📚 **Last Query Type:** General Knowledge")

        # Chat history display with enhanced formatting
        chat_container = st.container()
        with chat_container:
            for i, message in enumerate(st.session_state.chat_history):
                if message['role'] == 'user':
                    st.markdown(f"""
                    <div class="chat-message-user">
                        <strong>🧑‍💻 You:</strong> {message['content']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message-ai">
                        <strong>🤖 Enhanced RAG Assistant:</strong><br>{message['content']}
                    </div>
                    """, unsafe_allow_html=True)

                    # Show SQL query if available
                    if 'sql' in message:
                        with st.expander("💻 Generated SQL Query", expanded=False):
                            st.code(message['sql'], language='sql')

                    # Show thinking process if available
                    if 'thinking_process' in message and st.session_state.get('show_thinking', False):
                        with st.expander("🧠 AI Thinking Process", expanded=False):
                            st.text(message['thinking_process'])

                    # Show processing info if available
                    if 'processing_info' in message:
                        st.caption(f"📊 {message['processing_info']}")

        # Enhanced input section
        st.markdown("### 💬 Ask Your Question")

        # Toggle for showing thinking process
        col1, col2 = st.columns([3, 1])
        with col1:
                show_thinking = st.checkbox("🧠 Show AI thinking process", value=False)
                st.session_state.show_thinking = show_thinking
        
        with col2:
            if st.button("🗑️ Clear Chat"):
                st.session_state.chat_history = st.session_state.chat_history[:1]  # Keep welcome message
                if 'last_query_type' in st.session_state:
                    del st.session_state.last_query_type
                st.rerun()

        # Quick suggestion buttons
       
        col1, col2 = st.columns([4, 1])

        with col1:
            # Use suggested query if available
            default_query = st.session_state.get('suggested_query', '')
            user_query = st.text_input(
                "Your question:",
                value=default_query,
                placeholder="e.g., Find density inversions using sigma-0 calculations where deeper water is less dense than surface water",
                label_visibility="collapsed"
            )
            if 'suggested_query' in st.session_state:
                 del st.session_state.suggested_query

        with col2:
            send_button = st.button("🚀 Send", use_container_width=True, type="primary")

        # Process query
        if send_button and user_query:
            # Add user message
            st.session_state.chat_history.append({'role': 'user', 'content': user_query})

            if st.session_state.rag_system:
                with st.spinner("🔄 Processing with Enhanced RAG System..."):
                    try:
                        # Process query using RAG system
                        result = st.session_state.rag_system.process_enhanced_query(
                            user_query, 
                            show_details=show_thinking
                        )
                        st.session_state.last_query_type = result.get('query_type', 'unknown')
                        
                        if result['success']:
                            # Format response using RAG system
                            formatted_response = st.session_state.rag_system.format_detailed_response(
                                result, 
                                result['query_type']
                            )
                            
                            # Create AI message
                            ai_message = {
                                'role': 'ai', 
                                'content': formatted_response
                            }
                            
                            # Add SQL query if technical query
                            if result['query_type'] == 'technical' and 'sql_query' in result:
                                ai_message['sql'] = result['sql_query']
                            
                            # Add thinking process if available and requested
                            if show_thinking and 'thinking_process' in result:
                                ai_message['thinking_process'] = result['thinking_process']
                            
                            # Add processing info
                            if result['query_type'] == 'technical':
                                context_docs = result.get('context_documents', 0)
                                row_count = result.get('row_count', 0)
                                method = result.get('method', 'RAG + Database')
                                ai_message['processing_info'] = f"{method} | {row_count} results | {context_docs} context docs"
                            else:
                                method = result.get('method', 'Knowledge Base')
                                ai_message['processing_info'] = f"{method}"
                            
                            st.session_state.chat_history.append(ai_message)
                            
                            # Show success metrics
                            if result['query_type'] == 'technical':
                                st.success(f"✅ Query processed successfully! Found {result.get('row_count', 0)} results using {context_docs} context documents.")
                            else:
                                st.success(f"✅ Knowledge query processed successfully using {method}!")
                            
                        else:
                            # Handle failed queries
                            error_message = f"❌ Sorry, I encountered an error: {result.get('error', 'Unknown error')}"
                            
                            ai_message = {
                                'role': 'ai', 
                                'content': error_message
                            }
                            
                            # Add failed SQL if available
                            if 'sql_query' in result:
                                ai_message['sql'] = result['sql_query']
                            
                            # Add thinking process for debugging
                            if show_thinking and 'thinking_process' in result:
                                ai_message['thinking_process'] = result['thinking_process']
                            
                            st.session_state.chat_history.append(ai_message)
                            st.error("Query failed. Check the SQL query and thinking process for debugging.")
                        
                        st.rerun()
                        
                    except Exception as e:
                        error_message = f"❌ System error: {str(e)}"
                        st.session_state.chat_history.append({'role': 'ai', 'content': error_message})
                        st.error(f"System error: {e}")
                        st.rerun()
            else:
                st.error("❌ Enhanced RAG system not available. Please check initialization.")

        # Performance metrics (optional)
        if st.session_state.get('show_thinking', False):
            with st.expander("📊 System Performance", expanded=False):
                if 'rag_system' in st.session_state and st.session_state.rag_system:
                    st.success("✅ Enhanced RAG System: Active")
                    st.info("📡 Perplexity API: Connected")
                    st.info("🗄️ Database: Connected")
                    st.info("🧠 Thinking Mode: Enabled")
                else:
                    st.error("❌ Enhanced RAG System: Inactive")

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
                except Exception as cleanup_error:
                    pass

    def render_profile_plots(self):
        """Render enhanced temperature/salinity profiles with improved styling and features"""
        st.subheader("📈 Enhanced Temperature & Salinity Profiles")

        floats_df = self.get_database_data("SELECT DISTINCT platform_number FROM float_table ORDER BY platform_number")

        if not floats_df.empty:
            # Float selection with additional info
            col1, col2 = st.columns([2, 1])
            with col1:
                selected_float = st.selectbox("Select Float:", floats_df['platform_number'].tolist())
            
            with col2:
                # Add cycle selection option
                show_latest = st.checkbox("Show Latest Cycle Only", value=False)

            if selected_float:
                # Get profile count for this float
                count_query = f"""
                SELECT COUNT(DISTINCT cycle_number) as profile_count,
                    MIN(p.juld) as first_date,
                    MAX(p.juld) as last_date
                FROM profile_table p
                WHERE platform_number = '{selected_float}'
                """
                count_df = self.get_database_data(count_query)
                
                if not count_df.empty:
                    profile_count = count_df['profile_count'].iloc[0]
                    first_date = count_df['first_date'].iloc[0]
                    last_date = count_df['last_date'].iloc[0]
                    
                    st.info(f"📊 Float {selected_float}: {profile_count} profiles from {first_date} to {last_date}")

                # Enhanced queries with cycle information
                if show_latest:
                    cycle_filter = f"""
                    AND d.cycle_number = (
                        SELECT MAX(cycle_number) 
                        FROM depth_measurements_table 
                        WHERE platform_number = '{selected_float}'
                    )
                    """
                else:
                    cycle_filter = ""

                col1, col2 = st.columns(2)

                with col1:
                    temp_query = f"""
                    SELECT d.pres, d.temp, d.temp_qc, d.cycle_number,
                        p.juld, p.latitude, p.longitude
                    FROM depth_measurements_table d
                    JOIN profile_table p ON d.platform_number = p.platform_number 
                                        AND d.cycle_number = p.cycle_number
                    WHERE d.platform_number = '{selected_float}' 
                    AND d.temp IS NOT NULL AND d.temp_qc = '1'
                    {cycle_filter}
                    ORDER BY d.pres
                    """
                    temp_df = self.get_database_data(temp_query)

                    if not temp_df.empty:
                        # Enhanced temperature plot
                        fig_temp = go.Figure()
                        
                        if show_latest:
                            # Single profile with enhanced styling
                            fig_temp.add_trace(go.Scatter(
                                x=temp_df['temp'], 
                                y=temp_df['pres'],
                                mode='lines+markers',
                                name='Temperature',
                                line=dict(color='crimson', width=3),
                                marker=dict(
                                    size=4,
                                    color='darkred',
                                    line=dict(width=1, color='white')
                                ),
                                hovertemplate='<b>Temperature:</b> %{x:.2f}°C<br>' +
                                            '<b>Pressure:</b> %{y:.1f} dbar<br>' +
                                            '<extra></extra>'
                            ))
                            
                            # Add cycle info to title
                            cycle = temp_df['cycle_number'].iloc[0]
                            date = temp_df['juld'].iloc[0]
                            title = f'Temperature Profile - Float {selected_float}<br><sub>Cycle {cycle} - {date}</sub>'
                        else:
                            # Multiple profiles with color coding
                            cycles = temp_df['cycle_number'].unique()
                            colors = px.colors.qualitative.Set3
                            
                            for i, cycle in enumerate(cycles[:10]):  # Limit to 10 cycles for clarity
                                cycle_data = temp_df[temp_df['cycle_number'] == cycle]
                                fig_temp.add_trace(go.Scatter(
                                    x=cycle_data['temp'], 
                                    y=cycle_data['pres'],
                                    mode='lines',
                                    name=f'Cycle {cycle}',
                                    line=dict(color=colors[i % len(colors)], width=2),
                                    opacity=0.7,
                                    hovertemplate=f'<b>Cycle {cycle}</b><br>' +
                                                '<b>Temperature:</b> %{x:.2f}°C<br>' +
                                                '<b>Pressure:</b> %{y:.1f} dbar<br>' +
                                                '<extra></extra>'
                                ))
                            
                            title = f'Temperature Profiles - Float {selected_float}<br><sub>All Available Cycles</sub>'

                        # Enhanced layout for temperature
                        fig_temp.update_layout(
                            title=dict(text=title, font=dict(size=16)),
                            xaxis_title="Temperature (°C)",
                            yaxis_title="Pressure (dbar)",
                            yaxis=dict(
                                autorange="reversed",
                                showgrid=True,
                                gridcolor='lightgray',
                                gridwidth=1
                            ),
                            xaxis=dict(
                                showgrid=True,
                                gridcolor='lightgray',
                                gridwidth=1
                            ),
                            plot_bgcolor='white',
                            height=500,
                            margin=dict(l=50, r=50, t=80, b=50)
                        )
                        
                        # Add depth zone annotations
                        fig_temp.add_hrect(
                            y0=0, y1=50, 
                            fillcolor="lightblue", opacity=0.1,
                            annotation_text="Mixed Layer", 
                            annotation_position="top left"
                        )
                        fig_temp.add_hrect(
                            y0=200, y1=1000, 
                            fillcolor="lightgreen", opacity=0.1,
                            annotation_text="Thermocline", 
                            annotation_position="top left"
                        )

                        st.plotly_chart(fig_temp, use_container_width=True)
                    else:
                        st.info("No temperature data available for this float")

                with col2:
                    sal_query = f"""
                    SELECT d.pres, d.psal, d.psal_qc, d.cycle_number,
                        p.juld, p.latitude, p.longitude
                    FROM depth_measurements_table d
                    JOIN profile_table p ON d.platform_number = p.platform_number 
                                        AND d.cycle_number = p.cycle_number
                    WHERE d.platform_number = '{selected_float}'
                    AND d.psal IS NOT NULL AND d.psal_qc = '1'
                    {cycle_filter}
                    ORDER BY d.pres
                    """
                    sal_df = self.get_database_data(sal_query)

                    if not sal_df.empty:
                        # Enhanced salinity plot
                        fig_sal = go.Figure()
                        
                        if show_latest:
                            # Single profile with enhanced styling
                            fig_sal.add_trace(go.Scatter(
                                x=sal_df['psal'], 
                                y=sal_df['pres'],
                                mode='lines+markers',
                                name='Salinity',
                                line=dict(color='navy', width=3),
                                marker=dict(
                                    size=4,
                                    color='darkblue',
                                    line=dict(width=1, color='white')
                                ),
                                hovertemplate='<b>Salinity:</b> %{x:.3f} PSU<br>' +
                                            '<b>Pressure:</b> %{y:.1f} dbar<br>' +
                                            '<extra></extra>'
                            ))
                            
                            cycle = sal_df['cycle_number'].iloc[0]
                            date = sal_df['juld'].iloc[0]
                            title = f'Salinity Profile - Float {selected_float}<br><sub>Cycle {cycle} - {date}</sub>'
                        else:
                            # Multiple profiles
                            cycles = sal_df['cycle_number'].unique()
                            colors = px.colors.qualitative.Set3
                            
                            for i, cycle in enumerate(cycles[:10]):
                                cycle_data = sal_df[sal_df['cycle_number'] == cycle]
                                fig_sal.add_trace(go.Scatter(
                                    x=cycle_data['psal'], 
                                    y=cycle_data['pres'],
                                    mode='lines',
                                    name=f'Cycle {cycle}',
                                    line=dict(color=colors[i % len(colors)], width=2),
                                    opacity=0.7,
                                    hovertemplate=f'<b>Cycle {cycle}</b><br>' +
                                                '<b>Salinity:</b> %{x:.3f} PSU<br>' +
                                                '<b>Pressure:</b> %{y:.1f} dbar<br>' +
                                                '<extra></extra>'
                                ))
                            
                            title = f'Salinity Profiles - Float {selected_float}<br><sub>All Available Cycles</sub>'

                        # Enhanced layout for salinity
                        fig_sal.update_layout(
                            title=dict(text=title, font=dict(size=16)),
                            xaxis_title="Salinity (PSU)",
                            yaxis_title="Pressure (dbar)",
                            yaxis=dict(
                                autorange="reversed",
                                showgrid=True,
                                gridcolor='lightgray',
                                gridwidth=1
                            ),
                            xaxis=dict(
                                showgrid=True,
                                gridcolor='lightgray',
                                gridwidth=1
                            ),
                            plot_bgcolor='white',
                            height=500,
                            margin=dict(l=50, r=50, t=80, b=50)
                        )
                        
                        # Add depth zone annotations
                        fig_sal.add_hrect(
                            y0=0, y1=50, 
                            fillcolor="lightblue", opacity=0.1,
                            annotation_text="Mixed Layer", 
                            annotation_position="top left"
                        )
                        fig_sal.add_hrect(
                            y0=200, y1=1000, 
                            fillcolor="lightgreen", opacity=0.1,
                            annotation_text="Thermocline", 
                            annotation_position="top left"
                        )

                        st.plotly_chart(fig_sal, use_container_width=True)
                    else:
                        st.info("No salinity data available for this float")

                # Add T-S Diagram option
                if not temp_df.empty and not sal_df.empty:
                    if st.checkbox("📈 Show Temperature-Salinity Diagram"):
                        # Merge temperature and salinity data
                        ts_data = pd.merge(
                            temp_df[['pres', 'temp', 'cycle_number']], 
                            sal_df[['pres', 'psal', 'cycle_number']], 
                            on=['pres', 'cycle_number'], 
                            how='inner'
                        )
                        
                        if not ts_data.empty:
                            fig_ts = px.scatter(
                                ts_data, 
                                x='psal', y='temp', 
                                color='pres',
                                title=f'T-S Diagram - Float {selected_float}',
                                labels={
                                    'psal': 'Salinity (PSU)', 
                                    'temp': 'Temperature (°C)',
                                    'pres': 'Pressure (dbar)'
                                },
                                color_continuous_scale='viridis'
                            )
                            fig_ts.update_traces(marker=dict(size=6, line=dict(width=1, color='white')))
                            fig_ts.update_layout(
                                height=400,
                                plot_bgcolor='white',
                                coloraxis_colorbar_title="Pressure (dbar)"
                            )
                            st.plotly_chart(fig_ts, use_container_width=True)

        else:
            st.warning("No floats found")

    def render_temperature_series(self, time_grouping, show_trend, date_range):
            """Enhanced temperature time series"""
            
            # Build time grouping clause
            if time_grouping == "Daily":
                time_clause = "p.juld::date"
                date_format = "date"
            elif time_grouping == "Weekly": 
                time_clause = "DATE_TRUNC('week', p.juld)::date"
                date_format = "week"
            elif time_grouping == "Monthly":
                time_clause = "DATE_TRUNC('month', p.juld)::date"
                date_format = "month"
            else:  # Seasonal
                time_clause = "DATE_TRUNC('quarter', p.juld)::date"
                date_format = "season"
            
            # Build date filter - FIXED LOGIC
            date_filter = ""
            if date_range:
                # Handle different types that st.date_input can return
                if isinstance(date_range, tuple) and len(date_range) == 2:
                    # Range selection (start_date, end_date)
                    start_date, end_date = date_range
                    if start_date and end_date:
                        date_filter = f"AND p.juld::date BETWEEN '{start_date}' AND '{end_date}'"
                elif hasattr(date_range, '__iter__') and not isinstance(date_range, str):
                    # List-like object (could be from multi-select)
                    try:
                        date_list = list(date_range)
                        if len(date_list) == 2:
                            start_date, end_date = date_list[0], date_list[1]
                            if start_date and end_date:
                                date_filter = f"AND p.juld::date BETWEEN '{start_date}' AND '{end_date}'"
                        elif len(date_list) == 1 and date_list[0]:
                            # Single date selected
                            date_filter = f"AND p.juld::date = '{date_list[0]}'"
                    except (TypeError, IndexError):
                        pass
                else:
                    # Single date object
                    try:
                        if date_range:
                            date_filter = f"AND p.juld::date = '{date_range}'"
                    except:
                        pass
            
            # Rest of your function remains the same...
            surface_query = f"""
            SELECT 
                {time_clause} as time_period,
                AVG(d.temp) as avg_surface_temp,
                STDDEV(d.temp) as temp_std,
                COUNT(*) as measurement_count,
                COUNT(DISTINCT d.platform_number) as float_count,
                MIN(d.temp) as min_temp,
                MAX(d.temp) as max_temp
            FROM depth_measurements_table d
            JOIN profile_table p ON d.platform_number = p.platform_number AND d.cycle_number = p.cycle_number
            WHERE d.pres < 10 AND d.temp IS NOT NULL AND d.temp_qc = '1'
            {date_filter}
            GROUP BY {time_clause}
            ORDER BY time_period
            """
            ts_df = self.get_database_data(surface_query)
            
            if not ts_df.empty:
                # Create enhanced plot
                fig = go.Figure()
                
                # Main temperature line
                fig.add_trace(go.Scatter(
                    x=ts_df['time_period'], 
                    y=ts_df['avg_surface_temp'],
                    mode='lines+markers',
                    name='Average Temperature',
                    line=dict(color='crimson', width=3),
                    marker=dict(size=6, color='darkred'),
                    hovertemplate='<b>%{x}</b><br>' +
                                'Temperature: %{y:.2f}°C<br>' +
                                '<extra></extra>'
                ))
                
                # Add uncertainty bands if standard deviation available
                if 'temp_std' in ts_df.columns and ts_df['temp_std'].notna().any():
                    upper_bound = ts_df['avg_surface_temp'] + ts_df['temp_std']
                    lower_bound = ts_df['avg_surface_temp'] - ts_df['temp_std']
                    
                    fig.add_trace(go.Scatter(
                        x=ts_df['time_period'],
                        y=upper_bound,
                        fill=None,
                        mode='lines',
                        line_color='rgba(0,0,0,0)',
                        showlegend=False
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=ts_df['time_period'],
                        y=lower_bound,
                        fill='tonexty',
                        mode='lines',
                        line_color='rgba(0,0,0,0)',
                        name='±1 Std Dev',
                        fillcolor='rgba(220,20,60,0.2)'
                    ))
                import numpy as np
                # Add trend line if requested
                if show_trend and len(ts_df) > 2:
                    from scipy import stats
                    x_numeric = np.arange(len(ts_df))
                    slope, intercept, r_value, p_value, std_err = stats.linregress(x_numeric, ts_df['avg_surface_temp'])
                    
                    trend_line = slope * x_numeric + intercept
                    fig.add_trace(go.Scatter(
                        x=ts_df['time_period'],
                        y=trend_line,
                        mode='lines',
                        name=f'Trend (R²={r_value**2:.3f})',
                        line=dict(dash='dash', color='navy', width=2),
                        hovertemplate=f'Trend: {slope*365:.3f}°C/year<br>' +
                                    f'R²: {r_value**2:.3f}<br>' +
                                    '<extra></extra>'
                    ))
                
                # Enhanced layout
                fig.update_layout(
                    title=dict(
                        text=f'Surface Temperature Time Series ({time_grouping})',
                        font=dict(size=18)
                    ),
                    xaxis_title=f"Time ({date_format.title()})",
                    yaxis_title="Temperature (°C)",
                    hovermode='x unified',
                    plot_bgcolor='white',
                    height=500,
                    showlegend=True,
                    legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="left", 
                        x=0.01
                    )
                )
                
                # Add grid
                fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
                fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display statistics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Average Temperature", f"{ts_df['avg_surface_temp'].mean():.2f}°C")
                with col2:
                    st.metric("Temperature Range", f"{ts_df['max_temp'].max() - ts_df['min_temp'].min():.2f}°C")
                with col3:
                    st.metric("Total Measurements", f"{ts_df['measurement_count'].sum():,}")
                with col4:
                    st.metric("Active Floats", f"{ts_df['float_count'].max()}")
                    
            else:
                st.info("No temperature time series data available for the selected parameters")

    
    def render_combined_series(self, time_grouping, show_trend, date_range):
        """Combined temperature and salinity time series"""
        
        # Similar time grouping logic as above
        if time_grouping == "Monthly":
            time_clause = "DATE_TRUNC('month', p.juld)::date"
        else:
            time_clause = "p.juld::date"
        
        date_filter = ""
        if date_range and len(date_range) == 2:
            date_filter = f"AND p.juld::date BETWEEN '{date_range[0]}' AND '{date_range[1]}'"
        
        combined_query = f"""
        SELECT 
            {time_clause} as time_period,
            AVG(d.temp) as avg_temp,
            AVG(d.psal) as avg_salinity,
            COUNT(*) as measurement_count
        FROM depth_measurements_table d
        JOIN profile_table p ON d.platform_number = p.platform_number AND d.cycle_number = p.cycle_number  
        WHERE d.pres < 10 AND d.temp IS NOT NULL AND d.psal IS NOT NULL 
        AND d.temp_qc = '1' AND d.psal_qc = '1'
        {date_filter}
        GROUP BY {time_clause}
        ORDER BY time_period
        """
        
        ts_df = self.get_database_data(combined_query)
        
        if not ts_df.empty:
            # Create subplot with secondary y-axis
            from plotly.subplots import make_subplots
            
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Temperature trace
            fig.add_trace(
                go.Scatter(
                    x=ts_df['time_period'], 
                    y=ts_df['avg_temp'],
                    mode='lines+markers',
                    name='Temperature',
                    line=dict(color='red', width=3),
                    marker=dict(size=5)
                ),
                secondary_y=False,
            )
            
            # Salinity trace
            fig.add_trace(
                go.Scatter(
                    x=ts_df['time_period'], 
                    y=ts_df['avg_salinity'],
                    mode='lines+markers',
                    name='Salinity',
                    line=dict(color='blue', width=3),
                    marker=dict(size=5)
                ),
                secondary_y=True,
            )
            
            # Update axes labels
            fig.update_xaxes(title_text="Time")
            fig.update_yaxes(title_text="Temperature (°C)", secondary_y=False, title_font_color="red")
            fig.update_yaxes(title_text="Salinity (PSU)", secondary_y=True, title_font_color="blue")
            
            fig.update_layout(
                title="Combined Temperature & Salinity Time Series",
                height=500,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.info("No combined time series data available")


    def render_depth_comparison(self, time_grouping, show_trend, date_range):
        """Multi-depth temperature comparison"""
        
        time_clause = "DATE_TRUNC('month', p.juld)::date" if time_grouping == "Monthly" else "p.juld::date"
        
        date_filter = ""
        if date_range and len(date_range) == 2:
            date_filter = f"AND p.juld::date BETWEEN '{date_range[0]}' AND '{date_range[1]}'"
        
        depth_query = f"""
        SELECT 
            {time_clause} as time_period,
            AVG(CASE WHEN d.pres < 10 THEN d.temp END) as surface_temp,
            AVG(CASE WHEN d.pres BETWEEN 50 AND 100 THEN d.temp END) as subsurface_temp,
            AVG(CASE WHEN d.pres BETWEEN 200 AND 300 THEN d.temp END) as deep_temp,
            COUNT(*) as measurement_count
        FROM depth_measurements_table d
        JOIN profile_table p ON d.platform_number = p.platform_number AND d.cycle_number = p.cycle_number
        WHERE d.temp IS NOT NULL AND d.temp_qc = '1'
        {date_filter}
        GROUP BY {time_clause}
        HAVING AVG(CASE WHEN d.pres < 10 THEN d.temp END) IS NOT NULL
        ORDER BY time_period
        """
        
        ts_df = self.get_database_data(depth_query)
        
        if not ts_df.empty:
            fig = go.Figure()
            
            # Different depth layers
            if ts_df['surface_temp'].notna().any():
                fig.add_trace(go.Scatter(
                    x=ts_df['time_period'], y=ts_df['surface_temp'],
                    mode='lines+markers', name='Surface (0-10m)',
                    line=dict(color='red', width=2)
                ))
            
            if ts_df['subsurface_temp'].notna().any():
                fig.add_trace(go.Scatter(
                    x=ts_df['time_period'], y=ts_df['subsurface_temp'],
                    mode='lines+markers', name='Subsurface (50-100m)',
                    line=dict(color='orange', width=2)
                ))
            
            if ts_df['deep_temp'].notna().any():
                fig.add_trace(go.Scatter(
                    x=ts_df['time_period'], y=ts_df['deep_temp'],
                    mode='lines+markers', name='Deep (200-300m)',
                    line=dict(color='blue', width=2)
                ))
            
            fig.update_layout(
                title="Temperature Comparison Across Depths",
                xaxis_title="Time",
                yaxis_title="Temperature (°C)",
                height=500,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.info("No multi-depth time series data available")
    def render_time_series(self):
        """Render enhanced time series analysis with multiple parameters and options"""
        st.subheader("📊 Enhanced Time Series Analysis")
        
        # Time series options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            analysis_type = st.selectbox(
                "Analysis Type:",
                ["Surface Temperature", "Surface Salinity", "Both Parameters", "Multi-Depth Analysis"]
            )
        
        with col2:
            time_grouping = st.selectbox(
                "Time Resolution:",
                ["Daily", "Weekly", "Monthly", "Seasonal"]
            )
        
        with col3:
            show_trend = st.checkbox("Show Trend Line", value=True)
        
        # Date range selector
        date_range = st.date_input(
            "Select Date Range (optional):",
            value=None,
            help="Leave empty to show all available data"
        )
        
        # Build dynamic queries based on selections
        if analysis_type == "Surface Temperature":
            st.markdown("### 🌡️ Surface Temperature Trends")
            self.render_temperature_series( time_grouping, show_trend, date_range)
            
        elif analysis_type == "Surface Salinity":
            st.markdown("### 🧂 Surface Salinity Trends") 
            self.render_salinity_series( time_grouping, show_trend, date_range)
            
        elif analysis_type == "Both Parameters":
            st.markdown("### 🌊 Combined Temperature & Salinity Analysis")
            self.render_combined_series( time_grouping, show_trend, date_range)
            
        elif analysis_type == "Multi-Depth Analysis":
            st.markdown("### 📏 Multi-Depth Temperature Analysis")
            self.render_depth_comparison( time_grouping, show_trend, date_range)

    def render_salinity_series(self, time_grouping, show_trend, date_range):
        """Enhanced salinity time series"""
        
        # Build time grouping clause
        if time_grouping == "Daily":
            time_clause = "p.juld::date"
            date_format = "date"
        elif time_grouping == "Weekly": 
            time_clause = "DATE_TRUNC('week', p.juld)::date"
            date_format = "week"
        elif time_grouping == "Monthly":
            time_clause = "DATE_TRUNC('month', p.juld)::date"
            date_format = "month"
        else:  # Seasonal
            time_clause = "DATE_TRUNC('quarter', p.juld)::date"
            date_format = "season"
        
        # Build date filter with proper handling
        date_filter = ""
        if date_range is not None:
            try:
                if hasattr(date_range, '__len__') and len(date_range) == 2:
                    start_date, end_date = date_range
                    if start_date and end_date:
                        date_filter = f"AND p.juld::date BETWEEN '{start_date}' AND '{end_date}'"
                else:
                    # Single date
                    date_filter = f"AND p.juld::date = '{date_range}'"
            except (TypeError, AttributeError):
                # Skip date filtering if there's an issue
                pass
        
        surface_query = f"""
        SELECT 
            {time_clause} as time_period,
            AVG(d.psal) as avg_surface_salinity,
            STDDEV(d.psal) as salinity_std,
            COUNT(*) as measurement_count,
            COUNT(DISTINCT d.platform_number) as float_count,
            MIN(d.psal) as min_salinity,
            MAX(d.psal) as max_salinity
        FROM depth_measurements_table d
        JOIN profile_table p ON d.platform_number = p.platform_number AND d.cycle_number = p.cycle_number
        WHERE d.pres < 10 AND d.psal IS NOT NULL AND d.psal_qc = '1'
        {date_filter}
        GROUP BY {time_clause}
        ORDER BY time_period
        """
        
        ts_df = self.get_database_data(surface_query)
        
        if not ts_df.empty:
            # Create enhanced plot
            fig = go.Figure()
            
            # Main salinity line
            fig.add_trace(go.Scatter(
                x=ts_df['time_period'], 
                y=ts_df['avg_surface_salinity'],
                mode='lines+markers',
                name='Average Salinity',
                line=dict(color='navy', width=3),
                marker=dict(size=6, color='darkblue'),
                hovertemplate='<b>%{x}</b><br>' +
                            'Salinity: %{y:.3f} PSU<br>' +
                            '<extra></extra>'
            ))
            
            # Add uncertainty bands if standard deviation available
            if 'salinity_std' in ts_df.columns and ts_df['salinity_std'].notna().any():
                upper_bound = ts_df['avg_surface_salinity'] + ts_df['salinity_std']
                lower_bound = ts_df['avg_surface_salinity'] - ts_df['salinity_std']
                
                fig.add_trace(go.Scatter(
                    x=ts_df['time_period'],
                    y=upper_bound,
                    fill=None,
                    mode='lines',
                    line_color='rgba(0,0,0,0)',
                    showlegend=False
                ))
                
                fig.add_trace(go.Scatter(
                    x=ts_df['time_period'],
                    y=lower_bound,
                    fill='tonexty',
                    mode='lines',
                    line_color='rgba(0,0,0,0)',
                    name='±1 Std Dev',
                    fillcolor='rgba(0,0,139,0.2)'
                ))
            
            # Add trend line if requested
            if show_trend and len(ts_df) > 2:
                try:
                    from scipy import stats
                    import numpy as np
                    
                    x_numeric = np.arange(len(ts_df))
                    slope, intercept, r_value, p_value, std_err = stats.linregress(x_numeric, ts_df['avg_surface_salinity'])
                    
                    trend_line = slope * x_numeric + intercept
                    fig.add_trace(go.Scatter(
                        x=ts_df['time_period'],
                        y=trend_line,
                        mode='lines',
                        name=f'Trend (R²={r_value**2:.3f})',
                        line=dict(dash='dash', color='darkred', width=2),
                        hovertemplate=f'Trend: {slope*365:.4f} PSU/year<br>' +
                                    f'R²: {r_value**2:.3f}<br>' +
                                    '<extra></extra>'
                    ))
                except ImportError:
                    st.warning("scipy not available for trend analysis")
            
            # Enhanced layout
            fig.update_layout(
                title=dict(
                    text=f'Surface Salinity Time Series ({time_grouping})',
                    font=dict(size=18)
                ),
                xaxis_title=f"Time ({date_format.title()})",
                yaxis_title="Salinity (PSU)",
                hovermode='x unified',
                plot_bgcolor='white',
                height=500,
                showlegend=True,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left", 
                    x=0.01
                )
            )
            
            # Add grid
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Average Salinity", f"{ts_df['avg_surface_salinity'].mean():.3f} PSU")
            with col2:
                st.metric("Salinity Range", f"{ts_df['max_salinity'].max() - ts_df['min_salinity'].min():.3f} PSU")
            with col3:
                st.metric("Total Measurements", f"{ts_df['measurement_count'].sum():,}")
            with col4:
                st.metric("Active Floats", f"{ts_df['float_count'].max()}")
                
            # Additional salinity-specific insights
            st.markdown("### 📊 Salinity Analysis")
            
            col1, col2 = st.columns(2)
            with col1:
                # Salinity variability
                salinity_cv = (ts_df['avg_surface_salinity'].std() / ts_df['avg_surface_salinity'].mean()) * 100
                st.info(f"**Coefficient of Variation:** {salinity_cv:.2f}%")
                
            with col2:
                # Salinity classification (rough estimates)
                avg_salinity = ts_df['avg_surface_salinity'].mean()
                if avg_salinity < 32:
                    water_type = "Low Salinity (Freshwater Influence)"
                elif avg_salinity < 35:
                    water_type = "Normal Ocean Water"
                elif avg_salinity < 37:
                    water_type = "High Salinity (Evaporation Zone)"
                else:
                    water_type = "Very High Salinity (Hypersaline)"
                
                st.info(f"**Water Classification:** {water_type}")
                
        else:
            st.info("No salinity time series data available for the selected parameters")

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

        # RAG system status
        if 'rag_system' in st.session_state and st.session_state.rag_system:
            st.sidebar.success("✅ RAG System Active")
        else:
            st.sidebar.warning("⚠️ RAG System Not Initialized")

        st.sidebar.markdown("### 🔧 Data Management")

        if st.sidebar.button("📥 Export Comprehensive Data"):
            st.sidebar.info("🔄 Generating comprehensive export...")

            comprehensive_query = """
                        SELECT 
                f.platform_number,
                COALESCE(f.project_name, 'Unknown') AS project_name,
                COALESCE(m.platform_type, 'Unknown') AS platform_type,
                COALESCE(m.platform_maker, 'Unknown') AS platform_maker,
                p.cycle_number,
                p.juld AS profile_date,
                p.latitude,
                p.longitude,
                COUNT(d.measurement_id) AS total_measurements,
                ROUND(AVG(d.temp), 2) AS avg_temperature,
                ROUND(STDDEV(d.temp), 2) AS std_temperature,
                ROUND(MIN(d.temp), 2) AS min_temperature,
                ROUND(MAX(d.temp), 2) AS max_temperature,
                ROUND(AVG(d.psal), 2) AS avg_salinity,
                ROUND(STDDEV(d.psal), 2) AS std_salinity,
                ROUND(MIN(d.psal), 2) AS min_salinity,
                ROUND(MAX(d.psal), 2) AS max_salinity,
                ROUND(MIN(d.pres), 2) AS min_pressure,
                ROUND(MAX(d.pres), 2) AS max_pressure,
                COUNT(CASE WHEN d.temp_qc = '1' THEN 1 END) AS temp_qc_pass_count,
                COUNT(CASE WHEN d.psal_qc = '1' THEN 1 END) AS psal_qc_pass_count,
                ROUND(AVG(d.doxy), 2) AS avg_oxygen,
                ROUND(AVG(d.nitrate), 2) AS avg_nitrate,
                ROUND(AVG(d.ph_in_situ_total), 2) AS avg_ph
            FROM profile_table p
            LEFT JOIN float_table f ON p.platform_number = f.platform_number
            LEFT JOIN meta_table m ON p.platform_number = m.platform_number
            LEFT JOIN depth_measurements_table d 
                ON p.platform_number = d.platform_number 
                AND p.cycle_number = d.cycle_number
            GROUP BY 
                f.platform_number,
                f.project_name,
                m.platform_type,
                m.platform_maker,
                p.cycle_number,
                p.juld,
                p.latitude,
                p.longitude
            ORDER BY f.platform_number, p.cycle_number;

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
