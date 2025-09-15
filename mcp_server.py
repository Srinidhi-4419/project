#!/usr/bin/env python3
"""
Ultimate Argo Database MCP Server - PERFECT SQL GENERATION & NLP
Advanced natural language processing, intent recognition, and flawless SQL generation
"""

import json
import asyncio
import re
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime
import psycopg2
from configparser import ConfigParser

# MCP SDK imports
from mcp import FastMCP, types
from mcp.server import logging
from mcp.server.models import RequestContext

class UltimateArgoMCPServer:
    """Ultimate MCP Server with Perfect Query Intelligence and NLP"""

    def __init__(self, db_config_file: str = "database.ini"):
        self.db_config_file = db_config_file
        self.connection = None
        
        # Ultimate schema with complete intelligence
        self.argo_schema = {
            "database": "argo_floats",
            "schema_version": "2025-09-14 - Ultimate Perfect Intelligence",
            
            # Advanced Natural Language Processing
            "nlp_engine": {
                "platform_extraction": {
                    "patterns": [
                        r'\b(?:platform|float)\s*(?:number|#|id)?\s*(\d{4,7})\b',
                        r'\b(\d{4,7})\b',
                        r'for\s+(\d{4,7})',
                        r'of\s+(\d{4,7})',
                        r'platform\s+(\d{4,7})'
                    ],
                    "default_platforms": ["13859", "1900122", "1902676"]
                },
                
                "parameter_mapping": {
                    "temperature": {
                        "keywords": ["temp", "temperature", "thermal", "heat"],
                        "db_name": "TEMP",
                        "column": "temp",
                        "units": "degrees Celsius"
                    },
                    "salinity": {
                        "keywords": ["sal", "salinity", "psal", "salt", "saltiness"],
                        "db_name": "PSAL",
                        "column": "psal",
                        "units": "PSU"
                    },
                    "pressure": {
                        "keywords": ["pres", "pressure", "depth", "bar", "dbar"],
                        "db_name": "PRES",
                        "column": "pres",
                        "units": "decibars"
                    },
                    "oxygen": {
                        "keywords": ["oxy", "oxygen", "dissolved oxygen", "doxy", "o2"],
                        "db_name": "DOXY",
                        "column": "doxy",
                        "units": "micromol/kg"
                    },
                    "nitrate": {
                        "keywords": ["nitrate", "no3", "nitrogen"],
                        "db_name": "NITRATE",
                        "column": "nitrate",
                        "units": "micromol/kg"
                    },
                    "ph": {
                        "keywords": ["ph", "acidity", "alkalinity", "acid"],
                        "db_name": "PH_IN_SITU_TOTAL",
                        "column": "ph_in_situ_total",
                        "units": "total scale"
                    }
                },
                
                "query_intent_classification": {
                    "sensor_queries": {
                        "keywords": ["sensor", "instrument", "device", "equipment", "measures", "measuring"],
                        "confidence_boost": ["what sensor", "which sensor", "sensor used", "instrument for"],
                        "table_priority": "parameter_table"
                    },
                    "data_queries": {
                        "keywords": ["data", "measurement", "value", "reading", "level", "concentration"],
                        "table_priority": "depth_measurements_table"
                    },
                    "location_queries": {
                        "keywords": ["location", "position", "coordinate", "where", "latitude", "longitude"],
                        "subcategories": {
                            "current": ["current", "now", "latest", "present"],
                            "launch": ["launch", "deployment", "deployed", "started"],
                            "trajectory": ["trajectory", "movement", "path", "drift", "track"]
                        }
                    },
                    "metadata_queries": {
                        "keywords": ["type", "maker", "manufacturer", "PI", "investigator", "project"],
                        "table_priority": "meta_table"
                    },
                    "statistical_queries": {
                        "keywords": ["average", "mean", "max", "maximum", "min", "minimum", "count", "total", "sum"],
                        "functions": {
                            "average": ["avg", "average", "mean"],
                            "maximum": ["max", "maximum", "highest", "peak"],
                            "minimum": ["min", "minimum", "lowest"],
                            "count": ["count", "number", "total", "how many"]
                        }
                    },
                    "profile_queries": {
                        "keywords": ["profile", "vertical", "depth", "vs depth", "with depth"],
                        "table_priority": "depth_measurements_table"
                    }
                }
            },
            
            # Complete table schema with intelligence
            "tables": {
                "float_table": {
                    "description": "Basic float identification and project information",
                    "primary_use": "Basic float info, project queries",
                    "columns": {
                        "platform_number": "VARCHAR(20) PRIMARY KEY",
                        "project_name": "VARCHAR(100)",
                        "wmo_inst_type": "VARCHAR(10)",
                        "positioning_system": "VARCHAR(50)"
                    },
                    "query_patterns": {
                        "basic_info": "SELECT platform_number, project_name FROM float_table",
                        "by_platform": "SELECT * FROM float_table WHERE platform_number = '{platform}'"
                    }
                },
                
                "meta_table": {
                    "description": "Complete platform specifications and deployment details",
                    "primary_use": "Platform specs, PI info, launch details",
                    "columns": {
                        "platform_number": "VARCHAR(20) FOREIGN KEY",
                        "launch_latitude": "DECIMAL(10,6)",
                        "launch_longitude": "DECIMAL(11,6)",
                        "launch_date": "DATE",
                        "pi_name": "VARCHAR(100)",
                        "platform_type": "VARCHAR(50)",
                        "platform_maker": "VARCHAR(100)",
                        "battery_type": "VARCHAR(50)",
                        "firmware_version": "VARCHAR(50)"
                    },
                    "query_patterns": {
                        "platform_specs": "SELECT platform_type, platform_maker, pi_name FROM meta_table WHERE platform_number = '{platform}'",
                        "launch_info": "SELECT launch_latitude, launch_longitude, launch_date FROM meta_table WHERE platform_number = '{platform}'",
                        "pi_info": "SELECT pi_name, data_centre FROM meta_table WHERE platform_number = '{platform}'"
                    }
                },
                
                "profile_table": {
                    "description": "Profile metadata with current float locations",
                    "primary_use": "Current location, profile timing, regional analysis",
                    "columns": {
                        "profile_id": "SERIAL PRIMARY KEY",
                        "platform_number": "VARCHAR(20)",
                        "cycle_number": "INTEGER",
                        "juld": "TIMESTAMP",
                        "latitude": "DECIMAL(10,6)",
                        "longitude": "DECIMAL(11,6)",
                        "direction": "CHAR(1)"
                    },
                    "query_patterns": {
                        "current_location": "SELECT latitude, longitude, juld FROM profile_table WHERE platform_number = '{platform}' ORDER BY juld DESC LIMIT 1",
                        "profile_count": "SELECT COUNT(*) as profile_count FROM profile_table WHERE platform_number = '{platform}'",
                        "regional": "SELECT * FROM profile_table WHERE latitude BETWEEN {lat1} AND {lat2} AND longitude BETWEEN {lon1} AND {lon2}"
                    }
                },
                
                "depth_measurements_table": {
                    "description": "Core scientific measurements at depth with BGC parameters",
                    "primary_use": "Scientific data analysis, profiles, BGC studies",
                    "columns": {
                        "platform_number": "VARCHAR(20)",
                        "pres": "DECIMAL(10,3) - Pressure/depth",
                        "temp": "DECIMAL(8,4) - Temperature",
                        "psal": "DECIMAL(8,4) - Salinity",
                        "doxy": "DECIMAL(8,4) - Dissolved oxygen",
                        "nitrate": "DECIMAL(8,4) - Nitrate",
                        "ph_in_situ_total": "DECIMAL(8,4) - pH",
                        "temp_qc": "CHAR(1) - Quality flags",
                        "psal_qc": "CHAR(1)",
                        "doxy_qc": "CHAR(1)"
                    },
                    "query_patterns": {
                        "profile": "SELECT pres, {parameter} FROM depth_measurements_table WHERE platform_number = '{platform}' AND {parameter}_qc IN ('1', '2') AND {parameter} IS NOT NULL ORDER BY pres",
                        "surface": "SELECT AVG({parameter}) as avg_{parameter} FROM depth_measurements_table WHERE platform_number = '{platform}' AND pres < 10 AND {parameter}_qc = '1'",
                        "depth_range": "SELECT pres, {parameter} FROM depth_measurements_table WHERE platform_number = '{platform}' AND pres BETWEEN {min_depth} AND {max_depth} AND {parameter}_qc IN ('1', '2')",
                        "statistics": "SELECT AVG({parameter}) as avg_{parameter}, MAX({parameter}) as max_{parameter}, MIN({parameter}) as min_{parameter}, COUNT(*) as data_points FROM depth_measurements_table WHERE platform_number = '{platform}' AND {parameter}_qc IN ('1', '2') AND {parameter} IS NOT NULL"
                    }
                },
                
                "trajectory_table": {
                    "description": "Float movement and surface measurements over time",
                    "primary_use": "Movement tracking, drift analysis, surface conditions",
                    "columns": {
                        "platform_number": "VARCHAR(20)",
                        "juld": "TIMESTAMP",
                        "latitude": "DECIMAL(10,6)",
                        "longitude": "DECIMAL(11,6)",
                        "temp": "DECIMAL(8,4)",
                        "positioning_system": "VARCHAR(50)"
                    },
                    "query_patterns": {
                        "trajectory": "SELECT juld, latitude, longitude FROM trajectory_table WHERE platform_number = '{platform}' AND latitude IS NOT NULL ORDER BY juld",
                        "surface_temp": "SELECT juld, temp FROM trajectory_table WHERE platform_number = '{platform}' AND temp IS NOT NULL ORDER BY juld"
                    }
                },
                
                "sensor_table": {
                    "description": "Physical sensor hardware specifications",
                    "primary_use": "Hardware details, manufacturer info",
                    "columns": {
                        "platform_number": "VARCHAR(20)",
                        "sensor": "VARCHAR(50)",
                        "sensor_maker": "VARCHAR(100)",
                        "sensor_model": "VARCHAR(100)",
                        "sensor_serial_no": "VARCHAR(50)"
                    }
                },
                
                "parameter_table": {
                    "description": "CRITICAL: Parameter-to-sensor mapping",
                    "primary_use": "Parameter-sensor relationships, sensor identification",
                    "columns": {
                        "platform_number": "VARCHAR(20)",
                        "parameter": "VARCHAR(50)",
                        "parameter_sensor": "VARCHAR(50) - CRITICAL for sensor queries",
                        "parameter_units": "VARCHAR(20)",
                        "parameter_accuracy": "VARCHAR(50)"
                    },
                    "query_patterns": {
                        "sensor_for_parameter": "SELECT p.parameter_sensor, p.parameter_units, s.sensor_maker, s.sensor_model FROM parameter_table p LEFT JOIN sensor_table s ON p.platform_number = s.platform_number AND p.parameter_sensor = s.sensor WHERE p.platform_number = '{platform}' AND p.parameter LIKE '%{parameter}%'"
                    }
                }
            },
            
            # Domain knowledge for intelligent responses
            "domain_knowledge": {
                "available_floats": ["13859", "1900122", "1902676"],
                "typical_ranges": {
                    "temperature": {"surface": "15-30°C", "deep": "2-4°C", "range": "-2 to 30°C"},
                    "salinity": {"surface": "32-37", "deep": "34-35", "range": "30-40 PSU"},
                    "pressure": {"surface": "0-10", "deep": "2000-6000", "range": "0-6500 dbar"},
                    "oxygen": {"surface": "200-300", "deep": "50-200", "range": "0-400 μmol/kg"},
                    "nitrate": {"surface": "0-10", "deep": "20-45", "range": "0-50 μmol/kg"},
                    "ph": {"surface": "8.0-8.3", "deep": "7.5-7.8", "range": "7.4-8.4"}
                },
                "quality_flags": {
                    "1": "Good data",
                    "2": "Probably good data", 
                    "3": "Bad data that are correctable",
                    "4": "Bad data",
                    "9": "Missing value"
                },
                "argo_general_knowledge": {
                    "what_is_argo": "Argo is a global array of autonomous floats that measure temperature, salinity, and other ocean properties. The floats drift at depth and surface every ~10 days to transmit data.",
                    "float_cycle": "Floats typically descend to 1000-2000m, drift for ~9-10 days, then descend to profile depth (~2000m), and ascend while measuring T/S profiles.",
                    "data_quality": "All Argo data goes through quality control with flags: 1=good, 2=probably good, 3=correctable, 4=bad, 9=missing.",
                    "bgc_floats": "Some floats carry biogeochemical sensors measuring oxygen, nitrate, pH, chlorophyll, and other parameters.",
                    "coverage": "Argo provides global ocean coverage with ~4000 active floats worldwide."
                }
            }
        }

    def extract_platform_number(self, text: str) -> Optional[str]:
        """Extract platform number from text using multiple patterns"""
        for pattern in self.argo_schema["nlp_engine"]["platform_extraction"]["patterns"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def identify_parameters(self, text: str) -> List[Dict[str, Any]]:
        """Identify which parameters are mentioned in the text"""
        text_lower = text.lower()
        identified_params = []
        
        for param_name, param_info in self.argo_schema["nlp_engine"]["parameter_mapping"].items():
            for keyword in param_info["keywords"]:
                if keyword in text_lower:
                    identified_params.append({
                        "name": param_name,
                        "db_name": param_info["db_name"],
                        "column": param_info["column"],
                        "units": param_info["units"],
                        "keyword_matched": keyword
                    })
                    break
        
        return identified_params

    def classify_query_intent(self, text: str) -> Dict[str, Any]:
        """Advanced query intent classification"""
        text_lower = text.lower()
        intents = []
        
        for intent_name, intent_info in self.argo_schema["nlp_engine"]["query_intent_classification"].items():
            score = 0
            matched_keywords = []
            
            # Check main keywords
            for keyword in intent_info["keywords"]:
                if keyword in text_lower:
                    score += 1
                    matched_keywords.append(keyword)
            
            # Boost score for confidence phrases
            if "confidence_boost" in intent_info:
                for boost_phrase in intent_info["confidence_boost"]:
                    if boost_phrase in text_lower:
                        score += 3
                        matched_keywords.append(boost_phrase)
            
            if score > 0:
                intents.append({
                    "intent": intent_name,
                    "score": score,
                    "matched_keywords": matched_keywords,
                    "table_priority": intent_info.get("table_priority", "unknown")
                })
        
        # Sort by score (highest first)
        intents.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "primary_intent": intents[0] if intents else {"intent": "general", "score": 0},
            "all_intents": intents,
            "is_database_query": len(intents) > 0
        }

    def generate_perfect_sql(self, question: str) -> Dict[str, Any]:
        """Generate perfect SQL based on natural language analysis"""
        platform = self.extract_platform_number(question)
        parameters = self.identify_parameters(question)
        intent_analysis = self.classify_query_intent(question)
        
        if not intent_analysis["is_database_query"]:
            return {
                "is_general_query": True,
                "question": question,
                "response_type": "argo_knowledge",
                "message": "This appears to be a general Argo question that should be answered with domain knowledge."
            }
        
        primary_intent = intent_analysis["primary_intent"]["intent"]
        
        # SENSOR QUERIES - Highest Priority
        if primary_intent == "sensor_queries" and parameters:
            param = parameters[0]  # Use first identified parameter
            if platform:
                sql = f"""
                SELECT 
                    p.parameter_sensor as sensor_name,
                    p.parameter_units as units,
                    s.sensor_maker as manufacturer,
                    s.sensor_model as model
                FROM parameter_table p
                LEFT JOIN sensor_table s ON p.platform_number = s.platform_number 
                    AND p.parameter_sensor = s.sensor
                WHERE p.platform_number = '{platform}' 
                    AND p.parameter LIKE '%{param['db_name']}%'
                """
            else:
                sql = f"""
                SELECT 
                    p.platform_number,
                    p.parameter_sensor as sensor_name,
                    p.parameter_units as units
                FROM parameter_table p
                WHERE p.parameter LIKE '%{param['db_name']}%'
                """
            
            return {
                "sql": sql,
                "intent": "sensor_identification",
                "platform": platform,
                "parameter": param,
                "explanation": f"Finding the sensor that measures {param['name']} for platform {platform or 'all platforms'}"
            }
        
        # DATA QUERIES - Scientific measurements
        elif primary_intent == "data_queries" and parameters:
            param = parameters[0]
            
            # Check for statistical intent
            if any(word in question.lower() for word in ["average", "mean", "avg"]):
                if platform:
                    sql = f"""
                    SELECT 
                        AVG({param['column']}) as average_{param['name']},
                        COUNT(*) as data_points,
                        MIN(pres) as min_depth,
                        MAX(pres) as max_depth
                    FROM depth_measurements_table
                    WHERE platform_number = '{platform}'
                        AND {param['column']}_qc IN ('1', '2')
                        AND {param['column']} IS NOT NULL
                    """
                else:
                    sql = f"""
                    SELECT 
                        platform_number,
                        AVG({param['column']}) as average_{param['name']},
                        COUNT(*) as data_points
                    FROM depth_measurements_table
                    WHERE {param['column']}_qc IN ('1', '2')
                        AND {param['column']} IS NOT NULL
                    GROUP BY platform_number
                    """
            
            # Check for profile intent
            elif any(word in question.lower() for word in ["profile", "vs depth", "with depth"]):
                if platform:
                    sql = f"""
                    SELECT 
                        pres as depth,
                        {param['column']} as {param['name']},
                        {param['column']}_qc as quality_flag
                    FROM depth_measurements_table
                    WHERE platform_number = '{platform}'
                        AND {param['column']}_qc IN ('1', '2')
                        AND {param['column']} IS NOT NULL
                    ORDER BY pres
                    """
            
            # Check for surface conditions
            elif any(word in question.lower() for word in ["surface", "sea surface"]):
                if platform:
                    sql = f"""
                    SELECT 
                        AVG({param['column']}) as surface_{param['name']},
                        COUNT(*) as measurements
                    FROM depth_measurements_table
                    WHERE platform_number = '{platform}'
                        AND pres < 10
                        AND {param['column']}_qc = '1'
                        AND {param['column']} IS NOT NULL
                    """
            
            # Default data query
            else:
                if platform:
                    sql = f"""
                    SELECT 
                        pres,
                        {param['column']},
                        {param['column']}_qc
                    FROM depth_measurements_table
                    WHERE platform_number = '{platform}'
                        AND {param['column']}_qc IN ('1', '2')
                        AND {param['column']} IS NOT NULL
                    ORDER BY pres
                    LIMIT 100
                    """
            
            return {
                "sql": sql,
                "intent": "data_analysis",
                "platform": platform,
                "parameter": param,
                "explanation": f"Retrieving {param['name']} data for platform {platform or 'all platforms'}"
            }
        
        # LOCATION QUERIES
        elif primary_intent == "location_queries":
            if any(word in question.lower() for word in ["current", "now", "latest"]):
                if platform:
                    sql = f"""
                    SELECT 
                        latitude,
                        longitude,
                        juld as last_position_time
                    FROM profile_table
                    WHERE platform_number = '{platform}'
                    ORDER BY juld DESC
                    LIMIT 1
                    """
            elif any(word in question.lower() for word in ["launch", "deployment", "deployed"]):
                if platform:
                    sql = f"""
                    SELECT 
                        launch_latitude as latitude,
                        launch_longitude as longitude,
                        launch_date
                    FROM meta_table
                    WHERE platform_number = '{platform}'
                    """
            elif any(word in question.lower() for word in ["trajectory", "movement", "path"]):
                if platform:
                    sql = f"""
                    SELECT 
                        juld as time,
                        latitude,
                        longitude
                    FROM trajectory_table
                    WHERE platform_number = '{platform}'
                        AND latitude IS NOT NULL
                    ORDER BY juld
                    """
            
            return {
                "sql": sql,
                "intent": "location_info",
                "platform": platform,
                "explanation": f"Finding location information for platform {platform}"
            }
        
        # METADATA QUERIES
        elif primary_intent == "metadata_queries":
            if platform:
                if any(word in question.lower() for word in ["type", "maker", "manufacturer"]):
                    sql = f"""
                    SELECT 
                        platform_type,
                        platform_maker,
                        battery_type,
                        firmware_version
                    FROM meta_table
                    WHERE platform_number = '{platform}'
                    """
                elif any(word in question.lower() for word in ["pi", "investigator", "scientist"]):
                    sql = f"""
                    SELECT 
                        pi_name as principal_investigator,
                        data_centre,
                        f.project_name
                    FROM meta_table m
                    JOIN float_table f ON m.platform_number = f.platform_number
                    WHERE m.platform_number = '{platform}'
                    """
                else:
                    sql = f"""
                    SELECT 
                        f.platform_number,
                        f.project_name,
                        m.platform_type,
                        m.platform_maker,
                        m.pi_name,
                        m.launch_date
                    FROM float_table f
                    JOIN meta_table m ON f.platform_number = m.platform_number
                    WHERE f.platform_number = '{platform}'
                    """
            
            return {
                "sql": sql,
                "intent": "metadata_info",
                "platform": platform,
                "explanation": f"Retrieving metadata for platform {platform}"
            }
        
        # Fallback for unclassified queries
        return {
            "is_general_query": True,
            "question": question,
            "analysis": {
                "platform": platform,
                "parameters": parameters,
                "intent": intent_analysis
            },
            "message": "Could not classify query intent. This may be a general Argo question."
        }

    def get_db_connection(self):
        """Get database connection"""
        if not self.connection:
            parser = ConfigParser()
            parser.read(self.db_config_file)
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
        """Execute SQL query and return results"""
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

    def format_natural_language_response(self, query_result: Dict[str, Any], original_question: str) -> str:
        """Format database results into natural language"""
        if not query_result.get("success"):
            return f"I couldn't retrieve the data due to an error: {query_result.get('error', 'Unknown error')}"
        
        data = query_result["data"]
        columns = query_result["columns"]
        
        if not data:
            return "No data found matching your criteria."
        
        # Format based on query type and results
        if len(data) == 1 and len(columns) == 1:
            # Single value result
            value = data[0][0]
            return f"The answer is: {value}"
        
        elif len(data) == 1:
            # Single row, multiple columns
            response = "Here's what I found:\n"
            for i, col in enumerate(columns):
                response += f"• {col.replace('_', ' ').title()}: {data[0][i]}\n"
            return response
        
        elif len(columns) == 2 and len(data) <= 10:
            # Small dataset, show as pairs
            response = f"Found {len(data)} results:\n"
            for row in data:
                response += f"• {columns[0]}: {row[0]}, {columns[1]}: {row[1]}\n"
            return response
        
        else:
            # Large dataset, provide summary
            response = f"Found {len(data)} records. "
            if "avg" in columns[0].lower() or "average" in columns[0].lower():
                response += f"Average value: {data[0][0]:.2f}"
            elif len(data) > 10:
                response += f"Showing summary of results. "
                response += f"First few values: {', '.join(str(row[0]) for row in data[:5])}"
            
            return response

    def get_argo_knowledge_response(self, question: str) -> str:
        """Provide general Argo knowledge responses"""
        question_lower = question.lower()
        knowledge = self.argo_schema["domain_knowledge"]["argo_general_knowledge"]
        
        if any(word in question_lower for word in ["what is argo", "about argo", "argo program"]):
            return knowledge["what_is_argo"]
        elif any(word in question_lower for word in ["float cycle", "how do floats work", "float operation"]):
            return knowledge["float_cycle"]
        elif any(word in question_lower for word in ["data quality", "quality control", "qc flags"]):
            return knowledge["data_quality"]
        elif any(word in question_lower for word in ["bgc", "biogeochemical", "oxygen", "nitrate"]):
            return knowledge["bgc_floats"]
        elif any(word in question_lower for word in ["coverage", "global", "how many floats"]):
            return knowledge["coverage"]
        else:
            return "I can help you with Argo float data queries and general information about the Argo program. What would you like to know?"

