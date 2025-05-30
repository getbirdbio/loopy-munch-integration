#!/usr/bin/env python3
"""
Start the Loopy-Munch Production Service
========================================

This script loads environment variables and starts the production integration service.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from production.env
load_dotenv('production.env')

# Verify required environment variables
required_vars = [
    'LOOPY_API_KEY',
    'LOOPY_API_SECRET', 
    'LOOPY_USERNAME',
    'MUNCH_API_KEY',
    'MUNCH_ORGANIZATION_ID'
]

missing_vars = []
for var in required_vars:
    if not os.getenv(var):
        missing_vars.append(var)

if missing_vars:
    print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
    print("Please check production.env file")
    sys.exit(1)

# Display configuration
print("🚀 Starting Loopy-Munch Production Service")
print("=" * 50)
print(f"Loopy API User: {os.getenv('LOOPY_USERNAME')}")
print(f"Munch Organization: {os.getenv('MUNCH_ORGANIZATION_ID')}")
print(f"Service Port: {os.getenv('SERVICE_PORT', '5008')}")
print(f"Environment: {os.getenv('ENVIRONMENT', 'production')}")
print("=" * 50)

# Start the production service
os.system("python loopy_munch_production_service.py") 