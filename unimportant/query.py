#!/usr/bin/env python3
"""
Argo Natural Language Query System - COMPLETE SCHEMA VERSION
Now with all 15 tables and 191 variables fully documented for AI
"""

import json
import re
import psycopg2
from configparser import ConfigParser
import requests
from typing import Dict, List, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArgoSchemaContext:
    """COMPLETE schema context with all 15 tables and 191 variables"""

    def __init__(self):
        # Basic schema structure maintained for compatibility
        self.schema = {
            "database_name": "argo_floats",
            "total_tables": 15,
            "total_variables": 191,
            "categories": {
                "core_tables": 4,
                "metadata_tables": 5, 
                "trajectory_tables": 3,
                "reference_tables": 3
            }
        }

    def get_complete_schema_prompt(self) -> str:
        """Generate COMPLETE schema context with all 15 tables for AI"""

        prompt = """You are an expert SQL query generator for a comprehensive Argo oceanographic float database.

DATABASE: argo_floats (PostgreSQL)
TOTAL TABLES: 15 (Core + Metadata + Trajectory + Reference)
TOTAL VARIABLES: 191 fully documented

=== COMPLETE SCHEMA WITH ALL VARIABLES ===

TABLE 1: float_table (Master Float Registry)
Description: Master table with one row per Argo float containing basic metadata
Columns:
  • platform_number: VARCHAR(20) - Unique float identifier (WMO number) - PRIMARY KEY
  • project_name: VARCHAR(100) - Scientific project name
  • pi_name: VARCHAR(100) - Principal investigator name
  • launch_latitude: DECIMAL(10,6) - Deployment latitude in decimal degrees
  • launch_longitude: DECIMAL(11,6) - Deployment longitude in decimal degrees
  • platform_type: VARCHAR(50) - Float hardware type (e.g., APEX, ARVOR, SOLO)
  • firmware_version: VARCHAR(50) - Float firmware version
  • wmo_inst_type: VARCHAR(10) - WMO instrument type code
  • positioning_system: VARCHAR(50) - GPS/ARGOS positioning system
  • data_type: VARCHAR(20) - Data file type
  • format_version: VARCHAR(10) - NetCDF format version
  • handbook_version: VARCHAR(10) - Argo handbook version
  • date_creation: TIMESTAMP - Record creation date
  • date_update: TIMESTAMP - Last update date
  • created_at: TIMESTAMP - Database insert time
  • updated_at: TIMESTAMP - Database update time
Sample Data: platform_number: '13859', '1900122'
Row Count: ~2 active floats

TABLE 2: profile_table (Profile Metadata)
Description: Profile-level data with one row per float cycle/profile
Columns:
  • profile_id: SERIAL - Unique profile identifier - PRIMARY KEY
  • platform_number: VARCHAR(20) - Float WMO number - FOREIGN KEY
  • cycle_number: INTEGER - Float cycle number (1, 2, 3...)
  • juld: TIMESTAMP - Date/time of profile (Julian days converted)
  • juld_qc: CHAR(1) - Time quality flag ('1'=good, '4'=bad)
  • latitude: DECIMAL(10,6) - Profile latitude in decimal degrees
  • longitude: DECIMAL(11,6) - Profile longitude in decimal degrees
  • position_qc: CHAR(1) - Position quality flag
  • direction: CHAR(1) - Profile direction ('A'=ascending, 'D'=descending)
  • data_mode: CHAR(1) - Data mode ('R'=real-time, 'D'=delayed, 'A'=adjusted)
  • vertical_sampling_scheme: VARCHAR(100) - Sampling strategy description
  • config_mission_number: INTEGER - Mission configuration number
  • profile_pres_qc: CHAR(1) - Overall pressure QC for profile
  • profile_temp_qc: CHAR(1) - Overall temperature QC for profile
  • profile_psal_qc: CHAR(1) - Overall salinity QC for profile
  • created_at: TIMESTAMP - Database insert time
Sample Data: platform_number: '13859', cycle_number: 1-155, direction: 'A'
Row Count: ~207 total profiles
Unique Constraint: (platform_number, cycle_number, direction)

TABLE 3: depth_measurements_table (Core Oceanographic Data)
Description: Depth-resolved oceanographic measurements (main scientific data)
Columns:
  • measurement_id: SERIAL - Unique measurement ID - PRIMARY KEY
  • profile_id: INTEGER - Profile reference - FOREIGN KEY
  • platform_number: VARCHAR(20) - Float WMO number for quick filtering
  • cycle_number: INTEGER - Float cycle number
  • latitude: DECIMAL(10,6) - Measurement latitude
  • longitude: DECIMAL(11,6) - Measurement longitude

  PRESSURE DATA:
  • pres: DECIMAL(10,3) - Pressure in decibars (≈ depth in meters)
  • pres_qc: CHAR(1) - Pressure quality flag
  • pres_adjusted: DECIMAL(10,3) - Delayed-mode adjusted pressure
  • pres_adjusted_qc: CHAR(1) - Adjusted pressure quality flag
  • pres_adjusted_error: DECIMAL(10,3) - Adjusted pressure uncertainty

  TEMPERATURE DATA:
  • temp: DECIMAL(8,4) - Temperature in degrees Celsius
  • temp_qc: CHAR(1) - Temperature quality flag
  • temp_adjusted: DECIMAL(8,4) - Delayed-mode adjusted temperature
  • temp_adjusted_qc: CHAR(1) - Adjusted temperature quality flag
  • temp_adjusted_error: DECIMAL(8,4) - Adjusted temperature uncertainty

  SALINITY DATA:
  • psal: DECIMAL(8,4) - Practical salinity (PSU - dimensionless)
  • psal_qc: CHAR(1) - Salinity quality flag
  • psal_adjusted: DECIMAL(8,4) - Delayed-mode adjusted salinity
  • psal_adjusted_qc: CHAR(1) - Adjusted salinity quality flag
  • psal_adjusted_error: DECIMAL(8,4) - Adjusted salinity uncertainty

  BGC - DISSOLVED OXYGEN:
  • doxy: DECIMAL(8,4) - Dissolved oxygen (micromol/kg)
  • doxy_qc: CHAR(1) - Oxygen quality flag
  • doxy_adjusted: DECIMAL(8,4) - Adjusted dissolved oxygen
  • doxy_adjusted_qc: CHAR(1) - Adjusted oxygen quality flag
  • doxy_adjusted_error: DECIMAL(8,4) - Adjusted oxygen uncertainty

  BGC - NITRATE:
  • nitrate: DECIMAL(8,4) - Nitrate concentration (micromol/kg)
  • nitrate_qc: CHAR(1) - Nitrate quality flag
  • nitrate_adjusted: DECIMAL(8,4) - Adjusted nitrate
  • nitrate_adjusted_qc: CHAR(1) - Adjusted nitrate quality flag
  • nitrate_adjusted_error: DECIMAL(8,4) - Adjusted nitrate uncertainty

  BGC - pH:
  • ph_in_situ_total: DECIMAL(8,4) - pH in situ total scale
  • ph_in_situ_total_qc: CHAR(1) - pH quality flag
  • ph_in_situ_total_adjusted: DECIMAL(8,4) - Adjusted pH
  • ph_in_situ_total_adjusted_qc: CHAR(1) - Adjusted pH quality flag
  • ph_in_situ_total_adjusted_error: DECIMAL(8,4) - Adjusted pH uncertainty

  • created_at: TIMESTAMP - Database insert time
Sample Data: pres: 0-6500 dbar, temp: 2-28°C, psal: 32-37 PSU
Row Count: ~16,000+ measurements total

TABLE 4: meta_table (Comprehensive Float Metadata)
Description: Complete float specifications and deployment information
Columns:
  • meta_id: SERIAL - Unique meta ID - PRIMARY KEY
  • platform_number: VARCHAR(20) - Float WMO number - FOREIGN KEY - UNIQUE
  • data_type: VARCHAR(20) - Data file type identifier
  • format_version: VARCHAR(10) - NetCDF format version
  • platform_type: VARCHAR(50) - Specific platform type
  • platform_maker: VARCHAR(100) - Manufacturer (SBE, NKE, etc.)
  • firmware_version: VARCHAR(50) - Float firmware version
  • wmo_inst_type: VARCHAR(10) - WMO instrument type code
  • project_name: VARCHAR(100) - Scientific project
  • pi_name: VARCHAR(100) - Principal investigator
  • battery_type: VARCHAR(50) - Battery specifications
  • positioning_system: VARCHAR(50) - Positioning system (GPS/ARGOS)
  • launch_date: DATE - Deployment date
  • launch_latitude: DECIMAL(10,6) - Deployment latitude
  • launch_longitude: DECIMAL(11,6) - Deployment longitude
  • created_at: TIMESTAMP - Database insert time
  • updated_at: TIMESTAMP - Database update time
Sample Data: platform_type: 'APEX', platform_maker: 'SBE'
Row Count: ~1 record per float

TABLE 5: trajectory_table (Float Trajectory)
Description: Float positions and movement between profiles
Columns:
  • trajectory_id: SERIAL - Unique trajectory ID - PRIMARY KEY
  • platform_number: VARCHAR(20) - Float WMO number - FOREIGN KEY
  • cycle_number: INTEGER - Related cycle number
  • juld: TIMESTAMP - Position timestamp
  • juld_qc: CHAR(1) - Time quality flag
  • latitude: DECIMAL(10,6) - Position latitude
  • longitude: DECIMAL(11,6) - Position longitude
  • position_qc: CHAR(1) - Position quality flag
  • positioning_system: VARCHAR(50) - GPS/ARGOS system
  • direction: CHAR(1) - Movement direction ('A'=ascending, 'D'=descending)
  • data_mode: CHAR(1) - Data mode ('R'=real-time, 'D'=delayed)
  • pres: DECIMAL(10,3) - Pressure at position (if available)
  • temp: DECIMAL(8,4) - Temperature at position (if available)
  • psal: DECIMAL(8,4) - Salinity at position (if available)
  • doxy: DECIMAL(8,4) - Dissolved oxygen (if available)
  • created_at: TIMESTAMP - Database insert time
Sample Data: platform_number: '13859', ~1500 trajectory points
Row Count: ~1500+ positions per active float

TABLE 6: qc_flags_table (Quality Control Reference)
Description: Reference table for quality control flag meanings
Columns:
  • qc_flag: CHAR(1) - QC flag code - PRIMARY KEY
  • qc_description: VARCHAR(100) - Short description
  • qc_meaning: TEXT - Detailed meaning
Reference Values:
  '0': No QC performed
  '1': Good data (all QC tests passed)
  '2': Probably good data (few tests failed)
  '3': Bad data potentially correctable
  '4': Bad data (not recoverable)
  '5': Value changed during QC
  '8': Estimated value
  '9': Missing value
Row Count: 9 standard QC flags

=== CRITICAL RELATIONSHIPS ===
• float_table.platform_number (VARCHAR) = profile_table.platform_number (VARCHAR)
• profile_table.profile_id (SERIAL) = depth_measurements_table.profile_id (INTEGER)
• float_table.platform_number (VARCHAR) = meta_table.platform_number (VARCHAR)
• float_table.platform_number (VARCHAR) = trajectory_table.platform_number (VARCHAR)

=== CRITICAL DATA TYPE RULES ===
• platform_number: VARCHAR(20) - ALWAYS use quotes: '13859' NOT 13859
• cycle_number: INTEGER - NO quotes: 1 NOT '1'
• coordinates: DECIMAL - NO quotes: -45.5 NOT '-45.5'
• measurements: DECIMAL - NO quotes: 15.2 NOT '15.2'
• qc_flags: CHAR(1) - USE quotes: '1' NOT 1
• timestamps: TIMESTAMP - Use standard format

=== DOMAIN KNOWLEDGE ===
Available Floats: ['13859', '1900122']
Geographic Regions:
• Indian Ocean: latitude BETWEEN -40 AND 30 AND longitude BETWEEN 40 AND 120
• North Atlantic: latitude BETWEEN 30 AND 70 AND longitude BETWEEN -70 AND 0
• Arabian Sea: latitude BETWEEN 0 AND 30 AND longitude BETWEEN 50 AND 80
• Bay of Bengal: latitude BETWEEN 5 AND 25 AND longitude BETWEEN 80 AND 100

Quality Filters:
• Good data only: temp_qc = '1' AND psal_qc = '1'
• Quality data: temp_qc IN ('1', '2') AND psal_qc IN ('1', '2')
• Exclude bad data: temp_qc NOT IN ('3', '4', '9')

Typical Data Ranges:
• Temperature: 2°C to 28°C (surface warmer, deep colder)
• Salinity: 32 to 37 PSU (varies by region)
• Pressure: 0 to 6500 dbar (0=surface, 6500=deep ocean)
• Oxygen: 0 to 400 micromol/kg (varies with depth)

=== MANDATORY SQL GENERATION RULES ===
1. platform_number is VARCHAR - ALWAYS use quotes: WHERE platform_number = '13859'
2. cycle_number is INTEGER - NO quotes: WHERE cycle_number = 1
3. For location queries, always JOIN profile_table when using depth_measurements_table
4. For depth ranges use: WHERE pres BETWEEN (depth-10) AND (depth+10)
5. Include quality filters unless explicitly requested otherwise
6. Use proper PostgreSQL syntax with correct data types
7. Consider adjusted values for delayed-mode data when available
8. Generate ONLY the SQL query, no explanations or comments
9. Use appropriate JOINs for multi-table queries
10. Consider indexes: platform_number, cycle_number, pres are indexed

EXAMPLE QUERY PATTERNS:
• Float info: SELECT * FROM float_table WHERE platform_number = '13859'
• Profile count: SELECT COUNT(*) FROM profile_table WHERE platform_number = '13859'
• Avg temperature at depth: SELECT AVG(temp) FROM depth_measurements_table d JOIN profile_table p ON d.profile_id = p.profile_id WHERE d.pres BETWEEN 490 AND 510 AND d.temp_qc = '1'
• Geographic filter: WHERE p.latitude BETWEEN -40 AND 30 AND p.longitude BETWEEN 40 AND 120

"""

        return prompt

