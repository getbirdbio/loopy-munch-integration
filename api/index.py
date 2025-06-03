#!/usr/bin/env python3
"""
Vercel Entry Point for Loopy-Munch Integration
==============================================

This file adapts our Flask app for Vercel's serverless environment.
"""

import sys
import os

# Add the parent directory to the path so we can import our modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import our Flask app
from loopy_make_integration import app

# Export the Flask app for Vercel
# Vercel expects the app to be available directly
app = app

if __name__ == "__main__":
    # For local testing
    app.run(host='0.0.0.0', port=5008, debug=False) 