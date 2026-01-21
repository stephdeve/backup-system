"""
Module de surveillance automatique avec Watchdog
Détecte les changements en temps réel et lance des backups automatiques
"""

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
from typing import List, Optional, Set
from datetime import datetime
import time
import threading
from queue import Queue

from .backup import BackupEngine
from .config import Config
from .utils import is_excluded


class BackupEventHandler(FileSystemEventHandler):
    """
    Gestionnaire d'événements pour Watchdog.
    Détecte les modifications de fichiers et les ajoute à la file d'attente.
    """
    
    def __init__(self, queue: Queue, exclude_patterns: List[str] = None):
        """
        Initialise le gestionnaire.
        
        Args:
            queue: File d'attente pour les fichiers modifiés
            exclude_patterns: Patterns de fichiers à exclure
        """
        super().__init__()
        self.queue = queue
        self.exclude_patterns = exclude_patterns or []
        self.last_modified = {}  # Éviter les doublons
    
    def _should_process(self, path: str) -> bool:
        """Vérifie si un fichier doit être traité."""
        path_obj = Path(path)
        
        # Ignorer les dossiers
        if path_obj.is_dir():
            return False
        
        # Vérifier exclusions
        if is_excluded(path_obj, self.exclude_patterns):
            return False
        
        # Éviter doublons (même fichier modifié < 1 seconde)
        now = time.time()
        if path in self.last_modified:
            if now - self.last_modified[path] < 1.0:
                return False
        
        self.last_modified[path] = now
        return True
    
    def on_modified(self, event):
        """Appelé quand un fichier est modifié."""
        if self._should_process(event.src_path):
            self.queue.put(('modified', event.src_path, datetime.now()))
    
    def on_created(self, event):
        """Appelé quand un fichier est créé."""
        if self._should_process(event.src_path):
            self.queue.put(('created', event.src_path, datetime.now()))
    
    def on_deleted(self, event):
        """Appelé quand un fichier est supprimé."""
        if not event.is_directory:
            self.queue.put(('deleted', event.src_path, datetime.now()))


class BackupWatcher:
    """
    Surveillant principal qui coordonne Watchdog et les backups automatiques.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialise le surveillant.
        
        Args:
            config: Configuration MyBackup
        """
        self.config = config or Config()
        self.observers = []
        self.queue = Queue()
        self.running = False
        self.backup_thread = None
        self.stats = {
            'files_detected': 0,
            'files_backed_up': 0,
            'last_backup': None,
            'errors': []
        }
    
    def start(self):
        """Démarre la surveillance automatique."""
        if self.running:
            return
        
        self.running = True
        
        # Créer observateurs pour chaque source
        sources = self.config.get_sources()
        
        if not sources:
            raise ValueError("Aucune source configurée")
        
        for source in sources:
            observer = Observer()
            handler = BackupEventHandler(
                queue=self.queue,
                exclude_patterns=source.get('exclude', [])
            )
            
            observer.schedule(
                handler,
                source['path'],
                recursive=True
            )
            
            observer.start()
            self.observers.append(observer)
        
        # Démarrer thread de backup
        self.backup_thread = threading.Thread(target=self._backup_worker, daemon=True)
        self.backup_thread.start()
    
    def stop(self):
        """Arrête la surveillance."""
        self.running = False
        
        # Arrêter tous les observateurs
        for observer in self.observers:
            observer.stop()
        
        # Attendre la fin
        for observer in self.observers:
            observer.join(timeout=5)
        
        if self.backup_thread:
            self.backup_thread.join(timeout=5)
        
        self.observers.clear()
    
    def _backup_worker(self):
        """
        Worker thread qui traite la file d'attente.
        Effectue des backups par batch toutes les N secondes.
        """
        interval = self.config.get_watch_interval()
        pending_files = set()
        
        while self.running:
            # Collecter les fichiers modifiés pendant l'intervalle
            start_time = time.time()
            
            while time.time() - start_time < interval:
                try:
                    if not self.queue.empty():
                        event_type, file_path, timestamp = self.queue.get(timeout=1)
                        
                        if event_type in ('modified', 'created'):
                            pending_files.add(file_path)
                            self.stats['files_detected'] += 1
                        elif event_type == 'deleted':
                            # Retirer des fichiers en attente si supprimé
                            pending_files.discard(file_path)
                    else:
                        time.sleep(1)
                except:
                    time.sleep(1)
            
            # Backup des fichiers en attente
            if pending_files:
                self._backup_files(pending_files)
                pending_files.clear()
    
    def _backup_files(self, file_paths: Set[str]):
        """
        Effectue le backup d'un ensemble de fichiers.
        
        Args:
            file_paths: Chemins des fichiers à sauvegarder
        """
        try:
            engine = BackupEngine(self.config)
            destination = self.config.get_destination('primary')
            
            if not destination:
                raise ValueError("Destination non configurée")
            
            backed_up = 0
            
            for file_path in file_paths:
                try:
                    path = Path(file_path)
                    if path.exists():
                        result = engine.backup_file(path, Path(destination))
                        if result['backed_up']:
                            backed_up += 1
                except Exception as e:
                    self.stats['errors'].append(f"{file_path}: {e}")
            
            self.stats['files_backed_up'] += backed_up
            self.stats['last_backup'] = datetime.now()
            
        except Exception as e:
            self.stats['errors'].append(f"Backup batch échoué: {e}")
    
    def get_stats(self) -> dict:
        """Retourne les statistiques de surveillance."""
        return {
            **self.stats,
            'running': self.running,
            'observers': len(self.observers),
            'pending': self.queue.qsize()
        }


class WatcherDaemon:
    """
    Daemon pour exécuter le watcher en arrière-plan.
    """
    
    def __init__(self, config: Optional[Config] = None):
        self.watcher = BackupWatcher(config)
        self.running = False
    
    def start(self):
        """Démarre le daemon."""
        print(" Démarrage de la surveillance automatique...")
        self.watcher.start()
        self.running = True
        print(" Surveillance active")
        print(f" Surveillant {len(self.watcher.observers)} dossier(s)")
        print(f"  Backup automatique toutes les {self.watcher.config.get_watch_interval()}s")
        print("\nAppuyez sur Ctrl+C pour arrêter")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n  Arrêt demandé...")
            self.stop()
    
    def stop(self):
        """Arrête le daemon."""
        self.running = False
        self.watcher.stop()
        print(" Surveillance arrêtée")
        
        # Afficher stats
        stats = self.watcher.get_stats()
        print(f"\n Statistiques :")
        print(f"  Fichiers détectés : {stats['files_detected']}")
        print(f"  Fichiers sauvegardés : {stats['files_backed_up']}")
        if stats['last_backup']:
            print(f"  Dernier backup : {stats['last_backup']}")
        if stats['errors']:
            print(f"  Erreurs : {len(stats['errors'])}")