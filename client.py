#!/usr/bin/env python3
"""
Concise Argo Perplexity Client - Direct, Short Responses
Updated for New Simplified Schema (2025-09-13)
Provides brief, natural responses instead of lengthy explanations
"""

import asyncio
import json
import requests
import psycopg2
from configparser import ConfigParser
from typing import Dict, Any, List

# Try to import MCP - if not available, we'll use direct implementation
try:
    from mcp import ClientSession
    from mcp.client import stdio
    MCP_AVAILABLE = True
    print("✅ MCP SDK found - using full MCP integration")
except ImportError:
    MCP_AVAILABLE = False
    print("⚠️ MCP SDK not available - using direct implementation")

class ArgoSchemaProvider:
    """Provides schema context directly - UPDATED FOR NEW SIMPLIFIED SCHEMA"""

    def __init__(self):
        self.schema = """
ARGO OCEANOGRAPHIC FLOAT DATABASE SCHEMA - NEW SIMPLIFIED VERSION (2025-09-13)

=== SMART TABLE SELECTION GUIDE ===

🎯 CRITICAL: Use the RIGHT table for each query type!

BASIC FLOAT INFO → float_table (SIMPLIFIED):
• platform_number, project_name, wmo_inst_type, positioning_system
• Example: "What project is float part of?" → SELECT project_name FROM float_table

FLOAT SPECIFICATIONS & DEPLOYMENT → meta_table (COMPREHENSIVE):
• platform_type, platform_maker, firmware_version, battery_type
• pi_name, launch_date, launch_latitude, launch_longitude
• date_creation, date_update, serial numbers
• Example: "What is platform type?" → SELECT platform_type FROM meta_table
• Example: "Who is the PI?" → SELECT pi_name FROM meta_table
• Example: "Where was float launched?" → SELECT launch_latitude, launch_longitude FROM meta_table

CURRENT FLOAT LOCATIONS → profile_table:
• "floats in region" queries → use profile_table (current locations)
• latitude, longitude, cycle_number, juld, direction, data_mode
• Enhanced with QC flags: profile_pres_qc, profile_temp_qc, profile_psal_qc
• Example: "floats in Indian Ocean" → FROM profile_table WHERE latitude BETWEEN...

SCIENTIFIC MEASUREMENTS → depth_measurements_table (ENHANCED):
• Core: temp, psal, pres with QC flags
• BGC: doxy, nitrate, ph_in_situ_total with QC flags
• Adjusted values: *_adjusted columns with error estimates
• Example: "oxygen data" → SELECT doxy FROM depth_measurements_table WHERE doxy IS NOT NULL

TRAJECTORY DATA → trajectory_table (NEW):
• Float movement over time with surface measurements
• juld, latitude, longitude, pres, temp, psal, doxy
• Example: "float movement" → FROM trajectory_table ORDER BY juld

SENSORS → sensor_table:
• sensor, sensor_maker, sensor_model, sensor_serial_no
• Example: "what sensors?" → FROM sensor_table

=== TABLE DETAILS ===

float_table (SIMPLIFIED - Basic ID only):
• platform_number: VARCHAR(20) PRIMARY KEY
• project_name: VARCHAR(100) - Project name
• wmo_inst_type: VARCHAR(10) - WMO instrument type
• positioning_system: VARCHAR(50) - GPS/ARGOS system

meta_table (COMPREHENSIVE - All metadata):
• platform_number: VARCHAR(20) - FOREIGN KEY
• platform_type: VARCHAR(50) - Float type (APEX, ARVOR) ← MOVED HERE
• platform_maker: VARCHAR(100) - Manufacturer (SBE, NKE)
• pi_name: VARCHAR(100) - Principal investigator ← MOVED HERE
• launch_latitude: DECIMAL(10,6) - Deployment latitude ← MOVED HERE
• launch_longitude: DECIMAL(11,6) - Deployment longitude ← MOVED HERE
• launch_date: DATE - Deployment date ← MOVED HERE
• battery_type: VARCHAR(50) - Battery specifications
• firmware_version: VARCHAR(50) - Firmware version
• date_creation: TIMESTAMP - File creation date from NetCDF
• date_update: TIMESTAMP - File update date

profile_table (ENHANCED - More QC info):
• platform_number: VARCHAR(20) - FOREIGN KEY
• latitude: DECIMAL(10,6) - Current profile location ← USE FOR REGIONAL QUERIES
• longitude: DECIMAL(11,6) - Current profile location
• juld: TIMESTAMP - Profile date/time (converted from Julian)
• direction: CHAR(1) - A=ascending, D=descending
• data_mode: CHAR(1) - R=real-time, D=delayed, A=adjusted
• profile_pres_qc: CHAR(1) - Pressure profile QC ← NEW
• profile_temp_qc: CHAR(1) - Temperature profile QC ← NEW
• profile_psal_qc: CHAR(1) - Salinity profile QC ← NEW

depth_measurements_table (ENHANCED - BGC + Adjusted values):
• platform_number: VARCHAR(20) - For quick filtering
• pres: DECIMAL(10,3) - Pressure (dbar ≈ depth)
• temp: DECIMAL(8,4) - Temperature (°C)
• psal: DECIMAL(8,4) - Salinity (PSU)
• doxy: DECIMAL(8,4) - Dissolved oxygen (micromol/kg) ← ENHANCED
• nitrate: DECIMAL(8,4) - Nitrate concentration ← NEW
• ph_in_situ_total: DECIMAL(8,4) - pH in situ total scale ← NEW
• *_qc: CHAR(1) - Quality flags for all parameters
• *_adjusted: DECIMAL - Adjusted values ← NEW
• *_adjusted_error: DECIMAL - Error estimates ← NEW

trajectory_table (NEW TABLE):
• platform_number: VARCHAR(20) - FOREIGN KEY
• cycle_number: INTEGER - Float cycle
• juld: TIMESTAMP - Position timestamp
• latitude: DECIMAL(10,6) - Position latitude
• longitude: DECIMAL(11,6) - Position longitude
• pres: DECIMAL(10,3) - Surface pressure
• temp: DECIMAL(8,4) - Surface temperature
• psal: DECIMAL(8,4) - Surface salinity
• doxy: DECIMAL(8,4) - Surface oxygen
• station_parameters: JSONB - Additional parameters

=== CRITICAL SCHEMA CHANGES ===
1. float_table SIMPLIFIED - only basic ID info now
2. meta_table ENHANCED - contains ALL metadata (PI, launch coords, platform specs)
3. BGC parameters ADDED - oxygen, nitrate, pH with QC flags
4. Adjusted values ADDED - scientifically corrected measurements
5. trajectory_table ADDED - float movement tracking

=== CRITICAL RULES ===
1. Platform specs (type, maker, PI) → ALWAYS use meta_table
2. Launch coordinates → meta_table.launch_latitude/longitude
3. Current locations → profile_table.latitude/longitude
4. BGC data → depth_measurements_table (doxy, nitrate, ph_in_situ_total)
5. platform_number is VARCHAR → ALWAYS use quotes: '13859' NOT 13859

=== EXAMPLE CORRECTIONS ===
❌ OLD: SELECT platform_type FROM float_table (will be NULL)
✅ NEW: SELECT platform_type FROM meta_table

❌ OLD: SELECT pi_name FROM float_table (will be NULL) 
✅ NEW: SELECT pi_name FROM meta_table

❌ OLD: SELECT launch_latitude FROM float_table (will be NULL)
✅ NEW: SELECT launch_latitude FROM meta_table

Geographic Regions:
• Indian Ocean: latitude BETWEEN -40 AND 30 AND longitude BETWEEN 40 AND 120
• North Atlantic: latitude BETWEEN 30 AND 70 AND longitude BETWEEN -70 AND 0

Available Floats: ['13859', '1900122']
Data Status: ~300 profiles, ~30,000+ measurements, ~2,000+ trajectory points
"""

