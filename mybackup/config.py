"""
Gestion de la configuration pour MyBackup
Utilise YAML pour une configuration lisible
"""

import yaml
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
from . import CONFIG_DIR, CONFIG_FILE, DEFAULT_COMPRESSION_LEVEL, DEFAULT_WATCH_INTERVAL


class Config:
    """
    Gestionnaire de configuration centralisé.
    """
    
    DEFAULT_CONFIG = {
        'version': '1.0.0',
        'created_at': None,
        'encryption': {
            'algorithm': 'AES-256-GCM',
            'key': None,  # Sera généré à l'init
        },
        'compression': {
            'enabled': True,
            'algorithm': 'zstd',
            'level': DEFAULT_COMPRESSION_LEVEL,
        },
        'sources': [],  # Liste des dossiers à sauvegarder
        'destinations': {
            'primary': None,
            'secondary': None,
        },
        'watch': {
            'enabled': True,
            'interval': DEFAULT_WATCH_INTERVAL,  # secondes
            'realtime': True,
        },
        'retention': {
            'keep_days': 30,
            'keep_versions': 10,
            'auto_clean': False,
        },
        'priority': {
            'enabled': False,
            'model': 'simple',  # 'simple' ou 'ml'
        },
        'notifications': {
            'enabled': False,
            'on_error': True,
            'on_success': False,
        },
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialise la configuration.
        
        Args:
            config_path: Chemin du fichier de config (utilise le défaut si None)
        """
        self.config_path = Path(config_path) if config_path else CONFIG_FILE
        self.data = {}
        
        if self.config_path.exists():
            self.load()
        else:
            self.data = self.DEFAULT_CONFIG.copy()
    
    def load(self):
        """Charge la configuration depuis le fichier YAML."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.data = yaml.safe_load(f)
            
            # Merge avec config par défaut pour nouvelles clés
            self.data = self._merge_with_defaults(self.data)
        except Exception as e:
            raise ValueError(f"Erreur lors du chargement de la config : {e}")
    
    def save(self):
        """Sauvegarde la configuration dans le fichier YAML."""
        # Créer le dossier si nécessaire
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.data, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            raise ValueError(f"Erreur lors de la sauvegarde de la config : {e}")
    
    def _merge_with_defaults(self, config: dict) -> dict:
        """Fusionne la config chargée avec les valeurs par défaut."""
        merged = self.DEFAULT_CONFIG.copy()
        
        def deep_update(base: dict, update: dict):
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_update(base[key], value)
                else:
                    base[key] = value
        
        deep_update(merged, config)
        return merged
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Récupère une valeur de config (supporte nested keys avec '.').
        
        Args:
            key: Clé de config (ex: 'compression.level')
            default: Valeur par défaut si clé inexistante
        
        Returns:
            Valeur de la config
        
        Example:
            >>> config = Config()
            >>> level = config.get('compression.level')
        """
        keys = key.split('.')
        value = self.data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """
        Définit une valeur de config (supporte nested keys avec '.').
        
        Args:
            key: Clé de config (ex: 'compression.level')
            value: Nouvelle valeur
        
        Example:
            >>> config = Config()
            >>> config.set('compression.level', 5)
            >>> config.save()
        """
        keys = key.split('.')
        data = self.data
        
        # Naviguer jusqu'à l'avant-dernière clé
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        
        # Définir la valeur finale
        data[keys[-1]] = value
    
    def add_source(self, path: str, exclude: Optional[List[str]] = None):
        """
        Ajoute un dossier source à surveiller.
        
        Args:
            path: Chemin du dossier
            exclude: Liste de patterns à exclure
        
        Example:
            >>> config = Config()
            >>> config.add_source("C:/Users/Dev/Documents", ["*.tmp", "~*"])
        """
        source = {
            'path': str(Path(path).resolve()),
            'exclude': exclude or [],
            'added_at': datetime.now().isoformat(),
        }
        
        # Vérifier si déjà présent
        for existing in self.data['sources']:
            if existing['path'] == source['path']:
                existing['exclude'] = source['exclude']
                return
        
        self.data['sources'].append(source)
    
    def remove_source(self, path: str) -> bool:
        """
        Retire un dossier source.
        
        Args:
            path: Chemin du dossier à retirer
        
        Returns:
            True si retiré, False si pas trouvé
        """
        path = str(Path(path).resolve())
        original_len = len(self.data['sources'])
        self.data['sources'] = [s for s in self.data['sources'] if s['path'] != path]
        return len(self.data['sources']) < original_len
    
    def get_sources(self) -> List[Dict]:
        """
        Retourne la liste de tous les dossiers sources.
        
        Returns:
            Liste de dictionnaires avec infos des sources
        """
        return self.data.get('sources', [])
    
    def set_destination(self, path: str, destination_type: str = 'primary'):
        """
        Définit une destination de backup.
        
        Args:
            path: Chemin de la destination
            destination_type: 'primary' ou 'secondary'
        
        Example:
            >>> config = Config()
            >>> config.set_destination("D:/Backups", "primary")
            >>> config.set_destination("//NAS/backups", "secondary")
        """
        if destination_type not in ['primary', 'secondary']:
            raise ValueError("destination_type doit être 'primary' ou 'secondary'")
        
        self.data['destinations'][destination_type] = str(Path(path).resolve())
    
    def get_destination(self, destination_type: str = 'primary') -> Optional[str]:
        """
        Récupère le chemin d'une destination.
        
        Args:
            destination_type: 'primary' ou 'secondary'
        
        Returns:
            Chemin de la destination ou None
        """
        return self.data['destinations'].get(destination_type)
    
    def get_encryption_key(self) -> Optional[str]:
        """Retourne la clé de chiffrement."""
        return self.data.get('encryption', {}).get('key')
    
    def set_encryption_key(self, key: str):
        """Définit la clé de chiffrement."""
        if 'encryption' not in self.data:
            self.data['encryption'] = {}
        self.data['encryption']['key'] = key
    
    def is_watch_enabled(self) -> bool:
        """Vérifie si la surveillance est activée."""
        return self.data.get('watch', {}).get('enabled', True)
    
    def get_watch_interval(self) -> int:
        """Retourne l'intervalle de surveillance en secondes."""
        interval = self.data.get('watch', {}).get('interval', DEFAULT_WATCH_INTERVAL)
        return int(interval)
    
    def is_realtime_watch(self) -> bool:
        """Vérifie si la surveillance temps réel est activée."""
        return self.data.get('watch', {}).get('realtime', True)
    
    def get_compression_level(self) -> int:
        """Retourne le niveau de compression."""
        return self.data.get('compression', {}).get('level', DEFAULT_COMPRESSION_LEVEL)
    
    def is_compression_enabled(self) -> bool:
        """Vérifie si la compression est activée."""
        return self.data.get('compression', {}).get('enabled', True)
    
    def validate(self) -> List[str]:
        """
        Valide la configuration.
        
        Returns:
            Liste des erreurs (vide si OK)
        """
        errors = []
        
        # Vérifier qu'une clé de chiffrement existe
        if not self.get_encryption_key():
            errors.append("Clé de chiffrement manquante")
        
        # Vérifier qu'au moins une source existe
        if not self.get_sources():
            errors.append("Aucune source configurée")
        
        # Vérifier qu'une destination primaire existe
        if not self.get_destination('primary'):
            errors.append("Destination primaire manquante")
        
        # Vérifier que les chemins sources existent
        for source in self.get_sources():
            if not Path(source['path']).exists():
                errors.append(f"Source introuvable : {source['path']}")
        
        return errors
    
    def __str__(self) -> str:
        """Représentation string de la config."""
        return yaml.dump(self.data, default_flow_style=False, allow_unicode=True)


def create_default_config(encryption_key: str) -> Config:
    """
    Crée une configuration par défaut.
    
    Args:
        encryption_key: Clé de chiffrement à utiliser
    
    Returns:
        Instance de Config
    
    Example:
        >>> from mybackup.crypto import CryptoManager
        >>> key = CryptoManager.generate_key().decode('utf-8')
        >>> config = create_default_config(key)
    """
    config = Config()
    config.set_encryption_key(encryption_key)
    config.data['created_at'] = datetime.now().isoformat()
    return config