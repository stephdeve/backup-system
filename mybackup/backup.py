"""
Logique de backup pour MyBackup
Gère la sauvegarde incrémentale avec chiffrement et compression
"""

import zstandard as zstd
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime
import shutil

from .config import Config
from .crypto import CryptoManager
from .database import BackupDatabase
from .utils import (
    calculate_file_hash,
    get_file_info,
    is_excluded,
    ensure_directory,
    format_size,
    calculate_compression_ratio
)


class BackupEngine:
    """
    Moteur principal de backup.
    Gère le processus complet de sauvegarde incrémentale.
    """
    
    def __init__(self, config: Optional[Config] = None, db: Optional[BackupDatabase] = None):
        """
        Initialise le moteur de backup.
        
        Args:
            config: Configuration (charge depuis fichier si None)
            db: Base de données (crée une nouvelle si None)
        """
        self.config = config or Config()
        self.db = db or BackupDatabase()
        
        # Initialiser le gestionnaire de crypto
        encryption_key = self.config.get_encryption_key()
        if not encryption_key:
            raise ValueError("Clé de chiffrement manquante dans la configuration")
        
        self.crypto = CryptoManager.from_key_string(encryption_key)
        
        # Initialiser le compresseur zstandard
        compression_level = self.config.get_compression_level()
        self.compressor = zstd.ZstdCompressor(level=compression_level)
        self.decompressor = zstd.ZstdDecompressor()
    
    def backup_all_sources(self) -> Dict[str, any]:
        """
        Lance un backup de toutes les sources configurées.
        
        Returns:
            Statistiques du backup
        
        Example:
            >>> engine = BackupEngine()
            >>> stats = engine.backup_all_sources()
            >>> print(stats['files_backed_up'])
        """
        sources = self.config.get_sources()
        
        if not sources:
            raise ValueError("Aucune source configurée")
        
        destination = self.config.get_destination('primary')
        if not destination:
            raise ValueError("Aucune destination configurée")
        
        # Stats globales
        total_stats = {
            'files_backed_up': 0,
            'files_skipped': 0,
            'files_errors': 0,
            'total_size_original': 0,
            'total_size_encrypted': 0,
            'start_time': datetime.now(),
            'end_time': None,
            'duration': 0,
            'errors': []
        }
        
        # Backup chaque source
        for source in sources:
            try:
                stats = self.backup_source(
                    source_path=source['path'],
                    destination_path=destination,
                    exclude_patterns=source.get('exclude', [])
                )
                
                total_stats['files_backed_up'] += stats['files_backed_up']
                total_stats['files_skipped'] += stats['files_skipped']
                total_stats['files_errors'] += stats['files_errors']
                total_stats['total_size_original'] += stats['total_size_original']
                total_stats['total_size_encrypted'] += stats['total_size_encrypted']
                total_stats['errors'].extend(stats['errors'])
                
            except Exception as e:
                error_msg = f"Erreur lors du backup de {source['path']}: {e}"
                total_stats['errors'].append(error_msg)
                total_stats['files_errors'] += 1
                self.db.log_error('backup_source_failed', error_msg, source['path'])
        
        total_stats['end_time'] = datetime.now()
        total_stats['duration'] = (total_stats['end_time'] - total_stats['start_time']).total_seconds()
        
        return total_stats
    
    def backup_source(self, 
                      source_path: str, 
                      destination_path: str,
                      exclude_patterns: Optional[List[str]] = None) -> Dict[str, any]:
        """
        Backup d'un dossier source complet.
        
        Args:
            source_path: Chemin du dossier source
            destination_path: Chemin de destination
            exclude_patterns: Patterns de fichiers à exclure
        
        Returns:
            Statistiques du backup
        """
        source_path = Path(source_path)
        destination_path = Path(destination_path)
        exclude_patterns = exclude_patterns or []
        
        if not source_path.exists():
            raise FileNotFoundError(f"Source introuvable : {source_path}")
        
        # Créer le dossier de destination
        ensure_directory(destination_path)
        
        # Stats pour ce source
        stats = {
            'files_backed_up': 0,
            'files_skipped': 0,
            'files_errors': 0,
            'total_size_original': 0,
            'total_size_encrypted': 0,
            'errors': []
        }
        
        # Parcourir tous les fichiers
        for file_path in source_path.rglob('*'):
            # Ignorer les dossiers
            if file_path.is_dir():
                continue
            
            # Vérifier les exclusions
            if is_excluded(file_path, exclude_patterns):
                stats['files_skipped'] += 1
                continue
            
            try:
                # Backup incrémental du fichier
                result = self.backup_file(file_path, destination_path)
                
                if result['backed_up']:
                    stats['files_backed_up'] += 1
                    stats['total_size_original'] += result['size_original']
                    stats['total_size_encrypted'] += result['size_encrypted']
                else:
                    stats['files_skipped'] += 1
                    
            except Exception as e:
                error_msg = f"Erreur backup {file_path}: {e}"
                stats['errors'].append(error_msg)
                stats['files_errors'] += 1
                self.db.log_error('file_backup_failed', error_msg, str(file_path))
        
        return stats
    
    def backup_file(self, file_path: Path, destination_base: Path) -> Dict[str, any]:
        """
        Backup incrémental d'un seul fichier.
        
        Args:
            file_path: Chemin du fichier à sauvegarder
            destination_base: Dossier de destination de base
        
        Returns:
            Dictionnaire avec résultat du backup
        """
        file_path = Path(file_path)
        
        # Calculer le hash du fichier
        file_hash = calculate_file_hash(file_path)
        
        # Vérifier si le fichier a changé
        if not self.db.has_file_changed(str(file_path), file_hash):
            return {
                'backed_up': False,
                'reason': 'unchanged',
                'size_original': 0,
                'size_encrypted': 0
            }
        
        # Lire le fichier
        with open(file_path, 'rb') as f:
            data = f.read()
        
        size_original = len(data)
        
        # Compression (si activée)
        if self.config.is_compression_enabled():
            data_compressed = self.compressor.compress(data)
            size_compressed = len(data_compressed)
            compression_ratio = calculate_compression_ratio(size_original, size_compressed)
        else:
            data_compressed = data
            size_compressed = size_original
            compression_ratio = 0.0
        
        # Chiffrement
        data_encrypted = self.crypto.encrypt_bytes(data_compressed)
        size_encrypted = len(data_encrypted)
        
        # Générer un nom de fichier unique basé sur le hash
        encrypted_filename = f"{file_hash}.enc"
        encrypted_path = destination_base / encrypted_filename
        
        # Sauvegarder le fichier chiffré
        with open(encrypted_path, 'wb') as f:
            f.write(data_encrypted)
        
        # Hash du fichier chiffré (pour vérification)
        encrypted_hash = calculate_file_hash(encrypted_path)
        
        # Enregistrer dans la DB
        self.db.add_backup(
            path_original=str(file_path.absolute()),
            path_encrypted=str(encrypted_path.absolute()),
            hash_original=file_hash,
            hash_encrypted=encrypted_hash,
            size_original=size_original,
            size_encrypted=size_encrypted,
            size_compressed=size_compressed if self.config.is_compression_enabled() else None,
            compression_ratio=compression_ratio if self.config.is_compression_enabled() else None
        )
        
        return {
            'backed_up': True,
            'size_original': size_original,
            'size_compressed': size_compressed,
            'size_encrypted': size_encrypted,
            'compression_ratio': compression_ratio,
            'file_hash': file_hash,
            'encrypted_path': str(encrypted_path)
        }
    
    def get_files_to_backup(self, 
                           source_path: Path,
                           exclude_patterns: Optional[List[str]] = None) -> List[Path]:
        """
        Liste tous les fichiers qui doivent être sauvegardés.
        
        Args:
            source_path: Chemin du dossier source
            exclude_patterns: Patterns à exclure
        
        Returns:
            Liste des fichiers à sauvegarder
        """
        exclude_patterns = exclude_patterns or []
        files = []
        
        for file_path in source_path.rglob('*'):
            if file_path.is_file() and not is_excluded(file_path, exclude_patterns):
                files.append(file_path)
        
        return files
    
    def verify_backup(self, file_path: str) -> bool:
        """
        Vérifie l'intégrité d'un backup.
        
        Args:
            file_path: Chemin du fichier original
        
        Returns:
            True si backup intact, False sinon
        """
        # Récupérer le dernier backup
        backup = self.db.get_latest_backup(file_path)
        
        if not backup:
            return False
        
        encrypted_path = Path(backup['path_encrypted'])
        
        if not encrypted_path.exists():
            return False
        
        # Vérifier le hash du fichier chiffré
        current_hash = calculate_file_hash(encrypted_path)
        
        return current_hash == backup['hash_encrypted']