class ArgoQueryClient:
    """Concise Argo query client with short, direct responses - UPDATED"""

    def __init__(self, perplexity_api_key: str, db_config: str = "database.ini"):
        self.perplexity_api_key = perplexity_api_key
        self.db_config = db_config
        self.schema_provider = ArgoSchemaProvider()
        self.connection = None

    def get_db_connection(self):
        """Get database connection"""
        if not self.connection:
            parser = ConfigParser()
            parser.read(self.db_config)
            config = {param[0]: param[1] for param in parser.items('database')}

            self.connection = psycopg2.connect(
                host=config['host'],
                port=int(config['port']),
                user=config['user'],
                password=config['password'],
                database=config['database']
            )
        return self.connection

    def execute_query(self, sql_query: str) -> Dict[str, Any]:
        """Execute SQL query"""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(sql_query)
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

            return {
                "success": True,
                "data": results,
                "columns": columns,
                "row_count": len(results)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": sql_query
            }
        finally:
            cursor.close()

    def generate_sql_with_perplexity(self, user_query: str) -> str:
        """Generate SQL using Perplexity with NEW schema context"""

        system_prompt = f"""You are an expert PostgreSQL query generator for an Argo oceanographic float database.

IMPORTANT: This database uses a NEW SIMPLIFIED SCHEMA (2025-09-13). Pay attention to table changes:

{self.schema_provider.schema}

Generate ONLY the SQL query for the user's question. Use proper table selection based on the NEW schema guidance above.

CRITICAL REMINDERS:
- Platform specs (type, PI, launch coords) → meta_table 
- Current locations → profile_table
- Basic float info → float_table (simplified)
- BGC parameters available: doxy, nitrate, ph_in_situ_total
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate SQL for: {user_query}"}
        ]

        payload = {
            "model": "sonar",
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 400
        }

        headers = {
            "Authorization": f"Bearer {self.perplexity_api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post("https://api.perplexity.ai/chat/completions", 
                                   headers=headers, json=payload)
            response.raise_for_status()

            result = response.json()
            sql_query = result["choices"][0]["message"]["content"]

            # Clean SQL
            return self._extract_sql(sql_query)

        except Exception as e:
            raise Exception(f"Perplexity API error: {e}")

    def generate_concise_response(self, user_query: str, data: List, columns: List, sql_query: str) -> str:
        """Generate concise, direct response using Perplexity AI"""

        # Format data for context
        data_context = ""
        if data and columns:
            if len(data) == 1 and len(data[0]) == 1:
                # Single value
                data_context = f"Query result: {data[0][0]}"
            elif len(data) <= 5:
                # Multiple rows, format nicely
                data_context = "Query results:\n"
                for row in data:
                    row_data = []
                    for i, value in enumerate(row):
                        if value is not None and i < len(columns):
                            row_data.append(f"{columns[i]}: {value}")
                    if row_data:
                        data_context += f"  • {' | '.join(row_data)}\n"
            else:
                # Too many results
                data_context = f"Query returned {len(data)} results. Sample: {data[:3]}"

        system_prompt = """You are a direct, concise AI assistant for Argo oceanographic data queries.

