#!/usr/bin/env python3
"""
Enhanced RAG-Powered Argo Query System - Comprehensive Version
Handles technical queries, general Argo knowledge, and detailed responses
"""

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import json
import pickle
import psycopg2
import os
from typing import List, Dict, Any
import requests
import re

class EnhancedArgoRAGSystem:
    """Enhanced RAG system with general knowledge and detailed responses"""
    
    def __init__(self, db_config_file="database.ini", perplexity_api_key=None):
        self.db_config = db_config_file
        self.perplexity_key = perplexity_api_key
        
        # Initialize embedding model
        print("🔄 Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # File paths for saved vector database
        self.vector_db_path = "argo_vector_db.index"
        self.documents_path = "argo_documents.pkl"
        self.metadata_path = "argo_metadata.json"
        
        # Vector database containers
        self.vector_db = None
        self.documents = []
        self.document_metadata = []
        
        # Argo general knowledge base
        self.argo_knowledge = self.build_argo_knowledge_base()
        
        # Load existing vector database OR build new one
        if self.load_vector_database():
            print("✅ Loaded existing RAG vector database")
        else:
            print("🔄 Vector database not found, building new one...")
            self.build_vector_database()
    
    def build_argo_knowledge_base(self) -> str:
        """Build comprehensive Argo program knowledge base"""
        return """
ARGO PROGRAM COMPREHENSIVE KNOWLEDGE BASE

=== WHAT IS ARGO? ===
The Argo Program is a global ocean observing system that uses autonomous profiling floats to monitor ocean temperature, salinity, and other properties. It's the largest component of the global ocean observing system.

=== PROGRAM HISTORY ===
• Started: 1999
• Global coverage achieved: 2007
• Current status: Over 4,000 active floats worldwide
• Mission duration: Ongoing, permanent observing system
• International collaboration: 30+ countries participate

=== HOW ARGO FLOATS WORK ===
Float Cycle:
1. Float descends to "parking depth" (~1000m for 9-10 days)
2. Descends further to profile depth (~2000m)
3. Rises to surface while measuring temperature/salinity
4. Transmits data via satellite at surface
5. Repeats cycle every 10 days

Technical Specifications:
• Typical lifespan: 4-6 years
• Profile frequency: Every 10 days
• Parking depth: 1000m
• Profile depth: Usually 2000m (some go deeper)
• Surface time: 6-12 hours for data transmission

=== FLOAT TYPES ===
Core Argo Floats:
• Measure: Temperature, Salinity, Pressure
• Primary manufacturers: Sea-Bird Scientific (SBE), NKE Instrumentation
• Platform types: APEX, ARVOR, NOVA, SOLO

BGC-Argo Floats (Biogeochemical):
• Additional sensors: Oxygen, Nitrate, pH, Chlorophyll, Backscatter
• Enable study of ocean biogeochemistry and carbon cycle
• More complex and expensive than core floats

Deep Argo:
• Profile to 4000-6000m depth
• Study deep ocean warming and circulation
• Smaller network due to technical challenges

=== SCIENTIFIC IMPORTANCE ===
Climate Research:
• Monitor ocean heat content changes
• Track global warming in oceans (>90% of excess heat)
• Study ocean-atmosphere interactions
• Detect climate variability (El Niño, PDO, AMO)

Ocean Science:
• Map ocean circulation patterns
• Study water mass properties and mixing
• Monitor seasonal and interannual variability
• Validate satellite measurements

Weather & Climate Models:
• Provide real-time data for weather forecasting
• Essential for climate model initialization
• Improve seasonal climate predictions

=== DATA QUALITY & PROCESSING ===
Quality Control Levels:
• Real-time QC: Automatic checks, data available within 24 hours
• Delayed-mode QC: Scientific review, correction of sensor drift
• Quality flags: 1=good, 2=probably good, 3=probably bad, 4=bad

Data Products:
• Individual profiles
• Gridded products (temperature/salinity fields)
• Time series at fixed locations
• Regional summaries

Data Centers:
• Coriolis (France) - European data center
• AOML (USA) - Atlantic data center
• JMA (Japan) - Pacific data center
• Global Data Assembly Centers coordinate worldwide

=== MEASUREMENT ACCURACY ===
Core Parameters:
• Temperature: ±0.002°C accuracy
• Salinity: ±0.01 PSU accuracy
• Pressure: ±2.4 dbar accuracy

BGC Parameters:
• Oxygen: ±8 micromol/kg or 5%
• Nitrate: ±2 micromol/kg
• pH: ±0.02 units

=== GLOBAL COVERAGE ===
Geographic Distribution:
• All ocean basins covered
• Density: ~3° × 3° grid globally
• Higher density in some regions (North Atlantic, Southern Ocean)
• Coverage gaps in marginal seas, near coasts

Temporal Coverage:
• Continuous since 2000
• Over 2 million temperature/salinity profiles collected
• BGC data available since ~2012
• Deep Argo data since ~2015

=== TECHNOLOGICAL INNOVATIONS ===
Recent Advances:
• Two-way satellite communication
• Ice detection algorithms for polar regions
• Extended battery life (7+ years)
• Improved sensor accuracy and stability
• Real-time quality control algorithms

Future Developments:
• New BGC sensors (nitrite, alkalinity)
• Improved deep profiling capabilities
• Integration with other observing systems
• Enhanced polar operations

=== OPERATIONAL CHALLENGES ===
Technical Issues:
• Sensor drift over time (especially salinity)
• Battery degradation in cold water
• Ice damage in polar regions
• Fishing activity interactions
• Biofouling of sensors

Solutions:
• Regular calibration against ship data
• Delayed-mode quality control
• Ice-avoidance algorithms
• International cooperation protocols
• Anti-fouling treatments

=== ECONOMIC & SOCIAL IMPACT ===
Cost-Effectiveness:
• ~$20,000 per float
• Provides 150-200 profiles over lifetime
• Cost per profile: ~$100-150
• Much cheaper than ship-based observations

Societal Benefits:
• Improved weather forecasts
• Better climate projections
• Support for fisheries management
• Maritime safety applications
• Educational and research opportunities

=== INTERNATIONAL COOPERATION ===
Governance:
• Argo Steering Team provides international coordination
• Data sharing agreements ensure open access
• Standardized procedures for deployment and data processing
• Regular international meetings and workshops

Contributing Countries:
Major contributors: USA, France, Japan, Germany, Australia, UK, Canada
Emerging contributors: China, India, South Korea, Norway

=== FUTURE OF ARGO ===
Expansion Plans:
• OneArgo: Integration of Core, BGC, and Deep Argo
• Enhanced polar coverage
• Marginal seas deployment
• Increased BGC float percentage
• Technology improvements

Sustainability:
• Long-term funding commitments
• Technology transfer to developing countries
• Integration with satellite and other observing systems
• Contribution to UN Sustainable Development Goals
"""
    
    def load_vector_database(self) -> bool:
        """Load saved vector database from disk"""
        try:
            required_files = [self.vector_db_path, self.documents_path, self.metadata_path]
            missing_files = [f for f in required_files if not os.path.exists(f)]
            
            if missing_files:
                print(f"⚠️ Missing files: {missing_files}")
                return False
            
            # Load FAISS index
            self.vector_db = faiss.read_index(self.vector_db_path)
            print(f"  📁 Loaded FAISS index: {self.vector_db.ntotal} vectors")
            
            # Load documents
            with open(self.documents_path, 'rb') as f:
                self.documents = pickle.load(f)
            print(f"  📄 Loaded documents: {len(self.documents)} documents")
            
            # Load metadata
            with open(self.metadata_path, 'r') as f:
                metadata_info = json.load(f)
                self.document_metadata = metadata_info['document_metadata']
            print(f"  📊 Loaded metadata: {len(self.document_metadata)} entries")
            
            print(f"  ✅ Vector database loaded successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load vector database: {e}")
            return False
    
    def get_db_connection(self):
        """Database connection"""
        from configparser import ConfigParser
        parser = ConfigParser()
        parser.read(self.db_config)
        config = {param[0]: param[1] for param in parser.items('database')}
        
        return psycopg2.connect(
            host=config['host'],
            port=int(config['port']),
            user=config['user'],
            password=config['password'],
            database=config['database']
        )
    
    def classify_query_type(self, query: str) -> str:
        """Classify if query is technical (needs database) or general (needs knowledge)"""
        
        query_lower = query.lower()
        technical_indicators = [
            # Existing indicators...
            'float 13859', 'float 1900122', 'platform_number',
            'temperature', 'salinity', 'pressure', 'oxygen', 'nitrate', 'ph',
            'average', 'maximum', 'minimum', 'show me', 'what is the',
            'sensor', 'pi of', 'platform type', 'where is', 'how many',
            'cycle', 'profile', 'depth', 'measurement', 'inversion',
            
            # ✅ ADD THESE:
            'density inversion', 'density inversions', 'sigma-0', 'sigma0',
            'potential density', 'find density', 'detect density',
            'from the database', 'from database', 'using database',
            'calculate from', 'compute from', 'analyze from'
        ]
        
        # ✅ ENHANCED: Force technical if contains "find" + "from database"
        if 'find' in query_lower and ('from the database' in query_lower or 'from database' in query_lower):
            return 'technical'
        
        # ✅ ENHANCED: Force technical for specific oceanographic analyses  
        analysis_patterns = [
            r'find.*inversion.*database',
            r'detect.*inversion.*database',
            r'calculate.*sigma.*database',
            r'find.*where.*deeper.*water',
            r'identify.*profiles.*where'
        ]
        
        for pattern in analysis_patterns:
            if re.search(pattern, query_lower):
                return 'technical'
        # Technical query indicators (specific data requests)
        technical_indicators = [
            # Specific float references
            'float 13859', 'float 1900122', 'platform_number',
            # Specific measurements
            'temperature', 'salinity', 'pressure', 'oxygen', 'nitrate', 'ph',
            # Specific queries
            'average', 'maximum', 'minimum', 'show me', 'what is the',
            # Database-specific terms
            'sensor', 'pi of', 'platform type', 'where is', 'how many',
            'cycle', 'profile', 'depth', 'measurement'
        ]
        
        # General knowledge indicators
        general_indicators = [
            'what is argo', 'how does argo work', 'argo program', 'argo floats',
            'how do floats', 'what are floats', 'argo history', 'why argo',
            'argo mission', 'float technology', 'oceanography', 'climate',
            'international', 'cooperation', 'data quality', 'accuracy',
            'manufacturers', 'deployment', 'coverage', 'future'
        ]
        
        # Count indicators
        technical_score = sum(1 for indicator in technical_indicators if indicator in query_lower)
        general_score = sum(1 for indicator in general_indicators if indicator in query_lower)
        
        # Specific patterns for general questions
        general_patterns = [
            r'what is argo',
            r'how do.*argo.*work',
            r'how do.*float.*work',
            r'tell me about argo',
            r'explain argo',
            r'argo program',
            r'history of argo',
            r'why.*argo.*important'
        ]
        
        for pattern in general_patterns:
            if re.search(pattern, query_lower):
                return 'general'
        
        # Decision logic
        if general_score > technical_score and general_score > 0:
            return 'general'
        elif technical_score > 0:
            return 'technical'
        else:
            # Default to general for ambiguous questions
            return 'general'
    
    def answer_general_question(self, query: str) -> str:
        """Answer general questions about Argo using knowledge base"""
        
        system_prompt = f"""You are an expert oceanographer and Argo program specialist. Answer the user's question about the Argo program using the comprehensive knowledge base below. 

Provide detailed, accurate, and educational responses. Include specific facts, numbers, and technical details where relevant. Structure your response clearly with paragraphs and bullet points when appropriate.

ARGO PROGRAM KNOWLEDGE BASE:
{self.argo_knowledge}

User Question: {query}

Provide a comprehensive, detailed answer based on the knowledge base above."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]

        payload = {
            "model": "sonar",
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 600
        }

        headers = {
            "Authorization": f"Bearer {self.perplexity_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers, 
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            return f"I apologize, but I encountered an error while processing your question about the Argo program: {str(e)}"
    
    def retrieve_relevant_context(self, query: str, k: int = 5, show_details: bool = False) -> List[Dict]:
        """Retrieve relevant documents for query"""
        
        try:
            if show_details:
                print(f"🔍 Retrieving context for: '{query}'")
            
            query_embedding = self.embedding_model.encode([query])
            query_embedding = query_embedding.astype(np.float32)
            faiss.normalize_L2(query_embedding)
            
            k = min(k, len(self.documents))
            scores, indices = self.vector_db.search(query_embedding, k)
            
            relevant_docs = []
            
            for i in range(k):
                if i < len(indices[0]) and i < len(scores[0]):
                    idx = int(indices[0][i])
                    score = float(scores[0][i])
                    
                    if 0 <= idx < len(self.documents):
                        relevant_docs.append({
                            'document': self.documents[idx],
                            'metadata': self.document_metadata[idx],
                            'similarity_score': score,
                            'rank': i + 1
                        })
                        
                        if show_details:
                            doc_type = self.document_metadata[idx].get('type', 'unknown')
                            table_name = self.document_metadata[idx].get('table_name', 'N/A')
                            print(f"    {i+1}. {doc_type} - {table_name} (score: {score:.3f})")
            
            if show_details:
                print(f"  ✅ Retrieved {len(relevant_docs)} relevant documents")
            return relevant_docs
            
        except Exception as e:
            print(f"❌ Error in context retrieval: {e}")
            return []
    
    def generate_enhanced_sql(self, user_query: str, show_details: bool = False) -> Dict[str, Any]:
        """✅ ENHANCED: Generate SQL with better context and minimal verbose comments"""
        
        if show_details:
            print(f"\n🤖 Generating enhanced SQL for: '{user_query}'")
        
        relevant_docs = self.retrieve_relevant_context(user_query, k=5, show_details=show_details)
        
        if not relevant_docs:
            return {
                'success': False,
                'error': 'No relevant context found',
                'retrieved_context': []
            }
        
        # Build comprehensive context
        context_text = "RELEVANT DATABASE CONTEXT:\n\n"
        
        for doc in relevant_docs:
            context_text += f"--- Document (Relevance Score: {doc['similarity_score']:.3f}) ---\n"
            context_text += doc['document'] + "\n\n"
        
        if show_details:
            print(f"📝 Context length: {len(context_text)} characters")
        
        # ✅ ENHANCED: System prompt with specific guidance for complex calculations
        system_prompt = f"""You are an expert PostgreSQL query generator and oceanographic data analyst for Argo float databases.

    {context_text}

    ENHANCED QUERY GENERATION RULES:
    1. platform_number is VARCHAR → ALWAYS use quotes: '13859' NOT 13859
    2. Use ONLY tables and columns from the retrieved context above
    3. For statistical queries (avg, max, min), include appropriate WHERE clauses for data quality
    4. For depth/pressure queries, remember that pressure ~= depth in dbar (1 dbar ≈ 1 meter)
    5. Include quality control filters: temp_qc IN ('1', '2') for good data, psal_qc IN ('1', '2') for salinity
    6. For cycle-specific queries, use cycle_number column
    7. For regional queries, use latitude/longitude bounds from profile_table
    8. Join tables when necessary using platform_number as foreign key
    9. Use appropriate aggregation functions (AVG, MAX, MIN, COUNT, SUM)
    10. Include ORDER BY for meaningful result ordering
    11. DEPTH CONSTRAINTS: "upper 100 meters" → pres <= 100, "below 500m" → pres >= 500

    ✅ SPECIAL GUIDANCE FOR COMPLEX CALCULATIONS:
    - For sigma-0 (density): Use simple formula: (psal - 35) * 0.8 + (15 - temp) * 0.2
    - For inversions: Compare shallow (pres <= 50) vs deep (pres >= 100) water using self-joins
    - For gradients: Calculate differences between consecutive depth measurements
    - Keep SQL comments MINIMAL: -- Simple calculation only
    - NO detailed oceanographic theory in SQL - focus on working code
    - Use CTEs (WITH clauses) for complex multi-step calculations

    EXAMPLES OF ENHANCED QUERIES:
    - Temperature inversions: Self-join to compare temps at different depths, filter where deep > shallow
    - Density inversions: Calculate sigma-0, then compare shallow vs deep using similar logic
    - Gradient detection: Use LEAD/LAG window functions or self-joins for consecutive measurements
    - Regional analysis: Use geographic bounds in WHERE clauses

    CRITICAL SQL OUTPUT REQUIREMENTS:
    - Generate ONLY executable PostgreSQL SQL
    - Start response with SELECT or WITH keyword
    - Keep comments to 1 line per calculation maximum
    - Use proper SQL syntax (semicolons, parentheses, quotes)
    - Complete the entire query - do not cut off mid-calculation

    Generate a comprehensive, accurate PostgreSQL query that answers the user's question completely with minimal comments."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]

        payload = {
            "model": "sonar",
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 1500  # ✅ INCREASED from 1200 to handle complex queries
        }

        headers = {
            "Authorization": f"Bearer {self.perplexity_key}",
            "Content-Type": "application/json"
        }

        try:
            if show_details:
                print("🌐 Calling Perplexity API for SQL generation...")
            
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers, 
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            # ✅ ENHANCED: Better response handling
            full_response = result["choices"][0]["message"]["content"]
            sql_query = self._extract_sql(full_response)
            
            if show_details:
                print(f"🔍 Full LLM Response Length: {len(full_response)} chars")
                print(f"✅ Extracted SQL: {sql_query}")
            
            return {
                'success': True,
                'sql_query': sql_query,
                'full_response': full_response,  # ✅ ADDED: Keep full response for debugging
                'retrieved_context': relevant_docs,
                'context_used': len(relevant_docs)
            }
            
        except Exception as e:
            if show_details:
                print(f"❌ API Error: {e}")
            return {
                'success': False,
                'error': str(e),
                'retrieved_context': relevant_docs
            }

    
    def _extract_sql(self, response: str) -> str:
        """✅ FIXED: Extract clean SQL from LLM response"""
        
        # Method 1: Look for SQL code blocks first
        sql_patterns = [
            r"``````",
            r"``````",
            r"``````"
        ]
        
        for pattern in sql_patterns:
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                sql = match.group(1).strip()
                if sql.upper().startswith(('SELECT', 'WITH')):
                    return sql
        
        # Method 2: Look for SELECT or WITH statements
        sql_statement_patterns = [
            r"(WITH\s+\w+\s+AS\s*\(.*?SELECT.*?)(?:;|$|\n\n|$)",
            r"(SELECT.*?)(?:;|$|\n\n)",
        ]
        
        for pattern in sql_statement_patterns:
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                sql = match.group(1).strip()
                # Validate it looks like SQL
                if any(keyword in sql.upper() for keyword in ['FROM', 'WHERE', 'JOIN']):
                    return sql
        
        # Method 3: If response is very short and looks like SQL
        if len(response.split('\n')) <= 20 and 'SELECT' in response.upper():
            return response.strip()
        
        # Method 4: Last resort - look for any SQL-like content
        lines = response.split('\n')
        sql_lines = []
        in_sql_block = False
        
        for line in lines:
            line_upper = line.strip().upper()
            
            # Start collecting SQL
            if line_upper.startswith(('SELECT', 'WITH')):
                in_sql_block = True
                sql_lines = [line]
            elif in_sql_block:
                # Continue collecting until we hit explanatory text
                if any(word in line.lower() for word in ['explanation:', 'this query', 'note:', '**', 'context:']):
                    break
                sql_lines.append(line)
                
                # Stop at semicolon
                if ';' in line:
                    break
        
        if sql_lines:
            potential_sql = '\n'.join(sql_lines).strip()
            if any(keyword in potential_sql.upper() for keyword in ['FROM', 'WHERE', 'JOIN']):
                return potential_sql
        
        # If all else fails, return the first 500 chars as SQL attempt
        return response[:500].strip()
    
    def execute_sql(self, sql_query: str, show_details: bool = False) -> Dict[str, Any]:
        """Execute SQL query with enhanced error handling"""
        try:
            if show_details:
                print(f"🗄️ Executing SQL: {sql_query}")
            
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(sql_query)
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            cursor.close()
            conn.close()
            
            if show_details:
                print(f"✅ Query executed successfully: {len(results)} rows returned")
                if results and len(results) <= 5:
                    print(f"📋 Sample results: {results[:3]}")
            
            return {
                'success': True,
                'data': results,
                'columns': columns,
                'row_count': len(results)
            }
            
        except Exception as e:
            if show_details:
                print(f"❌ SQL Execution Error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def format_detailed_response(self, result: Dict[str, Any], query_type: str) -> str:
        """✅ LLM-POWERED: Let the LLM format responses intelligently"""
        
        if not result['success']:
            return f"❌ Error: {result.get('error', 'Unknown error')}"
        
        if query_type == 'general':
            return result.get('response', 'No response available')
        
        # For technical queries, let LLM format the response
        return self.format_response_with_llm(result)

    def format_response_with_llm(self, result: Dict[str, Any]) -> str:
        """Use LLM to intelligently format database results"""
        
        if not result['data']:
            return "No data found for your query."
        
        # Prepare the data context for LLM
        data_context = self.prepare_data_context(result)
        
        system_prompt = """You are an expert oceanographer and data analyst. Format the database query results into a clear, professional, and informative response for the user.

FORMATTING GUIDELINES:
1. Start with a clear summary of what was found
2. Present data in a readable format with appropriate scientific units
3. Include relevant oceanographic context and interpretation
4. Use proper formatting with headers, bullet points, and emphasis
5. Explain the scientific significance when relevant
6. For numerical data, use appropriate precision (temperature: 2-3 decimals, salinity: 2-3 decimals, pressure: 1 decimal)
7. Add emojis for visual appeal: 🌡️ for temperature, 🧂 for salinity, 📊 for data, 🗺️ for location, etc.

RESPONSE STRUCTURE:
- Use **bold** for key values and important information
- Use bullet points for lists
- Include scientific context in a separate "Context" section
- Keep responses informative but concise

Remember: You're communicating complex oceanographic data to users who may not be experts."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""
User Query: {result['user_query']}
Database Results: {data_context}

Please format this data into a clear, informative response for the user."""}
        ]

        payload = {
            "model": "sonar",
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 500
        }

        headers = {
            "Authorization": f"Bearer {self.perplexity_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers, 
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            llm_result = response.json()
            formatted_response = llm_result["choices"][0]["message"]["content"]
            
            return formatted_response.strip()
            
        except Exception as e:
            # Fallback to simple formatting if LLM fails
            return self.simple_fallback_format(result)

    def prepare_data_context(self, result: Dict[str, Any]) -> str:
        """Prepare data context for LLM formatting"""
        
        data_context = f"Query: {result['user_query']}\n"
        data_context += f"Number of results: {result['row_count']}\n"
        
        if result.get('columns'):
            data_context += f"Columns: {', '.join(result['columns'])}\n"
        
        data_context += "Data:\n"
        
        # Limit data size for LLM processing
        if result['row_count'] <= 10:
            # Show all data for small results
            for i, row in enumerate(result['data'], 1):
                data_context += f"Row {i}: {row}\n"
        elif result['row_count'] <= 50:
            # Show first 5 and last 2 for medium results
            for i, row in enumerate(result['data'][:5], 1):
                data_context += f"Row {i}: {row}\n"
            data_context += f"... ({result['row_count'] - 7} more rows)\n"
            for i, row in enumerate(result['data'][-2:], result['row_count'] - 1):
                data_context += f"Row {i}: {row}\n"
        else:
            # Show first 3 for large results
            for i, row in enumerate(result['data'][:3], 1):
                data_context += f"Row {i}: {row}\n"
            data_context += f"... ({result['row_count'] - 3} more rows - large dataset)\n"
            
            # Add summary statistics if numeric data
            if result['data'] and len(result['data'][0]) == 1:
                try:
                    values = [float(row[0]) for row in result['data'] if row[0] is not None]
                    if values:
                        data_context += f"Summary: Min={min(values):.3f}, Max={max(values):.3f}, Avg={sum(values)/len(values):.3f}\n"
                except:
                    pass
        
        return data_context

    def simple_fallback_format(self, result: Dict[str, Any]) -> str:
        """Simple fallback formatting if LLM fails"""
        
        if result['row_count'] == 1 and len(result['data'][0]) == 1:
            value = result['data'][0][0]
            return f"Result: {value}"
        
        elif result['row_count'] <= 5:
            response = f"Found {result['row_count']} results:\n"
            for i, row in enumerate(result['data'], 1):
                response += f"{i}. {row}\n"
            return response
        
        else:
            return f"Found {result['row_count']} results. Sample: {result['data'][:3]}"

    def process_enhanced_query(self, user_query: str, show_details: bool = False) -> Dict[str, Any]:
        """Enhanced query processing with classification and detailed responses"""
        
        if show_details:
            print(f"\n🚀 Processing enhanced query: '{user_query}'")
            print("=" * 70)
        
        # Classify query type
        query_type = self.classify_query_type(user_query)
        
        if show_details:
            print(f"🔍 Query classification: {query_type.upper()}")
        
        if query_type == 'general':
            # Handle general Argo knowledge questions
            if show_details:
                print("📚 Processing as general knowledge question...")
            
            try:
                response = self.answer_general_question(user_query)
                return {
                    'success': True,
                    'query_type': 'general',
                    'user_query': user_query,
                    'response': response,
                    'method': 'Knowledge Base + LLM'
                }
            except Exception as e:
                return {
                    'success': False,
                    'query_type': 'general',
                    'error': str(e),
                    'user_query': user_query
                }
        
        else:
            # Handle technical database queries
            if show_details:
                print("🗄️ Processing as technical database query...")
            
            # Generate enhanced SQL
            sql_result = self.generate_enhanced_sql(user_query, show_details)
            
            if not sql_result['success']:
                return {
                    'success': False,
                    'query_type': 'technical',
                    'error': sql_result['error'],
                    'user_query': user_query
                }
            
            # Execute SQL
            db_result = self.execute_sql(sql_result['sql_query'], show_details)
            
            # Combine results
            if db_result['success']:
                return {
                    'success': True,
                    'query_type': 'technical',
                    'user_query': user_query,
                    'sql_query': sql_result['sql_query'],
                    'data': db_result['data'],
                    'columns': db_result['columns'],
                    'row_count': db_result['row_count'],
                    'retrieved_context': sql_result['retrieved_context'],
                    'method': 'RAG + Database',
                    'context_documents': len(sql_result['retrieved_context'])
                }
            else:
                return {
                    'success': False,
                    'query_type': 'technical',
                    'error': db_result['error'],
                    'sql_query': sql_result['sql_query'],
                    'user_query': user_query
                }
    
    def build_vector_database(self):
        """Fallback message"""
        print("⚠️ Vector database files not found.")
        print("Please run: python setup_rag.py")
        raise Exception("Run setup_rag.py first to create the vector database.")

def interactive_enhanced_chat():
        """🎯 ENHANCED INTERACTIVE CHAT INTERFACE"""
        
        PERPLEXITY_API_KEY = "UR KEY"
        
        print("\n🌊 ENHANCED ARGO RAG SYSTEM - COMPREHENSIVE MODE")
        print("=" * 70)
        
        try:
            # Initialize enhanced RAG system
            rag_system = EnhancedArgoRAGSystem(perplexity_api_key=PERPLEXITY_API_KEY)
            
            print("\n🎯 Enhanced RAG System Ready!")
            print("\n📝 You can now ask:")
            print("\n🔬 **Technical Queries (Database)**:")
            print("   • What is the platform type of float 13859?")
            print("   • Maximum temperature for float 13859 in cycle 1")
            print("   • What sensors are on float 1900122?")
            print("   • Average salinity in the upper 100 meters")
            
            print("\n📚 **General Knowledge (Argo Program)**:")
            print("   • What is the Argo program?")
            print("   • How do Argo floats work?")
            print("   • Tell me about Argo data quality")
            print("   • What are the different types of Argo floats?")
            
            print("\n💡 **Commands**:")
            print("   • 'detailed' - Toggle detailed processing output")
            print("   • 'examples' - Show more example queries")
            print("   • 'quit' or 'exit' - Exit the program")
            
            detailed_mode = False
            
            while True:
                print("\n" + "-" * 70)
                user_input = input("🌊 Your question: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Thanks for using the Enhanced Argo RAG System!")
                    break
                
                if user_input.lower() == 'detailed':
                    detailed_mode = not detailed_mode
                    print(f"🔧 Detailed mode: {'ON' if detailed_mode else 'OFF'}")
                    continue
                
                if user_input.lower() == 'examples':
                    print("\n📖 **More Example Queries**:")
                    print("\n🔬 **Technical Queries**:")
                    print("   • Compare oxygen levels between float 13859 and 1900122")
                    print("   • Show temperature profile for float 13859 below 500m")
                    print("   • Which float has the most BGC measurements?")
                    print("   • Average temperature gradient in the thermocline")
                    
                    print("\n📚 **General Knowledge**:")
                    print("   • Why is the Argo program important for climate research?")
                    print("   • How accurate are Argo float measurements?")
                    print("   • What is the international cooperation in Argo?")
                    print("   • How long do Argo floats operate?")
                    continue
                
                if not user_input:
                    print("❓ Please enter a question")
                    continue
                
                try:
                    # Process enhanced query
                    result = rag_system.process_enhanced_query(user_input, show_details=detailed_mode)
                    
                    if result['success']:
                        # Format detailed response
                        formatted_response = rag_system.format_detailed_response(result, result['query_type'])
                        print(f"\n🤖 **Response**:")
                        print(formatted_response)
                        
                        # Show thinking process in detailed mode
                        if detailed_mode and result['query_type'] == 'technical' and 'thinking_process' in result:
                            print(f"\n🧠 **LLM Thinking Process**:")
                            print(result['thinking_process'])
                        
                        # Show SQL query for technical queries
                        if result['query_type'] == 'technical' and 'sql_query' in result and result['sql_query']:
                            print(f"\n💻 **Generated SQL Query**:")
                            print("```")
                            print(result['sql_query'])
                            print("```")
                        elif result['query_type'] == 'technical':
                            print(f"\n💻 **Generated SQL Query**: [Not available or extraction failed]")
                        
                        # Show processing method
                        if not detailed_mode:
                            method = result.get('method', 'Unknown')
                            if result['query_type'] == 'technical':
                                context_docs = result.get('context_documents', 0)
                                row_count = result.get('row_count', 0)
                                print(f"\n📊 **Processing Info**: {method} | {row_count} results | {context_docs} context docs")
                            else:
                                print(f"\n📊 **Processing Info**: {method}")
                        
                    else:
                        print(f"\n❌ **Query Failed**: {result['error']}")
                        if 'sql_query' in result and result['sql_query']:
                            print(f"\n💻 **Attempted SQL**:")
                            print("```")
                            print(result['sql_query'])
                            print("```")
                        elif 'sql_query' in result:
                            print(f"\n💻 **Attempted SQL**: [SQL extraction failed]")
                        
                        # Show thinking process for failed queries in detailed mode
                        if detailed_mode and 'thinking_process' in result:
                            print(f"\n🧠 **Thinking Process**: {result['thinking_process']}")
                            
                except KeyboardInterrupt:
                    print("\n👋 Interrupted by user")
                    break
                except Exception as e:
                    print(f"\n❌ **System Error**: {e}")
            
        except Exception as e:
            print(f"❌ System initialization failed: {e}")
            print("Make sure you've run 'python setup_rag.py' first!")



if __name__ == "__main__":
    interactive_enhanced_chat()
