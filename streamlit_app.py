"""
FleetGuardAI - Streamlit Cloud Entry Point

This file serves as the entry point for Streamlit Cloud deployment.
It imports and runs the main application from the FleetGuard package.
"""

import sys
from pathlib import Path

# Add FleetGuard directory to path
fleet_guard_dir = Path(__file__).parent / "FleetGuard"
sys.path.insert(0, str(fleet_guard_dir))

# Import and run the main app
from main import main

if __name__ == "__main__":
    main()
