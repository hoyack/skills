#!/usr/bin/env python3
"""
SharePoint Access Control - Hermes FT Bot Integration

This module provides a drop-in replacement for direct SharePoint API calls
that enforces drive-level access restrictions.
"""

import os
import sys

# Add the skill scripts directory to path
_scripts_dir = os.path.join(os.path.dirname(__file__), 'scripts')
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

# Re-export the main client and functions
from sharepoint_access import (
    SharePointClient,
    SharePointAccessError,
    get_client,
    sharepoint_request
)

__all__ = [
    'SharePointClient',
    'SharePointAccessError', 
    'get_client',
    'sharepoint_request'
]
