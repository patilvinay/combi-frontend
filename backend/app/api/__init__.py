"""
API package initialization.

This package contains all API-related code including endpoints, dependencies, and versioning.
"""

# Import and expose the main components
from .api_v1.api import api_router as api_v1_router
from .deps import get_api_key, api_key_header

__all__ = [
    'api_v1_router',
    'get_api_key',
    'api_key_header',
]
