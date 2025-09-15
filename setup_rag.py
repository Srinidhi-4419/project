#!/usr/bin/env python3
"""
RAG System Setup - Build Vector Database for Argo Data
Run this FIRST to create the embeddings and vector database
"""

import os
import pickle
import json
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import psycopg2
from configparser import ConfigParser
from typing import List, Dict, Any
from datetime import datetime

class ArgoRAGSetup:
    """Setup and build RAG vector database for Argo system"""
    
    def __init__(self, db_config_file="database.ini"):
        self.db_config = db_config_file
        
        # Initialize embedding model
        print("🔄 Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Embedding model loaded")
        
        # Storage paths
        self.vector_db_path = "argo_vector_db.index"
        self.documents_path = "argo_documents.pkl"
        self.metadata_path = "argo_metadata.json"
        
        # Data containers
        self.documents = []
        self.document_metadata = []
        self.vector_db = None
    
    def get_db_connection(self):
        """Get database connection"""
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
    
    def step1_extract_table_metadata(self):
        """STEP 1: Extract rich metadata from SQL tables"""
        print("\n🔄 STEP 1: Extracting table metadata...")
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Define table information
        tables_info = {
            'float_table': {
                'description': 'Basic float identification and project information',
                'primary_use': 'Platform registration, project classification, WMO instrument codes',
                'query_types': ['project queries', 'basic float info', 'WMO lookups'],
                'keywords': ['project', 'wmo', 'float info', 'basic']
            },
            'meta_table': {
                'description': 'Comprehensive float specifications and deployment information',
                'primary_use': 'Platform specifications, manufacturer details, PI information, launch coordinates',
                'query_types': ['platform type', 'manufacturer', 'PI queries', 'deployment info'],
                'keywords': ['platform type', 'PI', 'manufacturer', 'launch', 'deployment', 'specifications']
            },
            'profile_table': {
                'description': 'Current float positions and cycle tracking information',
                'primary_use': 'Current locations, regional analysis, cycle monitoring',
                'query_types': ['location queries', 'regional analysis', 'where is float'],
                'keywords': ['location', 'position', 'where', 'region', 'current', 'coordinates']
            },
            'depth_measurements_table': {
                'description': 'Scientific oceanographic measurements at various depths',
                'primary_use': 'Temperature, salinity, pressure, BGC parameters (oxygen, nitrate, pH)',
                'query_types': ['scientific data', 'profiles', 'measurements', 'averages'],
                'keywords': ['temperature', 'salinity', 'pressure', 'oxygen', 'nitrate', 'pH', 'measurements', 'profile']
            },
            'trajectory_table': {
                'description': 'Float surface positions and movement tracking over time',
                'primary_use': 'Trajectory analysis, float movement, surface measurements',
                'query_types': ['trajectory', 'movement', 'surface data'],
                'keywords': ['trajectory', 'movement', 'surface', 'drift', 'path']
            },
            'sensor_table': {
                'description': 'Instrumentation specifications and sensor details',
                'primary_use': 'Sensor identification, manufacturer details, model information',
                'query_types': ['sensor queries', 'instrumentation', 'what sensors'],
                'keywords': ['sensor', 'instrument', 'CTD', 'optode', 'equipment']
            }
        }
        
        table_documents = []
        
        for table_name, info in tables_info.items():
            try:
                # Get column information
                cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position
                """)
                columns = cursor.fetchall()
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                
                # Get sample data for context
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                sample_data = cursor.fetchall()
                
                # Create rich document
                doc_text = f"""
Table: {table_name}
Description: {info['description']}
Primary Use Cases: {info['primary_use']}
Query Types: {', '.join(info['query_types'])}
Keywords: {', '.join(info['keywords'])}

Database Details:
- Total Records: {row_count:,}
- Column Count: {len(columns)}
- Columns: {', '.join([f"{col[0]} ({col[1]})" for col in columns])}

Use this table when user asks about:
{chr(10).join([f"• {keyword}" for keyword in info['keywords']])}

