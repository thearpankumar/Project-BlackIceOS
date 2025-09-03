#!/usr/bin/env python3
"""
AI0S - Agentic AI OS Control System
Main entry point for the application.
"""

import sys
from pathlib import Path

# Add src to path so imports work
sys.path.insert(0, str(Path(__file__).parent / "src"))

from launcher import main

if __name__ == "__main__":
    sys.exit(main())