"""
Utilities for pushing BA artefacts to external integrations.
"""

from .sync_artifact import sync_artifact_from_path, parse_args, main

__all__ = ["sync_artifact_from_path", "parse_args", "main"]


