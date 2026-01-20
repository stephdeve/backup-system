"""
MyBackup - Système de Backup Incrémental Intelligent
Version: 1.0.0
Compatible: Python 3.10+, Windows/Linux/macOS
"""

__version__ = "1.0.0"
__author__ = "StephDev"

from pathlib import Path

# Dossier de configuration par défaut
CONFIG_DIR = Path.home() / ".mybackup"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
DB_FILE = CONFIG_DIR / "backups.db"

# Constantes
DEFAULT_COMPRESSION_LEVEL = 3
DEFAULT_WATCH_INTERVAL = 300  # 5 minutes en secondes
HASH_ALGORITHM = "sha256"
ENCRYPTION_ALGORITHM = "AES-256-GCM"

__all__ = [
    "__version__",
    "__author__",
    "CONFIG_DIR",
    "CONFIG_FILE",
    "DB_FILE",
]