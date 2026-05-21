"""
ChE Design Agent - Entry point
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.main_window import run_app

if __name__ == "__main__":
    run_app()
