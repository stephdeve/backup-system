"""
Fonctions utilitaires pour MyBackup
"""

import hashlib
from pathlib import Path
from typing import Union, Optional
from datetime import datetime
import os


def calculate_file_hash(filepath: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Calcule le hash d'un fichier.
    
    Args:
        filepath: Chemin du fichier
        algorithm: Algorithme de hash (sha256, blake2b, etc.)
    
    Returns:
        Hash hexadécimal du fichier
    
    Example:
        >>> hash_value = calculate_file_hash("document.txt")
        >>> print(hash_value)
        'a3f5c892b1e4...'
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"Fichier introuvable : {filepath}")
    
    # Choisir l'algorithme
    hash_obj = hashlib.new(algorithm)
    
    # Lire par chunks pour économiser la mémoire (important pour gros fichiers)
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):  # 8 KB chunks
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


def format_size(size_bytes: int) -> str:
    """
    Convertit une taille en bytes vers un format lisible.
    
    Args:
        size_bytes: Taille en bytes
    
    Returns:
        Taille formatée (ex: "1.5 GB")
    
    Example:
        >>> format_size(1536000000)
        '1.43 GB'
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def format_timestamp(dt: datetime) -> str:
    """
    Formate un timestamp de manière lisible.
    
    Args:
        dt: Objet datetime
    
    Returns:
        String formaté
    
    Example:
        >>> format_timestamp(datetime.now())
        '2026-01-20 14:30:00'
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    S'assure qu'un dossier existe, le crée si nécessaire.
    
    Args:
        path: Chemin du dossier
    
    Returns:
        Path object du dossier
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_excluded(filepath: Union[str, Path], exclude_patterns: list) -> bool:
    """
    Vérifie si un fichier doit être exclu selon les patterns.
    
    Args:
        filepath: Chemin du fichier
        exclude_patterns: Liste de patterns à exclure
    
    Returns:
        True si le fichier doit être exclu
    
    Example:
        >>> is_excluded("projet/node_modules/lib.js", ["node_modules", "*.tmp"])
        True
    """
    filepath = Path(filepath)
    filepath_str = str(filepath)
    
    for pattern in exclude_patterns:
        # Pattern simple : nom de dossier
        if pattern in filepath.parts:
            return True
        
        # Pattern wildcard : *.ext
        if pattern.startswith("*") and filepath_str.endswith(pattern[1:]):
            return True
        
        # Pattern exact
        if pattern in filepath_str:
            return True
    
    return False


def get_relative_path(filepath: Union[str, Path], base_path: Union[str, Path]) -> Path:
    """
    Obtient le chemin relatif d'un fichier par rapport à un dossier de base.
    
    Args:
        filepath: Chemin complet du fichier
        base_path: Dossier de base
    
    Returns:
        Chemin relatif
    
    Example:
        >>> get_relative_path("C:/Users/Dev/projet/app.py", "C:/Users/Dev")
        Path('projet/app.py')
    """
    return Path(filepath).relative_to(base_path)


def calculate_compression_ratio(original_size: int, compressed_size: int) -> float:
    """
    Calcule le ratio de compression.
    
    Args:
        original_size: Taille originale en bytes
        compressed_size: Taille compressée en bytes
    
    Returns:
        Ratio de compression en pourcentage
    
    Example:
        >>> calculate_compression_ratio(1000, 400)
        60.0  # 60% de compression
    """
    if original_size == 0:
        return 0.0
    return ((original_size - compressed_size) / original_size) * 100


def sanitize_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier pour éviter les caractères problématiques.
    
    Args:
        filename: Nom de fichier original
    
    Returns:
        Nom de fichier nettoyé
    
    Example:
        >>> sanitize_filename("mon fichier*.txt")
        'mon_fichier.txt'
    """
    # Remplace les caractères interdits sur Windows
    forbidden_chars = '<>:"/\\|?*'
    for char in forbidden_chars:
        filename = filename.replace(char, '_')
    return filename


def get_file_info(filepath: Union[str, Path]) -> dict:
    """
    Récupère les informations détaillées d'un fichier.
    
    Args:
        filepath: Chemin du fichier
    
    Returns:
        Dictionnaire avec les infos du fichier
    
    Example:
        >>> info = get_file_info("document.txt")
        >>> print(info['size'], info['modified'])
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"Fichier introuvable : {filepath}")
    
    stat = filepath.stat()
    
    return {
        'path': str(filepath.absolute()),
        'name': filepath.name,
        'size': stat.st_size,
        'size_formatted': format_size(stat.st_size),
        'modified': datetime.fromtimestamp(stat.st_mtime),
        'created': datetime.fromtimestamp(stat.st_ctime),
        'is_file': filepath.is_file(),
        'is_dir': filepath.is_dir(),
        'extension': filepath.suffix,
    }


class ProgressTracker:
    """Classe simple pour suivre la progression."""
    
    def __init__(self, total: int):
        self.total = total
        self.current = 0
        self.start_time = datetime.now()
    
    def update(self, increment: int = 1):
        """Incrémente la progression."""
        self.current += increment
    
    def get_percentage(self) -> float:
        """Retourne le pourcentage de progression."""
        if self.total == 0:
            return 100.0
        return (self.current / self.total) * 100
    
    def get_elapsed_time(self) -> float:
        """Retourne le temps écoulé en secondes."""
        return (datetime.now() - self.start_time).total_seconds()
    
    def get_eta(self) -> Optional[float]:
        """Estime le temps restant en secondes."""
        if self.current == 0:
            return None
        elapsed = self.get_elapsed_time()
        rate = self.current / elapsed
        remaining = self.total - self.current
        return remaining / rate if rate > 0 else None