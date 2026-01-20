"""
Système de restauration pour MyBackup
Permet de récupérer des fichiers sauvegardés
"""

import zstandard as zstd
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

from .config import Config
from .crypto import CryptoManager
from .database import BackupDatabase
from .utils import calculate_file_hash, ensure_directory, format_size


class RestoreEngine:
    """
    Moteur de restauration de fichiers.
    """
    
    def __init__(self, config: Optional[Config] = None, db: Optional[BackupDatabase] = None):
        """
        Initialise le moteur de restauration.
        
        Args:
            config: Configuration
            db: Base de données
        """
        self.config = config or Config()
        self.db = db or BackupDatabase()
        
        # Initialiser le gestionnaire de crypto
        encryption_key = self.config.get_encryption_key()
        if not encryption_key:
            raise ValueError("Clé de chiffrement manquante")
        
        self.crypto = CryptoManager.from_key_string(encryption_key)
        self.decompressor = zstd.ZstdDecompressor()
    
    def restore_file(self, 
                     original_path: str,
                     destination_path: Optional[str] = None,
                     version: Optional[int] = None,
                     target_date: Optional[datetime] = None) -> Dict[str, any]:
        """
        Restaure un fichier spécifique.
        
        Args:
            original_path: Chemin original du fichier
            destination_path: Où restaurer (même emplacement si None)
            version: Numéro de version à restaurer (dernière si None)
            target_date: Restaurer la version à cette date (ignoré si version spécifiée)
        
        Returns:
            Statistiques de restauration
        
        Example:
            >>> restore = RestoreEngine()
            >>> stats = restore.restore_file("C:/Users/Dev/doc.txt")
            >>> print(stats['success'])
        """
        # Récupérer le backup approprié
        if version is not None:
            # Version spécifique
            backups = self.db.get_all_versions(original_path)
            backup = next((b for b in backups if b['version'] == version), None)
            if not backup:
                raise ValueError(f"Version {version} introuvable pour {original_path}")
        
        elif target_date is not None:
            # Backup le plus proche de la date
            backup = self.db.get_backup_by_date(original_path, target_date)
            if not backup:
                raise ValueError(f"Aucun backup trouvé avant {target_date} pour {original_path}")
        
        else:
            # Dernier backup
            backup = self.db.get_latest_backup(original_path)
            if not backup:
                raise ValueError(f"Aucun backup trouvé pour {original_path}")
        
        # Chemin du fichier chiffré
        encrypted_path = Path(backup['path_encrypted'])
        
        if not encrypted_path.exists():
            raise FileNotFoundError(f"Fichier de backup introuvable : {encrypted_path}")
        
        # Déterminer le chemin de destination
        if destination_path is None:
            destination_path = original_path
        
        destination_path = Path(destination_path)
        
        # Créer le dossier parent si nécessaire
        ensure_directory(destination_path.parent)
        
        # Lire le fichier chiffré
        with open(encrypted_path, 'rb') as f:
            encrypted_data = f.read()
        
        # Vérifier le hash du fichier chiffré
        current_encrypted_hash = calculate_file_hash(encrypted_path)
        if current_encrypted_hash != backup['hash_encrypted']:
            raise ValueError("Le fichier de backup est corrompu (hash invalide)")
        
        # Déchiffrer
        try:
            compressed_data = self.crypto.decrypt_bytes(encrypted_data)
        except Exception as e:
            raise ValueError(f"Échec du déchiffrement (clé invalide ou fichier corrompu): {e}")
        
        # Décompresser (si nécessaire)
        if backup['size_compressed'] is not None:
            # Le fichier était compressé
            original_data = self.decompressor.decompress(compressed_data)
        else:
            original_data = compressed_data
        
        # Vérifier le hash du fichier restauré
        restored_hash = calculate_file_hash(original_data, algorithm='sha256')
        if restored_hash != backup['hash_original']:
            raise ValueError("Les données restaurées sont corrompues (hash invalide)")
        
        # Écrire le fichier restauré
        with open(destination_path, 'wb') as f:
            f.write(original_data)
        
        return {
            'success': True,
            'original_path': original_path,
            'restored_path': str(destination_path),
            'version': backup['version'],
            'timestamp': backup['timestamp'],
            'size': len(original_data),
            'size_formatted': format_size(len(original_data))
        }
    
    def restore_directory(self,
                         source_directory: str,
                         destination_directory: str,
                         target_date: Optional[datetime] = None,
                         recursive: bool = True) -> Dict[str, any]:
        """
        Restaure tous les fichiers d'un dossier.
        
        Args:
            source_directory: Dossier source original
            destination_directory: Où restaurer les fichiers
            target_date: Date cible (dernières versions si None)
            recursive: Inclure les sous-dossiers
        
        Returns:
            Statistiques de restauration
        """
        source_directory = str(Path(source_directory).absolute())
        destination_directory = Path(destination_directory)
        
        # Créer le dossier de destination
        ensure_directory(destination_directory)
        
        # Trouver tous les fichiers du dossier source
        if recursive:
            pattern = f"{source_directory}%"
        else:
            pattern = source_directory
        
        backups = self.db.search_backups(pattern, limit=10000)
        
        stats = {
            'files_found': 0,
            'files_restored': 0,
            'files_failed': 0,
            'total_size': 0,
            'errors': []
        }
        
        # Grouper par fichier et prendre la dernière version
        files_to_restore = {}
        for backup in backups:
            path = backup['path_original']
            
            # Filtrer selon target_date
            if target_date:
                backup_date = datetime.fromisoformat(backup['timestamp'])
                if backup_date > target_date:
                    continue
            
            # Garder la version la plus récente par fichier
            if path not in files_to_restore:
                files_to_restore[path] = backup
            else:
                if backup['version'] > files_to_restore[path]['version']:
                    files_to_restore[path] = backup
        
        stats['files_found'] = len(files_to_restore)
        
        # Restaurer chaque fichier
        for original_path, backup in files_to_restore.items():
            try:
                # Calculer le chemin relatif
                rel_path = Path(original_path).relative_to(source_directory)
                dest_path = destination_directory / rel_path
                
                # Restaurer
                result = self.restore_file(
                    original_path=original_path,
                    destination_path=str(dest_path),
                    version=backup['version']
                )
                
                stats['files_restored'] += 1
                stats['total_size'] += result['size']
                
            except Exception as e:
                error_msg = f"Échec restauration {original_path}: {e}"
                stats['errors'].append(error_msg)
                stats['files_failed'] += 1
        
        return stats
    
    def restore_all_to_date(self, target_date: datetime, destination_directory: str) -> Dict[str, any]:
        """
        Restaure TOUS les fichiers à une date donnée.
        
        Args:
            target_date: Date cible
            destination_directory: Dossier de destination
        
        Returns:
            Statistiques de restauration
        """
        destination_directory = Path(destination_directory)
        ensure_directory(destination_directory)
        
        # Récupérer tous les fichiers
        backups = self.db.search_backups('', limit=100000)
        
        stats = {
            'files_found': 0,
            'files_restored': 0,
            'files_failed': 0,
            'total_size': 0,
            'errors': []
        }
        
        # Grouper par fichier
        files_to_restore = {}
        for backup in backups:
            backup_date = datetime.fromisoformat(backup['timestamp'])
            if backup_date > target_date:
                continue
            
            path = backup['path_original']
            if path not in files_to_restore:
                files_to_restore[path] = backup
            else:
                if backup['version'] > files_to_restore[path]['version']:
                    files_to_restore[path] = backup
        
        stats['files_found'] = len(files_to_restore)
        
        # Restaurer
        for original_path, backup in files_to_restore.items():
            try:
                # Utiliser un chemin plat dans destination (éviter conflits)
                filename = Path(original_path).name
                dest_path = destination_directory / filename
                
                # Gérer les doublons de noms
                counter = 1
                while dest_path.exists():
                    stem = Path(original_path).stem
                    suffix = Path(original_path).suffix
                    dest_path = destination_directory / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                result = self.restore_file(
                    original_path=original_path,
                    destination_path=str(dest_path),
                    version=backup['version']
                )
                
                stats['files_restored'] += 1
                stats['total_size'] += result['size']
                
            except Exception as e:
                error_msg = f"Échec {original_path}: {e}"
                stats['errors'].append(error_msg)
                stats['files_failed'] += 1
        
        return stats
    
    def list_available_files(self, search_pattern: str = "") -> List[Dict]:
        """
        Liste tous les fichiers disponibles pour restauration.
        
        Args:
            search_pattern: Pattern de recherche (optionnel)
        
        Returns:
            Liste des fichiers avec leurs versions
        """
        backups = self.db.search_backups(search_pattern, limit=10000)
        
        # Grouper par fichier
        files = {}
        for backup in backups:
            path = backup['path_original']
            if path not in files:
                files[path] = {
                    'path': path,
                    'versions': [],
                    'latest_backup': backup['timestamp'],
                    'total_versions': 0
                }
            
            files[path]['versions'].append({
                'version': backup['version'],
                'timestamp': backup['timestamp'],
                'size': backup['size_original']
            })
            files[path]['total_versions'] += 1
        
        return list(files.values())


def calculate_file_hash(data, algorithm='sha256'):
    """Helper pour calculer hash depuis bytes ou Path."""
    import hashlib
    from pathlib import Path
    
    if isinstance(data, (str, Path)):
        # C'est un chemin de fichier
        filepath = Path(data)
        hash_obj = hashlib.new(algorithm)
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    else:
        # C'est des bytes
        return hashlib.new(algorithm, data).hexdigest()