#!/usr/bin/env python3
"""Simple test runner to handle Python path issues."""

import sys
import os
import pytest

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Run pytest with verbose output
    sys.exit(pytest.main(["-v", "tests/"]))