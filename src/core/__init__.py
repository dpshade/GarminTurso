"""
Core functionality for GarminTurso.

This module contains the essential components:
- Authentication (auth.py)
- Database operations (database.py)
- Sync services (sync_service.py)
"""

from .auth import GarminAuthenticator
from .database import TursoDatabase
from .sync_service import GarminSyncService

__all__ = [
    'GarminAuthenticator',
    'TursoDatabase',
    'GarminSyncService'
]