class IncrementalBackup:
    """
    Helper class pour gérer les backups incrémentaux intelligents.
    """
    
    def __init__(self, engine: BackupEngine):
        self.engine = engine
    
    def get_changed_files(self, source_path: Path, exclude_patterns: Optional[List[str]] = None) -> List[Path]:
        """
        Détecte les fichiers qui ont changé depuis le dernier backup.
        
        Args:
            source_path: Dossier source
            exclude_patterns: Patterns à exclure
        
        Returns:
            Liste des fichiers modifiés
        """
        changed_files = []
        exclude_patterns = exclude_patterns or []
        
        for file_path in source_path.rglob('*'):
            if file_path.is_dir():
                continue
            
            if is_excluded(file_path, exclude_patterns):
                continue
            
            try:
                # Calculer le hash actuel
                current_hash = calculate_file_hash(file_path)
                
                # Vérifier si changé
                if self.engine.db.has_file_changed(str(file_path), current_hash):
                    changed_files.append(file_path)
                    
            except Exception:
                # En cas d'erreur, considérer comme changé
                changed_files.append(file_path)
        
        return changed_files
    
    def backup_changed_only(self, source_path: Path, destination_path: Path,
                           exclude_patterns: Optional[List[str]] = None) -> Dict[str, any]:
        """
        Backup uniquement des fichiers modifiés (incrémental pur).
        
        Args:
            source_path: Dossier source
            destination_path: Dossier destination
            exclude_patterns: Patterns à exclure
        
        Returns:
            Statistiques du backup
        """
        changed_files = self.get_changed_files(source_path, exclude_patterns)
        
        stats = {
            'files_scanned': 0,
            'files_changed': len(changed_files),
            'files_backed_up': 0,
            'files_errors': 0,
            'total_size': 0,
            'errors': []
        }
        
        for file_path in changed_files:
            try:
                result = self.engine.backup_file(file_path, destination_path)
                if result['backed_up']:
                    stats['files_backed_up'] += 1
                    stats['total_size'] += result['size_original']
            except Exception as e:
                stats['files_errors'] += 1
                stats['errors'].append(f"{file_path}: {e}")
        
        return stats