Common query patterns:
{chr(10).join([f"• {qt}" for qt in info['query_types']])}
""".strip()
                
                table_documents.append({
                    'document': doc_text,
                    'metadata': {
                        'type': 'table_schema',
                        'table_name': table_name,
                        'row_count': row_count,
                        'columns': [col[0] for col in columns],
                        'keywords': info['keywords'],
                        'query_types': info['query_types']
                    }
                })
                
                print(f"  ✅ Processed {table_name}: {row_count:,} records, {len(columns)} columns")
                
            except Exception as e:
                print(f"  ❌ Error processing {table_name}: {e}")
        
        # Add data pattern documents
        pattern_docs = self.extract_data_patterns(cursor)
        table_documents.extend(pattern_docs)
        
        # Add query pattern documents
        query_docs = self.create_query_patterns()
        table_documents.extend(query_docs)
        
        cursor.close()
        conn.close()
        
        print(f"✅ STEP 1 Complete: {len(table_documents)} documents created")
        return table_documents
    
    def extract_data_patterns(self, cursor) -> List[Dict]:
        """Extract data distribution and patterns"""
        pattern_docs = []
        
        try:
            # Platform statistics
            cursor.execute("""
                SELECT platform_number, COUNT(*) as profile_count 
                FROM profile_table 
                GROUP BY platform_number 
                ORDER BY profile_count DESC
            """)
            platform_stats = cursor.fetchall()
            
            platform_doc = f"""
Platform Data Distribution:
Available Floats: {', '.join([str(p[0]) for p in platform_stats])}
Profile Statistics:
{chr(10).join([f"• Float {p[0]}: {p[1]} profiles" for p in platform_stats])}

Total Floats: {len(platform_stats)}
Most Active Float: {platform_stats[0][0]} ({platform_stats[0][1]} profiles)

Use when user asks about:
• Available floats
• Float activity levels
• Platform-specific queries
• Data coverage per float
"""
            
            pattern_docs.append({
                'document': platform_doc.strip(),
                'metadata': {
                    'type': 'data_pattern',
                    'pattern_name': 'platform_distribution',
                    'floats': [str(p[0]) for p in platform_stats]
                }
            })
            
            # Geographic coverage
            cursor.execute("""
                SELECT 
                    MIN(latitude) as min_lat, MAX(latitude) as max_lat,
                    MIN(longitude) as min_lon, MAX(longitude) as max_lon,
                    COUNT(*) as total_positions,
                    COUNT(DISTINCT platform_number) as unique_floats
                FROM profile_table 
                WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            """)
            geo_stats = cursor.fetchone()
            
            if geo_stats and geo_stats[0] is not None:
                geo_doc = f"""
Geographic Coverage Analysis:
Latitude Range: {geo_stats[0]:.2f}°N to {geo_stats[1]:.2f}°N
Longitude Range: {geo_stats[2]:.2f}°E to {geo_stats[3]:.2f}°E
Total Positions: {geo_stats[4]:,}
Active Floats: {geo_stats[5]} floats with position data

Ocean Basin Coverage:
• Global ocean monitoring
• Suitable for regional analysis
• Supports basin-scale studies

Common Regional Queries:
• Indian Ocean: latitude -40 to 30, longitude 40 to 120
• North Atlantic: latitude 30 to 70, longitude -70 to 0

