"""
Wiki API Routes

Note: Wiki service implementation is in src/services/wiki/
This is just a re-export for the modular structure.
"""
# Import from existing wiki implementation
import sys

sys.path.insert(0, "C:/1cAI/src")

from src.api.wiki import router

__all__ = ["router"]
