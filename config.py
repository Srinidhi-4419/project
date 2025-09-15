
# Configuration helper for Perplexity API
# Add this to your argo_nl_query_system.py

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment variable
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')

if not PERPLEXITY_API_KEY:
    print("Please set PERPLEXITY_API_KEY environment variable")
    print("Or create a .env file with: PERPLEXITY_API_KEY=your-key-here")