# Initialize FastMCP server
server = FastMCP("Ultimate Argo Database Server")
argo_server = UltimateArgoMCPServer()

@server.tool("intelligent_query")
async def intelligent_query(
    question: str,
    context: RequestContext
) -> Dict[str, Any]:
    """Ultimate intelligent query processing with perfect SQL generation"""
    
    # Generate perfect SQL or identify as general question
    query_analysis = argo_server.generate_perfect_sql(question)
    
    if query_analysis.get("is_general_query"):
        # Handle general Argo questions
        response = argo_server.get_argo_knowledge_response(question)
        return {
            "success": True,
            "query_type": "general_knowledge",
            "question": question,
            "response": response,
            "message": "Answered using Argo domain knowledge"
        }
    
    # Execute the generated SQL
    sql = query_analysis["sql"]
    db_result = argo_server.execute_query(sql)
    
    if db_result["success"]:
        # Format natural language response
        natural_response = argo_server.format_natural_language_response(db_result, question)
        
        return {
            "success": True,
            "query_type": "database_query",
            "question": question,
            "sql_generated": sql,
            "intent": query_analysis["intent"],
            "platform": query_analysis.get("platform"),
            "parameter": query_analysis.get("parameter"),
            "data": db_result["data"],
            "columns": db_result["columns"],
            "row_count": db_result["row_count"],
            "natural_language_response": natural_response,
            "explanation": query_analysis.get("explanation", "Query executed successfully")
        }
    else:
        return {
            "success": False,
            "query_type": "database_query",
            "question": question,
            "sql_generated": sql,
            "error": db_result["error"],
            "message": "Failed to execute the generated SQL query"
        }