Use when user asks about:
• Regional analysis
• Geographic distribution
• Ocean basin queries
• Spatial coverage
"""
                
                pattern_docs.append({
                    'document': geo_doc.strip(),
                    'metadata': {
                        'type': 'data_pattern',
                        'pattern_name': 'geographic_coverage',
                        'lat_range': [float(geo_stats[0]), float(geo_stats[1])],
                        'lon_range': [float(geo_stats[2]), float(geo_stats[3])]
                    }
                })
            
            # Parameter availability
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN temp IS NOT NULL THEN 1 END) as temp_count,
                    COUNT(CASE WHEN psal IS NOT NULL THEN 1 END) as psal_count,
                    COUNT(CASE WHEN doxy IS NOT NULL THEN 1 END) as doxy_count,
                    COUNT(CASE WHEN nitrate IS NOT NULL THEN 1 END) as nitrate_count,
                    COUNT(CASE WHEN ph_in_situ_total IS NOT NULL THEN 1 END) as ph_count,
                    COUNT(*) as total_measurements
                FROM depth_measurements_table
            """)
            param_stats = cursor.fetchone()
            
            if param_stats:
                param_doc = f"""
Scientific Parameter Availability:
Total Measurements: {param_stats[5]:,}

Core Parameters:
• Temperature: {param_stats[0]:,} measurements ({param_stats[0]/param_stats[5]*100:.1f}% coverage)
• Salinity: {param_stats[1]:,} measurements ({param_stats[1]/param_stats[5]*100:.1f}% coverage)

BGC Parameters:
• Dissolved Oxygen: {param_stats[2]:,} measurements ({param_stats[2]/param_stats[5]*100:.1f}% coverage)
• Nitrate: {param_stats[3]:,} measurements ({param_stats[3]/param_stats[5]*100:.1f}% coverage)
• pH: {param_stats[4]:,} measurements ({param_stats[4]/param_stats[5]*100:.1f}% coverage)

Data Quality Notes:
• Core parameters (temp, salinity) have highest coverage
• BGC parameters available for specialized analysis
• Quality flags available for all parameters

Use when user asks about:
• Parameter availability
• Data quality
• BGC analysis
• Measurement statistics
"""
                
                pattern_docs.append({
                    'document': param_doc.strip(),
                    'metadata': {
                        'type': 'data_pattern',
                        'pattern_name': 'parameter_availability',
                        'parameters': ['temp', 'psal', 'doxy', 'nitrate', 'ph_in_situ_total']
                    }
                })
            
            print(f"  ✅ Data patterns extracted: {len(pattern_docs)} documents")
            
        except Exception as e:
            print(f"  ⚠️ Warning: Could not extract some data patterns: {e}")
        
        return pattern_docs
    
    def create_query_patterns(self) -> List[Dict]:
        """Create query pattern documents with examples"""
        
        query_patterns = [
            {
                'pattern_name': 'Platform Specification Queries',
                'description': 'Questions about float hardware, manufacturer, and specifications',
                'examples': [
                    'What is the platform type of float 13859?',
                    'Who is the PI of float 1900122?',
                    'What manufacturer made float 13859?',
                    'When was float 1900122 deployed?',
                    'Where was float 13859 launched?'
                ],
                'sql_templates': [
                    "SELECT platform_type FROM meta_table WHERE platform_number = '{float_id}'",
                    "SELECT pi_name FROM meta_table WHERE platform_number = '{float_id}'",
                    "SELECT platform_maker FROM meta_table WHERE platform_number = '{float_id}'"
                ],
                'primary_table': 'meta_table',
                'keywords': ['platform type', 'PI', 'manufacturer', 'deployed', 'launched', 'specifications']
            },
            {
                'pattern_name': 'Current Location Queries',
                'description': 'Questions about current float positions and recent locations',
                'examples': [
                    'Where is float 13859 now?',
                    'Current position of float 1900122',
                    'Latest location of all floats',
                    'Show me float positions'
                ],
                'sql_templates': [
                    "SELECT latitude, longitude FROM profile_table WHERE platform_number = '{float_id}' ORDER BY juld DESC LIMIT 1",
                    "SELECT platform_number, latitude, longitude FROM profile_table WHERE juld = (SELECT MAX(juld) FROM profile_table)"
                ],
                'primary_table': 'profile_table',
                'keywords': ['where', 'location', 'position', 'current', 'now', 'latest']
            },
            {
                'pattern_name': 'Scientific Measurement Queries',
                'description': 'Questions about temperature, salinity, and other oceanographic measurements',
                'examples': [
                    'Average temperature for float 13859',
                    'Salinity profile for float 1900122',
                    'Temperature vs pressure for all floats',
                    'Show oxygen levels for float 13859',
                    'Maximum depth reached by float 1900122'
                ],
                'sql_templates': [
                    "SELECT AVG(temp) FROM depth_measurements_table WHERE platform_number = '{float_id}' AND temp IS NOT NULL",
                    "SELECT pres, temp FROM depth_measurements_table WHERE platform_number = '{float_id}' ORDER BY pres",
                    "SELECT MAX(pres) FROM depth_measurements_table WHERE platform_number = '{float_id}'"
                ],
                'primary_table': 'depth_measurements_table',
                'keywords': ['temperature', 'salinity', 'pressure', 'oxygen', 'measurements', 'profile', 'average', 'depth']
            },
            {
                'pattern_name': 'Regional Analysis Queries',
                'description': 'Questions about floats in specific geographic regions',
                'examples': [
                    'Floats in the Indian Ocean',
                    'How many floats are in the North Atlantic?',
                    'Show floats near the equator',
                    'Temperature data from tropical regions'
                ],
                'sql_templates': [
                    "SELECT DISTINCT platform_number FROM profile_table WHERE latitude BETWEEN {lat1} AND {lat2} AND longitude BETWEEN {lon1} AND {lon2}",
                    "SELECT COUNT(DISTINCT platform_number) FROM profile_table WHERE latitude BETWEEN {lat1} AND {lat2}"
                ],
                'primary_table': 'profile_table',
                'keywords': ['region', 'ocean', 'Atlantic', 'Pacific', 'Indian', 'equator', 'tropical', 'basin']
            },
            {
                'pattern_name': 'Sensor and Instrumentation Queries',
                'description': 'Questions about sensors, instruments, and hardware on floats',
                'examples': [
                    'What sensors are on float 13859?',
                    'CTD manufacturer for float 1900122',
                    'List all sensor types',
                    'Show instrumentation for all floats'
                ],
                'sql_templates': [
                    "SELECT sensor, sensor_maker FROM sensor_table WHERE platform_number = '{float_id}'",
                    "SELECT DISTINCT sensor FROM sensor_table",
                    "SELECT platform_number, sensor, sensor_maker FROM sensor_table"
                ],
                'primary_table': 'sensor_table',
                'keywords': ['sensor', 'instrument', 'CTD', 'optode', 'hardware', 'equipment']
            }
        ]
        
        pattern_docs = []
        
        for pattern in query_patterns:
            doc_text = f"""
Query Pattern: {pattern['pattern_name']}
Description: {pattern['description']}
Primary Table: {pattern['primary_table']}

Example Questions:
{chr(10).join([f"• {ex}" for ex in pattern['examples']])}

SQL Templates:
{chr(10).join([f"• {template}" for template in pattern['sql_templates']])}

Keywords that trigger this pattern:
{', '.join(pattern['keywords'])}

Use this pattern when user asks about:
{chr(10).join([f"• {keyword}" for keyword in pattern['keywords']])}
"""
            
            pattern_docs.append({
                'document': doc_text.strip(),
                'metadata': {
                    'type': 'query_pattern',
                    'pattern_name': pattern['pattern_name'],
                    'primary_table': pattern['primary_table'],
                    'keywords': pattern['keywords'],
                    'examples': pattern['examples']
                }
            })
        
        print(f"  ✅ Query patterns created: {len(pattern_docs)} documents")
        return pattern_docs
    
    def step2_generate_embeddings(self, documents):
        """STEP 2: Generate embeddings for all documents"""
        print(f"\n🔄 STEP 2: Generating embeddings for {len(documents)} documents...")
        
        # Extract text documents
        doc_texts = [doc['document'] for doc in documents]
        self.documents = doc_texts
        self.document_metadata = [doc['metadata'] for doc in documents]
        
        # Generate embeddings
        print("  🔄 Computing embeddings (this may take a moment)...")
        embeddings = self.embedding_model.encode(
            doc_texts, 
            show_progress_bar=True,
            batch_size=32
        )
        
        print(f"  ✅ Embeddings generated: {embeddings.shape}")
        return embeddings
    
    def step3_build_vector_database(self, embeddings):
        """STEP 3: Build FAISS vector database"""
        print(f"\n🔄 STEP 3: Building FAISS vector database...")
        
        # Initialize FAISS index
        dimension = embeddings.shape[1]
        self.vector_db = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Add embeddings to index
        self.vector_db.add(embeddings.astype('float32'))
        
        print(f"  ✅ Vector database built: {self.vector_db.ntotal} vectors indexed")
        print(f"  📊 Dimension: {dimension}")
        
        # Test the database
        self.test_vector_database()
    
    def step4_save_system(self):
        """STEP 4: Save vector database and metadata to disk"""
        print(f"\n🔄 STEP 4: Saving RAG system to disk...")
        
        try:
            # Save FAISS index
            faiss.write_index(self.vector_db, self.vector_db_path)
            print(f"  ✅ Vector database saved: {self.vector_db_path}")
            
            # Save documents
            with open(self.documents_path, 'wb') as f:
                pickle.dump(self.documents, f)
            print(f"  ✅ Documents saved: {self.documents_path}")
            
            # Save metadata
            metadata_info = {
                'document_metadata': self.document_metadata,
                'embedding_model': 'all-MiniLM-L6-v2',
                'dimension': self.vector_db.d,
                'total_documents': len(self.documents),
                'created_at': datetime.now().isoformat(),
                'database_tables': ['float_table', 'meta_table', 'profile_table', 
                                  'depth_measurements_table', 'trajectory_table', 'sensor_table']
            }
            
            with open(self.metadata_path, 'w') as f:
                json.dump(metadata_info, f, indent=2)
            print(f"  ✅ Metadata saved: {self.metadata_path}")
            
            print(f"\n🎉 RAG system setup complete!")
            print(f"📁 Files created:")
            print(f"   • {self.vector_db_path} - Vector database")
            print(f"   • {self.documents_path} - Documents")  
            print(f"   • {self.metadata_path} - Metadata")
            
        except Exception as e:
            print(f"  ❌ Error saving system: {e}")
    
    def test_vector_database(self):
        """Test the vector database with sample queries"""
        print(f"  🧪 Testing vector database...")
        
        test_queries = [
            "platform type of float",
            "temperature measurements",
            "sensor information",
            "float location"
        ]
        
        for query in test_queries:
            # Encode query
            query_embedding = self.embedding_model.encode([query])
            faiss.normalize_L2(query_embedding)
            
            # Search
            scores, indices = self.vector_db.search(query_embedding.astype('float32'), k=2)
            
            print(f"    Query: '{query}' -> Found {len(indices[0])} matches")
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < len(self.document_metadata):
                    doc_type = self.document_metadata[idx].get('type', 'unknown')
                    print(f"      {i+1}. {doc_type} (score: {score:.3f})")
        
        print(f"  ✅ Vector database test complete")
    
    def run_complete_setup(self):
        """Run the complete RAG setup process"""
        print("🚀 STARTING ARGO RAG SYSTEM SETUP")
        print("=" * 50)
        
        start_time = datetime.now()
        
        try:
            # Step 1: Extract metadata
            documents = self.step1_extract_table_metadata()
            
            # Step 2: Generate embeddings  
            embeddings = self.step2_generate_embeddings(documents)
            
            # Step 3: Build vector database
            self.step3_build_vector_database(embeddings)
            
            # Step 4: Save system
            self.step4_save_system()
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            print(f"\n🎉 SETUP COMPLETE!")
            print(f"⏱️  Duration: {duration.total_seconds():.1f} seconds")
            print(f"📊 Total documents: {len(self.documents)}")
            print(f"🎯 Ready for RAG queries!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ SETUP FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main setup function"""
    print("🌊 Argo RAG System Setup")
    print("This will create the vector database for your RAG system")
    print()
    
    # Create setup instance
    setup = ArgoRAGSetup()
    
    # Run complete setup
    success = setup.run_complete_setup()
    
    if success:
        print("\n✅ Your RAG system is ready!")
        print("You can now use the ArgoRAGSystem class for intelligent queries.")
    else:
        print("\n❌ Setup failed. Please check the errors above.")

if __name__ == "__main__":
    main()