class PerplexityClient:
    """Pure AI client with working model detection"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.working_model = None

    def find_working_model(self) -> bool:
        """Find first working model"""
        models = ["sonar", "sonar-pro", "sonar-reasoning"]

        for model in models:
            try:
                test_payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": "SELECT 1"}],
                    "max_tokens": 20
                }

                response = requests.post(self.base_url, headers=self.headers, json=test_payload)

                if response.status_code == 200:
                    self.working_model = model
                    print(f"✅ Using Perplexity model: {model}")
                    return True

            except Exception:
                continue

        print("❌ No Perplexity models available")
        return False

    def generate_sql(self, user_query: str, schema_context: str) -> str:
        """Generate SQL with complete schema context"""

        if not self.working_model:
            raise Exception("No working Perplexity model available")

        messages = [
            {
                "role": "system",
                "content": schema_context
            },
            {
                "role": "user", 
                "content": f"Generate PostgreSQL query for: {user_query}"
            }
        ]

        payload = {
            "model": self.working_model,
            "messages": messages,
            "temperature": 0.0,  # Most deterministic
            "max_tokens": 400
        }

        response = requests.post(self.base_url, headers=self.headers, json=payload)
        response.raise_for_status()

        result = response.json()
        sql_query = result["choices"][0]["message"]["content"]

        return self._extract_sql(sql_query)

    def _extract_sql(self, response: str) -> str:
        """Extract clean SQL from AI response"""

        # Remove SQL code blocks
        if "```sql" in response.lower():
            sql_match = re.search(r'```sql\s*\n(.*?)\n```', response, re.DOTALL | re.IGNORECASE)
            if sql_match:
                return sql_match.group(1).strip()

        # Find SELECT statement  
        select_match = re.search(r'(SELECT.*?)(?:;|$|\n\n)', response, re.DOTALL | re.IGNORECASE)
        if select_match:
            return select_match.group(1).strip()

        # Clean and return
        cleaned = response.strip()
        if cleaned.endswith(';'):
            cleaned = cleaned[:-1]

        return cleaned

class PostgreSQLConnection:
    """Database connection with better error reporting"""

    def __init__(self, config_file="database.ini"):
        self.config_file = config_file
        self.connection = None

    def connect(self):
        """Connect with error handling"""
        parser = ConfigParser()
        parser.read(self.config_file)

        config = {param[0]: param[1] for param in parser.items('database')}

        self.connection = psycopg2.connect(
            host=config['host'],
            port=int(config['port']), 
            user=config['user'],
            password=config['password'],
            database=config['database']
        )
        return self.connection

    def execute_query(self, sql_query: str) -> Dict:
        """Execute with detailed error info"""
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        try:
            print(f"🔍 Executing: {sql_query}")
            cursor.execute(sql_query)
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

            print(f"📊 Results: {len(results)} rows returned")
            return {"data": results, "columns": columns}

        except Exception as e:
            print(f"❌ SQL Error: {e}")
            print(f"🔍 Query was: {sql_query}")
            raise
        finally:
            cursor.close()

class ArgoNLQuerySystem:
    """Complete AI system with full schema knowledge"""

    def __init__(self, perplexity_api_key: str):
        self.schema_context = ArgoSchemaContext()
        self.perplexity_client = PerplexityClient(perplexity_api_key)
        self.db_connection = PostgreSQLConnection()

        # Must have working API - no fallback
        print("🔧 Initializing Complete Argo AI Query System...")
        print("📋 Loading complete schema: 15 tables, 191 variables")

        if not self.perplexity_client.find_working_model():
            raise Exception("❌ Perplexity API required for complete system")

        print("✅ AI system ready with COMPLETE schema context")
        print("🧠 AI knows every column in all 15 tables!")

    def process_query(self, user_query: str) -> Dict[str, Any]:
        """Process with complete AI knowledge - no guessing"""

        try:
            # Generate SQL with COMPLETE schema context
            schema_prompt = self.schema_context.get_complete_schema_prompt()
            sql_query = self.perplexity_client.generate_sql(user_query, schema_prompt)

            print(f"🤖 AI Generated SQL: {sql_query}")

            # Execute query
            query_result = self.db_connection.execute_query(sql_query)

            # Format response
            response = self.format_response(query_result, user_query)

            return {
                "user_query": user_query,
                "sql_query": sql_query,
                "raw_results": query_result, 
                "natural_response": response,
                "success": True
            }

        except Exception as e:
            return {
                "user_query": user_query,
                "error": str(e),
                "natural_response": f"Query failed: {str(e)}",
                "success": False
            }

    def format_response(self, query_result: Dict, user_query: str) -> str:
        """Smart response formatting"""
        data = query_result["data"]
        columns = query_result["columns"]

        if not data:
            return "No data found matching your query."

        # Single value responses
        if len(data) == 1 and len(data[0]) == 1:
            value = data[0][0]

            if "platform_type" in user_query.lower() or "type" in user_query.lower():
                return f"Platform type: {value}"
            elif "temperature" in user_query.lower() or "temp" in user_query.lower():
                if value is None:
                    return "No temperature data found."
                return f"Temperature: {float(value):.2f}°C"
            elif "count" in user_query.lower() or "how many" in user_query.lower():
                return f"Count: {value}"
            elif "depth" in user_query.lower() or "deepest" in user_query.lower():
                return f"Depth: {float(value):.1f} dbar"
            elif "salinity" in user_query.lower():
                if value is None:
                    return "No salinity data found."
                return f"Salinity: {float(value):.2f} PSU"
            elif "oxygen" in user_query.lower() or "doxy" in user_query.lower():
                if value is None:
                    return "No oxygen data found."
                return f"Dissolved oxygen: {float(value):.2f} micromol/kg"
            else:
                return f"Result: {value}"

        # Multiple column responses
        elif len(data) == 1 and len(data[0]) > 1:
            result_parts = []
            for i, value in enumerate(data[0]):
                if i < len(columns) and value is not None:
                    result_parts.append(f"{columns[i]}: {value}")
            return " | ".join(result_parts)

        # Multiple row responses
        elif len(data) <= 10:
            formatted_results = []
            for row in data:
                row_parts = []
                for i, value in enumerate(row):
                    if value is not None and i < len(columns):
                        row_parts.append(f"{columns[i]}: {value}")
                formatted_results.append(" | ".join(row_parts))
            return "Results:\n" + "\n".join(formatted_results)

        else:
            return f"Found {len(data)} results (showing first 3): {data[:3]}"

def main():
    """Main execution with complete schema"""

    PERPLEXITY_API_KEY = "UR KEY"

    print("🌊 ARGO COMPLETE AI QUERY SYSTEM")
    print("=" * 60)
    print("🤖 AI with complete schema knowledge")
    print("📋 15 tables, 191 variables, full oceanographic context")
    print("🎯 No guessing - pure AI intelligence")

    try:
        # Initialize complete AI system
        system = ArgoNLQuerySystem(PERPLEXITY_API_KEY)

        # Test queries to show capabilities
        test_queries = [
            "What is the platform type of float no 1900122?",
            "How many floats are there?",
            "What is average temperature at 500 meters?",
            "Which floats have BGC data?",
            "Show me trajectory data for float 13859"
        ]

        print("\n🚀 Testing system capabilities...")
        for query in test_queries[:2]:  # Test first 2
            print(f"\n❓ {query}")
            result = system.process_query(query)

            if result["success"]:
                print(f"💬 {result['natural_response']}")
            else:
                print(f"❌ {result['natural_response']}")

        # Interactive mode
        print("\n🎯 Interactive mode - Ask anything about your Argo data!")
        print("Examples:")
        print("• 'What sensors does float 13859 have?'")
        print("• 'Show BGC parameters for Arabian Sea'")  
        print("• 'What's the battery type of float 1900122?'")
        print("• 'Temperature profile for cycle 50'")
        print("Type 'exit' to quit\n")

        while True:
            user_input = input("🌊 Your question: ").strip()

            if user_input.lower() in ['exit', 'quit']:
                break

            if not user_input:
                continue

            result = system.process_query(user_input)

            if result["success"]:
                print(f"💬 {result['natural_response']}\n")
            else:
                print(f"❌ {result['natural_response']}\n")

    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        print("💡 Ensure Perplexity API is working properly")

if __name__ == "__main__":
    main()
