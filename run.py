#!/usr/bin/env python
"""
TourAI Guide - Weather & Travel Assistant
Run this script to start the Flask server
"""
import os
import sys

print("=" * 60)
print("🌍 TourAI Guide - Weather & Travel Assistant")
print("=" * 60)

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

try:
    # Try to load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env")
except Exception as e:
    print(f"⚠️  Warning: Could not load .env file: {e}")

try:
    # Import required modules
    print("✅ Checking imports...")
    import flask
    print(f"   - Flask version: {flask.__version__}")
    
    import google.generativeai
    print(f"   - Google Generative AI imported")
    
    import requests
    print(f"   - Requests imported")
    
    # Check Gemini API key
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key and gemini_key != "your-gemini-api-key-here":
        print(f"✅ Gemini API key is configured")
    else:
        print(f"⚠️  WARNING: Gemini API key not configured!")
        print(f"   Please update the GEMINI_API_KEY in .env file")
    
    print("\n✅ All imports successful!")
    print("=" * 60)
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("   Please run: pip install -r requirements.txt")
    sys.exit(1)

try:
    # Import and run the Flask app
    print("\n🚀 Starting Flask server...")
    from app import app
    
    print("\n" + "=" * 60)
    print("✅ Server is running!")
    print("=" * 60)
    print("\n🌐 Open your browser and go to:")
    print("   👉 http://localhost:5000")
    print("\n⏹️  Press CTRL+C to stop the server")
    print("=" * 60 + "\n")
    
    #app.run(debug=True, port=5000, use_reloader=False)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

    
except Exception as e:
    print(f"\n❌ Error starting app: {e}")
    import traceback
    print("\nFull error details:")
    traceback.print_exc()
    sys.exit(1)