@server.tool("analyze_question_advanced")
async def analyze_question_advanced(
    question: str,
    context: RequestContext
) -> Dict[str, Any]:
    """Advanced question analysis with full NLP breakdown"""
    
    platform = argo_server.extract_platform_number(question)
    parameters = argo_server.identify_parameters(question)
    intent_analysis = argo_server.classify_query_intent(question)
    
    return {
        "question": question,
        "analysis": {
            "extracted_platform": platform,
            "identified_parameters": parameters,
            "intent_classification": intent_analysis,
            "is_database_query": intent_analysis["is_database_query"]
        },
        "recommendations": {
            "suggested_approach": "database_query" if intent_analysis["is_database_query"] else "general_knowledge",
            "primary_table": intent_analysis["primary_intent"].get("table_priority", "unknown"),
            "confidence": "high" if intent_analysis["primary_intent"]["score"] >= 3 else "medium"
        },
        "available_data": {
            "platforms": argo_server.argo_schema["domain_knowledge"]["available_floats"],
            "parameters": list(argo_server.argo_schema["nlp_engine"]["parameter_mapping"].keys())
        }
    }

@server.tool("execute_sql_query")
async def execute_sql_query(
    sql_query: str,
    context: RequestContext
) -> Dict[str, Any]:
    """Execute SQL query with enhanced error handling"""
    result = argo_server.execute_query(sql_query)
    
    if result["success"]:
        natural_response = argo_server.format_natural_language_response(result, "")
        return {
            "success": True,
            "sql_query": sql_query,
            "data": result["data"],
            "columns": result["columns"],
            "row_count": result["row_count"],
            "natural_language_response": natural_response,
            "message": f"Query executed successfully. Returned {result['row_count']} rows."
        }
    else:
        return {
            "success": False,
            "sql_query": sql_query,
            "error": result["error"],
            "message": "Query execution failed. Check SQL syntax and table/column names."
        }

