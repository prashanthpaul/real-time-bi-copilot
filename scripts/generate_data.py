"""
Convenience wrapper to run sample data generation from the scripts/ directory.

Usage:
    python scripts/generate_data.py
    python scripts/generate_data.py --rows 50000
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.sample_data_generator import main

if __name__ == "__main__":
    main()
