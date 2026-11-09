"""Utility functions for filesystem path handling."""

from __future__ import annotations

import os


def normalize_path(path_str: str) -> str:
    """Return a normalized version of *path_str* using forward slashes.

    This function collapses redundant separators and up-level references and
    converts any Windows style backslashes to forward slashes so that paths are
    handled consistently across platforms.
    """
    if path_str is None:
        return ""
    normalized = os.path.normpath(path_str)
    return normalized.replace("\\", "/")