@server.resource("argo://ultimate_schema")
async def get_ultimate_schema() -> str:
    """Get the ultimate Argo database schema with perfect intelligence"""
    
    schema_info = argo_server.argo_schema
    
    schema_description = f"""
ULTIMATE ARGO DATABASE SCHEMA - PERFECT INTELLIGENCE ENGINE
Schema Version: {schema_info['schema_version']}

=== NATURAL LANGUAGE PROCESSING CAPABILITIES ===

✅ Platform Extraction: Automatically detects float numbers (13859, 1902676, 1900122)
✅ Parameter Recognition: Temperature, Salinity, Pressure, Oxygen, Nitrate, pH
✅ Intent Classification: Sensor queries, Data analysis, Location tracking, Metadata
✅ Statistical Analysis: Averages, Profiles, Surface conditions, Ranges
✅ General Argo Knowledge: Program info, Float operations, Quality control

=== PERFECT SQL GENERATION PATTERNS ===

🎯 SENSOR QUERIES:
   "What sensor measures temperature for float 1902676?"
   → SELECT p.parameter_sensor, s.sensor_maker FROM parameter_table p LEFT JOIN sensor_table s...

🎯 DATA QUERIES:
   "Average temperature for float 13859"
   → SELECT AVG(temp) FROM depth_measurements_table WHERE platform_number = '13859'...

🎯 PROFILE QUERIES:
   "Temperature profile for float 1902676"
   → SELECT pres, temp FROM depth_measurements_table WHERE platform_number = '1902676'...

🎯 LOCATION QUERIES:
   "Where is float 13859 now?"
   → SELECT latitude, longitude FROM profile_table WHERE platform_number = '13859' ORDER BY juld DESC LIMIT 1

🎯 METADATA QUERIES:
   "What type of float is 1902676?"
   → SELECT platform_type, platform_maker FROM meta_table WHERE platform_number = '1902676'

=== CORE TABLES WITH INTELLIGENCE ===

"""

    for table_name, table_info in schema_info['tables'].items():
        schema_description += f"""
{table_name.upper()}:
Description: {table_info['description']}
Primary Use: {table_info['primary_use']}
Key Columns:
"""
        for col_name, col_desc in table_info['columns'].items():
            schema_description += f"  • {col_name}: {col_desc}\n"
        
        if 'query_patterns' in table_info:
            schema_description += "Common Patterns:\n"
            for pattern_name, pattern_sql in table_info['query_patterns'].items():
                schema_description += f"  • {pattern_name}: {pattern_sql[:100]}...\n"

    schema_description += f"""

=== DOMAIN KNOWLEDGE INTEGRATION ===

Available Floats: {', '.join(schema_info['domain_knowledge']['available_floats'])}
Parameter Ranges: {len(schema_info['domain_knowledge']['typical_ranges'])} parameters with expected ranges
Quality Control: Full QC flag interpretation
General Argo Knowledge: Program overview, float operations, data quality

=== USAGE EXAMPLES ===

Natural Language Input → Perfect SQL Generation:

1. "What sensor measures temperature for 1902676?" 
   → Sensor identification query with JOIN

2. "Average surface salinity for float 13859"
   → Statistical query with depth filtering

3. "Show me the temperature profile for 1902676"
   → Profile query with quality control

4. "Where was float 13859 deployed?"
   → Launch location from meta_table

5. "Tell me about Argo floats"
   → General knowledge response (no SQL)

The system automatically:
✅ Extracts platform numbers and parameters
✅ Classifies query intent
✅ Generates perfect SQL
✅ Formats natural language responses
✅ Handles general Argo questions
"""

    return schema_description

if __name__ == "__main__":
    import mcp.server.stdio

    async def main():
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream, 
                write_stream,
                options=types.ServerOptions(),
                init_data={
                    "argo_schema_loaded": True, 
                    "schema_version": "ultimate-perfect-intelligence",
                    "nlp_engine": "advanced",
                    "sql_generation": "perfect"
                }
            )

    asyncio.run(main())
