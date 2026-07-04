"""Config behave : rendre le package `src` importable depuis les steps."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
