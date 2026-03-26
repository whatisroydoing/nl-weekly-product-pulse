"""
Root conftest.py — adds the project root to sys.path so that
'models', 'module_a', 'module_b', etc. are importable from all test files,
regardless of the directory pytest is run from.
"""
import sys
import os

# Ensure the project root is always on sys.path
sys.path.insert(0, os.path.dirname(__file__))
