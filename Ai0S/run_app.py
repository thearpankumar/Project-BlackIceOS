#!/usr/bin/env python3
"""
Agentic AI OS Control System - Application Runner
Simple runner script to start the complete desktop application.
"""

import sys
import os
from pathlib import Path

# Add the source directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.launcher import main
    
    if __name__ == "__main__":
        print("🚀 Starting Agentic AI OS Control System...")
        print("   - Backend Service: FastAPI + LangGraph + MCP")
        print("   - Desktop App: CustomTkinter Professional UI")
        print("   - AI Models: Gemini 2.0 Flash + Groq")
        print("   - Voice Input: Real-time transcription")
        print("   - MCP Integration: Cross-platform automation")
        print()
        
        sys.exit(main())
        
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print()
    print("Please ensure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Startup Error: {e}")
    sys.exit(1)