IMPORTANT GUIDELINES:
- Keep responses SHORT and DIRECT
- Maximum 1-2 sentences
- Answer in this exact format for platform type queries: "The platform type of float [NUMBER] is [TYPE]."
- Answer in this exact format for PI queries: "The PI of float [NUMBER] is [NAME]."
- Answer in this exact format for count queries: "There are [NUMBER] floats [CONDITION]."
- Answer in this exact format for location queries: "Float [NUMBER] is located at [LAT], [LON]."
- For BGC data: "The oxygen/nitrate/pH level is [VALUE] [UNITS]."
- DO NOT provide long explanations or background information
- DO NOT use technical jargon or educational content
- Be factual and brief

Examples of good responses:
- "The platform type of float 13859 is APEX."
- "The PI of float 13859 is John Smith."
- "There are 2 floats in the Indian Ocean."
- "The average temperature is 15.5°C."
- "The oxygen level is 245.3 micromol/kg."
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""
User asked: "{user_query}"
SQL executed: {sql_query}
{data_context}

Provide a SHORT, DIRECT response (maximum 1-2 sentences).
"""}
        ]

        payload = {
            "model": "sonar",
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 50
        }

        headers = {
            "Authorization": f"Bearer {self.perplexity_api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post("https://api.perplexity.ai/chat/completions", 
                                   headers=headers, json=payload)
            response.raise_for_status()

            result = response.json()
            concise_response = result["choices"][0]["message"]["content"]

            return concise_response.strip()

        except Exception as e:
            # Fallback to simple formatted response if AI fails
            return self._simple_format_response(user_query, data, columns)

    def _simple_format_response(self, user_query: str, data: List, columns: List) -> str:
        """Simple formatting for direct responses - ENHANCED"""
        if not data:
            return "No data found."

        # Single value result with direct format
        if len(data) == 1 and len(data[0]) == 1:
            value = data[0][0]
            user_query_lower = user_query.lower()

            if value is None:
                return "No result found."
            elif "platform_type" in user_query_lower or "platform type" in user_query_lower:
                # Extract float number from query
                import re
                float_match = re.search(r'\b(\d+)\b', user_query)
                float_num = float_match.group(1) if float_match else "the float"
                return f"The platform type of float {float_num} is {value}."
            elif "pi" in user_query_lower and "name" in user_query_lower:
                import re
                float_match = re.search(r'\b(\d+)\b', user_query)
                float_num = float_match.group(1) if float_match else "the float"
                return f"The PI of float {float_num} is {value}."
            elif "project" in user_query_lower:
                return f"The project is {value}."
            elif "count" in user_query_lower or "how many" in user_query_lower:
                return f"There are {value} floats matching your query."
            elif "temperature" in user_query_lower:
                return f"The temperature is {float(value):.1f}°C."
            elif "salinity" in user_query_lower:
                return f"The salinity is {float(value):.1f} PSU."
            elif "oxygen" in user_query_lower or "doxy" in user_query_lower:
                return f"The oxygen level is {float(value):.1f} micromol/kg."
            elif "nitrate" in user_query_lower:
                return f"The nitrate level is {float(value):.1f} micromol/kg."
            elif "ph" in user_query_lower:
                return f"The pH is {float(value):.2f}."
            else:
                return f"The result is {value}."

        # Multiple results - keep brief
        elif len(data) <= 3:
            results = []
            for row in data:
                if len(row) >= 2:
                    results.append(f"{row[0]}: {row[1]}")
                else:
                    results.append(str(row[0]))
            return f"Results: {', '.join(results)}."
        else:
            return f"Found {len(data)} results."

    def _extract_sql(self, response: str) -> str:
        """Extract clean SQL from response"""
        import re

        # Remove SQL code blocks
        if "```sql" in response.lower():
            sql_match = re.search(r'```sql\s*\n(.*?)\n```', response, re.DOTALL | re.IGNORECASE)
            if sql_match:
                return sql_match.group(1).strip()

        # Find SELECT statement
        select_match = re.search(r'(SELECT.*?)(?:;|$)', response, re.DOTALL | re.IGNORECASE)
        if select_match:
            return select_match.group(1).strip()

        return response.strip()
    def validate_query(self, sql_query: str) -> Dict[str, Any]:
        """Basic query validation - UPDATED for new schema"""
        issues = []
        suggestions = []

        # Updated validation for new schema structure
        if any(field in sql_query for field in ["platform_type", "pi_name", "launch_latitude", "launch_longitude"]) and "float_table" in sql_query:
            issues.append("Metadata fields moved to meta_table in new schema")
            suggestions.append("Use: SELECT platform_type, pi_name FROM meta_table WHERE platform_number = '...'")

        if "launch_latitude" in sql_query or "launch_longitude" in sql_query:
            if any(word in sql_query.lower() for word in ["region", "ocean", "count"]):
                issues.append("For regional queries, use current profile locations from profile_table")
                suggestions.append("Use: SELECT ... FROM profile_table WHERE latitude BETWEEN ...")

        # Check data type usage
        import re
        if re.search(r'platform_number\s*=\s*\d+', sql_query):
            issues.append("platform_number is VARCHAR - use quotes around the value")
            suggestions.append("Use: platform_number = '13859' not platform_number = 13859")

        # Check for BGC parameter usage
        if any(bgc in sql_query for bgc in ["doxy", "nitrate", "ph_"]) and "depth_measurements_table" in sql_query:
            if "IS NOT NULL" not in sql_query:
                suggestions.append("Consider adding 'WHERE doxy IS NOT NULL' for BGC parameters")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions
        }

    def process_query(self, user_query: str) -> Dict[str, Any]:
        """Complete pipeline with concise response"""
        try:
            print("🤖 Generating SQL with Perplexity AI...")
            sql_query = self.generate_sql_with_perplexity(user_query)
            print(f"Generated SQL: {sql_query}")

            print("✅ Validating SQL...")
            validation = self.validate_query(sql_query)

            if not validation["is_valid"]:
                print("⚠️ Validation issues found:")
                for issue in validation["issues"]:
                    print(f"  - {issue}")
                for suggestion in validation["suggestions"]:
                    print(f"  💡 {suggestion}")

            print("🔍 Executing SQL...")
            result = self.execute_query(sql_query)

            if result["success"]:
                print("🤖 Generating concise response...")
                concise_response = self.generate_concise_response(
                    user_query, 
                    result["data"], 
                    result["columns"], 
                    sql_query
                )
            else:
                concise_response = f"Error: {result.get('error', 'Unknown error')}"

            return {
                "success": result["success"],
                "user_query": user_query,
                "sql_query": sql_query,
                "data": result.get("data", []),
                "columns": result.get("columns", []),
                "row_count": result.get("row_count", 0),
                "error": result.get("error"),
                "validation": validation,
                "natural_response": concise_response
            }

        except Exception as e:
            return {
                "success": False,
                "user_query": user_query,
                "error": str(e),
                "natural_response": f"Error: {str(e)}"
            }

def format_response(result: Dict[str, Any]) -> str:
    """Concise response formatting"""
    if "natural_response" in result:
        return result["natural_response"]

    # Fallback
    if not result["success"]:
        return f"Error: {result.get('error', 'Unknown error')}"

    return "Query completed."

def main():
    """Main application - concise responses"""
    PERPLEXITY_API_KEY = "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"

    print("🌊 CONCISE ARGO PERPLEXITY CLIENT - NEW SIMPLIFIED SCHEMA")
    print("=" * 65)
    print("🔧 Updated for 2025-09-13 simplified schema...")

    client = ArgoQueryClient(PERPLEXITY_API_KEY)

    # Updated test queries for new schema
    test_queries = [
        "What is the platform type of float 1900122?",
        "Who is the PI of float 13859?",
        "What project is float 13859 part of?",
        "Where was float 13859 launched?",
        "How many floats are operating in Indian Ocean?",
        "What is the average oxygen level in the upper 100 meters?",
    ]

    print("\n🚀 Testing system with concise responses...")
    for query in test_queries:
        print(f"\n❓ Query: {query}")

        result = client.process_query(query)
        response = format_response(result)
        print(f"🤖 {response}")

    # Interactive mode
    print("\n🎯 Interactive mode - Get direct, concise answers!")
    print("New features: PI names, launch coords, BGC data (oxygen, nitrate, pH)")
    print("Type 'exit' to quit\n")

    while True:
        try:
            user_input = input("🌊 Your question: ").strip()

            if user_input.lower() in ['exit', 'quit', 'q']:
                break

            if not user_input:
                continue

            result = client.process_query(user_input)
            response = format_response(result)
            print(f"🤖 {response}\n")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

    print("👋 Thanks for using the Updated Concise Argo Query System!")

if __name__ == "__main__":
    main()
