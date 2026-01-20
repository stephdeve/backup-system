"""
Gestion de la base de données SQLite pour MyBackup
Stocke les métadonnées des backups et versions
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager
from . import DB_FILE


class BackupDatabase:
    """
    Gestionnaire de base de données pour les métadonnées de backup.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialise la connexion à la base de données.
        
        Args:
            db_path: Chemin du fichier DB (utilise le défaut si None)
        """
        self.db_path = Path(db_path) if db_path else DB_FILE
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager pour gérer les connexions DB."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par nom
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_database(self):
        """Crée les tables si elles n'existent pas."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Table principale des backups
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS backups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path_original TEXT NOT NULL,
                    path_encrypted TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    hash_original TEXT NOT NULL,
                    hash_encrypted TEXT NOT NULL,
                    size_original INTEGER NOT NULL,
                    size_compressed INTEGER,
                    size_encrypted INTEGER NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    compression_ratio REAL,
                    status TEXT DEFAULT 'completed',
                    UNIQUE(path_original, version)
                )
            ''')
            
            # Index pour recherches rapides
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_path 
                ON backups(path_original)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON backups(timestamp)
            ''')
            
            # Table pour les statistiques
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL UNIQUE,
                    files_backed_up INTEGER DEFAULT 0,
                    total_size_original INTEGER DEFAULT 0,
                    total_size_encrypted INTEGER DEFAULT 0,
                    backup_duration REAL DEFAULT 0
                )
            ''')
            
            # Table pour les logs d'erreurs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    error_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    file_path TEXT
                )
            ''')
            
            conn.commit()
    
    def add_backup(self, 
                   path_original: str,
                   path_encrypted: str,
                   hash_original: str,
                   hash_encrypted: str,
                   size_original: int,
                   size_encrypted: int,
                   size_compressed: Optional[int] = None,
                   compression_ratio: Optional[float] = None) -> int:
        """
        Enregistre un nouveau backup dans la base.
        
        Args:
            path_original: Chemin original du fichier
            path_encrypted: Chemin du fichier chiffré
            hash_original: Hash du fichier original
            hash_encrypted: Hash du fichier chiffré
            size_original: Taille originale en bytes
            size_encrypted: Taille chiffrée en bytes
            size_compressed: Taille après compression (optionnel)
            compression_ratio: Ratio de compression (optionnel)
        
        Returns:
            ID du backup créé
        
        Example:
            >>> db = BackupDatabase()
            >>> backup_id = db.add_backup(
            ...     path_original="C:/Users/Dev/doc.txt",
            ...     path_encrypted="D:/Backups/abc123.enc",
            ...     hash_original="abc123...",
            ...     hash_encrypted="xyz789...",
            ...     size_original=10240,
            ...     size_encrypted=8192
            ... )
        """
        # Calculer le numéro de version
        version = self.get_next_version(path_original)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO backups (
                    path_original, path_encrypted, version,
                    hash_original, hash_encrypted,
                    size_original, size_compressed, size_encrypted,
                    timestamp, compression_ratio, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                path_original, path_encrypted, version,
                hash_original, hash_encrypted,
                size_original, size_compressed, size_encrypted,
                datetime.now(), compression_ratio, 'completed'
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_next_version(self, path_original: str) -> int:
        """
        Obtient le prochain numéro de version pour un fichier.
        
        Args:
            path_original: Chemin du fichier
        
        Returns:
            Numéro de version suivant (1 si premier backup)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT MAX(version) as max_version 
                FROM backups 
                WHERE path_original = ?
            ''', (path_original,))
            
            result = cursor.fetchone()
            max_version = result['max_version']
            
            return (max_version + 1) if max_version is not None else 1
    
    def get_latest_backup(self, path_original: str) -> Optional[Dict[str, Any]]:
        """
        Récupère le backup le plus récent d'un fichier.
        
        Args:
            path_original: Chemin du fichier
        
        Returns:
            Dictionnaire avec infos du backup ou None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM backups
                WHERE path_original = ?
                ORDER BY version DESC
                LIMIT 1
            ''', (path_original,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_backup_by_date(self, path_original: str, target_date: datetime) -> Optional[Dict[str, Any]]:
        """
        Récupère le backup le plus proche d'une date donnée.
        
        Args:
            path_original: Chemin du fichier
            target_date: Date cible
        
        Returns:
            Dictionnaire avec infos du backup ou None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM backups
                WHERE path_original = ? AND timestamp <= ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (path_original, target_date))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_versions(self, path_original: str) -> List[Dict[str, Any]]:
        """
        Récupère toutes les versions d'un fichier.
        
        Args:
            path_original: Chemin du fichier
        
        Returns:
            Liste des backups, triés par version
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM backups
                WHERE path_original = ?
                ORDER BY version ASC
            ''', (path_original,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def file_exists_in_backup(self, path_original: str) -> bool:
        """
        Vérifie si un fichier a déjà été sauvegardé.
        
        Args:
            path_original: Chemin du fichier
        
        Returns:
            True si au moins un backup existe
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) as count FROM backups
                WHERE path_original = ?
            ''', (path_original,))
            
            result = cursor.fetchone()
            return result['count'] > 0
    
    def has_file_changed(self, path_original: str, current_hash: str) -> bool:
        """
        Vérifie si un fichier a changé depuis le dernier backup.
        
        Args:
            path_original: Chemin du fichier
            current_hash: Hash actuel du fichier
        
        Returns:
            True si le fichier a changé ou n'existe pas en backup
        """
        latest = self.get_latest_backup(path_original)
        
        if latest is None:
            return True  # Pas de backup, donc "changé"
        
        return latest['hash_original'] != current_hash
    
    def get_total_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques globales.
        
        Returns:
            Dictionnaire avec stats
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Nombre total de fichiers uniques
            cursor.execute('SELECT COUNT(DISTINCT path_original) as count FROM backups')
            unique_files = cursor.fetchone()['count']
            
            # Nombre total de versions
            cursor.execute('SELECT COUNT(*) as count FROM backups')
            total_versions = cursor.fetchone()['count']
            
            # Taille totale originale
            cursor.execute('SELECT SUM(size_original) as total FROM backups')
            total_original = cursor.fetchone()['total'] or 0
            
            # Taille totale chiffrée
            cursor.execute('SELECT SUM(size_encrypted) as total FROM backups')
            total_encrypted = cursor.fetchone()['total'] or 0
            
            # Date du dernier backup
            cursor.execute('SELECT MAX(timestamp) as last_backup FROM backups')
            last_backup = cursor.fetchone()['last_backup']
            
            return {
                'unique_files': unique_files,
                'total_versions': total_versions,
                'total_size_original': total_original,
                'total_size_encrypted': total_encrypted,
                'space_saved': total_original - total_encrypted if total_encrypted else 0,
                'last_backup': last_backup,
            }
    
    def get_recent_backups(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Récupère les backups les plus récents.
        
        Args:
            limit: Nombre de résultats à retourner
        
        Returns:
            Liste des backups récents
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM backups
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def log_error(self, error_type: str, error_message: str, file_path: Optional[str] = None):
        """
        Enregistre une erreur dans la base.
        
        Args:
            error_type: Type d'erreur (ex: 'encryption_failed')
            error_message: Message d'erreur détaillé
            file_path: Chemin du fichier concerné (optionnel)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO errors (timestamp, error_type, error_message, file_path)
                VALUES (?, ?, ?, ?)
            ''', (datetime.now(), error_type, error_message, file_path))
            
            conn.commit()
    
    def get_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Récupère les erreurs récentes.
        
        Args:
            limit: Nombre d'erreurs à retourner
        
        Returns:
            Liste des erreurs
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM errors
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def clean_old_versions(self, keep_days: int = 30, keep_versions: int = 10) -> int:
        """
        Nettoie les anciennes versions selon la politique de rétention.
        
        Args:
            keep_days: Garder les versions des N derniers jours
            keep_versions: Garder au moins N versions par fichier
        
        Returns:
            Nombre de versions supprimées
        """
        cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - keep_days)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Supprimer les vieilles versions, mais garder au moins keep_versions par fichier
            cursor.execute('''
                DELETE FROM backups
                WHERE id IN (
                    SELECT id FROM (
                        SELECT id,
                               ROW_NUMBER() OVER (PARTITION BY path_original ORDER BY version DESC) as rn
                        FROM backups
                        WHERE timestamp < ?
                    ) WHERE rn > ?
                )
            ''', (cutoff_date, keep_versions))
            
            deleted = cursor.rowcount
            conn.commit()
            
            return deleted
    
    def search_backups(self, search_term: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Recherche des backups par nom de fichier.
        
        Args:
            search_term: Terme de recherche
            limit: Nombre de résultats max
        
        Returns:
            Liste des backups correspondants
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM backups
                WHERE path_original LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (f'%{search_term}%', limit))
            
            return [dict(row) for row in cursor.fetchall()]