"""
Gestion de la configuration pour CryptBackup
Compatible Windows, Linux, macOS
Supporte : PC local, USB, Disque externe, NAS
"""

import yaml
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
import platform
import os
import shutil

from . import CONFIG_DIR, CONFIG_FILE, DEFAULT_COMPRESSION_LEVEL, DEFAULT_WATCH_INTERVAL


class DestinationType:
    """Types de destinations supportées."""
    LOCAL    = "local"      # Dossier sur le PC
    USB      = "usb"        # Clé USB
    EXTERNAL = "external"   # Disque dur externe
    NAS      = "nas"        # Serveur NAS (réseau)
    UNKNOWN  = "unknown"    # Inconnu


class Config:
    """
    Gestionnaire de configuration centralisé.
    Supporte : PC local, USB, Disque externe, NAS
    """

    DEFAULT_CONFIG = {
        'version': '1.0.1',
        'created_at': None,
        'system': {
            'os': None,
            'platform': None,
        },
        'encryption': {
            'algorithm': 'AES-256-GCM',
            'key': None,
        },
        'compression': {
            'enabled': True,
            'algorithm': 'zstd',
            'level': DEFAULT_COMPRESSION_LEVEL,
        },
        'sources': [],
        'destinations': {
            'primary': None,        # Destination principale
            'secondary': None,      # Destination secondaire
            'tertiary': None,       # Destination tertiaire (NAS par exemple)
        },
        'watch': {
            'enabled': True,
            'interval': DEFAULT_WATCH_INTERVAL,
            'realtime': True,
        },
        'retention': {
            'keep_days': 30,
            'keep_versions': 10,
            'auto_clean': False,
        },
        'priority': {
            'enabled': False,
            'model': 'simple',
        },
        'notifications': {
            'enabled': False,
            'on_error': True,
            'on_success': False,
        },
    }

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = Path(config_path) if config_path else CONFIG_FILE
        self.os_type = platform.system()
        self.data = {}

        if self.config_path.exists():
            self.load()
        else:
            self.data = self.DEFAULT_CONFIG.copy()
            self._set_system_info()

    def _set_system_info(self):
        """Enregistre les infos système."""
        if 'system' not in self.data:
            self.data['system'] = {}
        self.data['system']['os'] = self.os_type
        self.data['system']['platform'] = platform.platform()

    def load(self):
        """Charge la configuration depuis YAML."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.data = yaml.safe_load(f)
            self.data = self._merge_with_defaults(self.data)
            self._set_system_info()
        except Exception as e:
            raise ValueError(f"Erreur chargement config : {e}")

    def save(self):
        """Sauvegarde la configuration en YAML."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        if self.os_type != 'Windows':
            self._set_secure_permissions(self.config_path.parent)

        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.data, f, default_flow_style=False, allow_unicode=True)
            if self.os_type != 'Windows':
                self._set_secure_permissions(self.config_path)
        except Exception as e:
            raise ValueError(f"Erreur sauvegarde config : {e}")

    def _set_secure_permissions(self, path: Path):
        """Permissions sécurisées Unix."""
        if self.os_type == 'Windows':
            return
        try:
            os.chmod(path, 0o700 if path.is_dir() else 0o600)
        except Exception:
            pass

    def _merge_with_defaults(self, config: dict) -> dict:
        """Fusionne avec les valeurs par défaut."""
        merged = self.DEFAULT_CONFIG.copy()

        def deep_update(base: dict, update: dict):
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_update(base[key], value)
                else:
                    base[key] = value

        deep_update(merged, config)
        return merged

    # ================================================================
    # GESTION DES DESTINATIONS (LOCAL / USB / EXTERNE / NAS)
    # ================================================================

    def detect_destination_type(self, path: str) -> str:
        """
        Détecte automatiquement le type de destination.

        Returns:
            'local', 'usb', 'external', 'nas', 'unknown'

        Examples:
            C:\\Users\\backup     → local
            E:\\backup           → usb ou external
            \\\\NAS\\backup      → nas
            /home/user/backup    → local
            /media/usb/backup    → usb
            /mnt/nas/backup      → nas
        """
        path_obj = Path(path)
        path_str = str(path_obj)

        # Détection NAS (chemin réseau)
        if self.os_type == 'Windows':
            if path_str.startswith('\\\\'):
                return DestinationType.NAS
        else:
            # Linux/macOS : montage NAS dans /mnt ou /net
            path_lower = path_str.lower()
            if any(p in path_lower for p in ['/mnt/nas', '/net/', '/smb/', '/nfs/']):
                return DestinationType.NAS

        # Détection USB / Disque externe (Windows)
        if self.os_type == 'Windows':
            try:
                import ctypes
                drive = path_str[:3]  # Ex: "E:\\"
                drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive)
                # 2=removable(USB), 3=fixed(interne), 4=network, 5=cd
                if drive_type == 2:
                    return DestinationType.USB
                elif drive_type == 4:
                    return DestinationType.NAS
                elif drive_type == 3:
                    # Vérifier si c'est le disque système ou externe
                    system_drive = os.environ.get('SystemDrive', 'C:')
                    if not path_str.upper().startswith(system_drive.upper()):
                        return DestinationType.EXTERNAL
                    return DestinationType.LOCAL
            except Exception:
                pass

        # Détection USB / Disque externe (Linux/macOS)
        else:
            path_lower = path_str.lower()
            if any(p in path_lower for p in ['/media/', '/run/media/', '/volumes/']):
                return DestinationType.USB

        return DestinationType.LOCAL

    def check_destination_accessible(self, path: str) -> Dict:
        """
        Vérifie si une destination est accessible.

        Returns:
            Dict avec 'accessible', 'error', 'free_space', 'type'
        """
        result = {
            'accessible': False,
            'error': None,
            'free_space': 0,
            'free_space_formatted': '0 B',
            'type': DestinationType.UNKNOWN,
            'path': path
        }

        try:
            path_obj = Path(path)
            dest_type = self.detect_destination_type(path)
            result['type'] = dest_type

            # Vérifier existence
            if not path_obj.exists():
                # Tenter de créer le dossier
                try:
                    path_obj.mkdir(parents=True, exist_ok=True)
                except PermissionError:
                    result['error'] = f"Permission refusée pour créer : {path}"
                    return result
                except Exception as e:
                    result['error'] = f"Impossible de créer : {e}"
                    return result

            # Vérifier accès écriture
            test_file = path_obj / '.cryptbackup_test'
            try:
                test_file.touch()
                test_file.unlink()
            except Exception:
                result['error'] = "Pas de permission d'écriture"
                return result

            # Calculer espace libre
            disk_usage = shutil.disk_usage(path_obj)
            result['free_space'] = disk_usage.free
            result['free_space_formatted'] = self._format_size(disk_usage.free)
            result['accessible'] = True

        except FileNotFoundError:
            result['error'] = "Destination non trouvée (périphérique débranché ?)"
        except PermissionError:
            result['error'] = "Accès refusé"
        except Exception as e:
            result['error'] = str(e)

        return result

    def _format_size(self, size: int) -> str:
        """Formate une taille en bytes."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    def set_destination(self, path: str, destination_type: str = 'primary'):
        """
        Définit une destination de backup.

        Supporte : dossier local, USB, disque externe, NAS

        Args:
            path: Chemin de la destination
            destination_type: 'primary', 'secondary', ou 'tertiary'

        Examples:
            # Dossier local
            config.set_destination("C:\\Users\\Backup", "primary")

            # Clé USB (Windows)
            config.set_destination("E:\\Backup", "secondary")

            # Disque externe (Linux)
            config.set_destination("/media/user/disk/backup", "secondary")

            # NAS (Windows)
            config.set_destination("\\\\192.168.1.100\\backup", "tertiary")

            # NAS (Linux)
            config.set_destination("/mnt/nas/backup", "tertiary")
        """
        if destination_type not in ['primary', 'secondary', 'tertiary']:
            raise ValueError("destination_type doit être 'primary', 'secondary' ou 'tertiary'")

        # Expansion chemins Unix
        path_obj = Path(path).expanduser()

        # Pour les chemins réseau Windows (\\NAS\...), pas de resolve()
        if self.os_type == 'Windows' and str(path).startswith('\\\\'):
            resolved_path = str(path)
        else:
            resolved_path = str(path_obj)

        self.data['destinations'][destination_type] = resolved_path

    def get_destination(self, destination_type: str = 'primary') -> Optional[str]:
        """Récupère le chemin d'une destination."""
        return self.data['destinations'].get(destination_type)

    def get_all_destinations(self) -> List[Dict]:
        """
        Retourne toutes les destinations configurées avec leur statut.

        Returns:
            Liste de destinations avec type, chemin et accessibilité
        """
        destinations = []
        for dest_type in ['primary', 'secondary', 'tertiary']:
            path = self.data['destinations'].get(dest_type)
            if path:
                dest_type_detected = self.detect_destination_type(path)
                accessible_info = self.check_destination_accessible(path)
                destinations.append({
                    'name': dest_type,
                    'path': path,
                    'device_type': dest_type_detected,
                    'accessible': accessible_info['accessible'],
                    'free_space': accessible_info['free_space_formatted'],
                    'error': accessible_info.get('error')
                })
        return destinations

    def get_accessible_destinations(self) -> List[str]:
        """
        Retourne uniquement les destinations accessibles.
        Utile pendant un backup pour ignorer les périphériques déconnectés.
        """
        accessible = []
        for dest in self.get_all_destinations():
            if dest['accessible']:
                accessible.append(dest['path'])
        return accessible

    # ================================================================
    # GESTION DES SOURCES
    # ================================================================

    def get(self, key: str, default: Any = None) -> Any:
        """Récupère une valeur de config (supporte 'compression.level')."""
        keys = key.split('.')
        value = self.data
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """Définit une valeur de config (supporte 'compression.level')."""
        keys = key.split('.')
        data = self.data
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        data[keys[-1]] = value

    def add_source(self, path: str, exclude: Optional[List[str]] = None):
        """Ajoute un dossier source à surveiller."""
        path_obj = Path(path).expanduser().resolve()
        source = {
            'path': str(path_obj),
            'exclude': exclude or [],
            'added_at': datetime.now().isoformat(),
            'os': self.os_type,
        }
        for existing in self.data['sources']:
            if existing['path'] == source['path']:
                existing['exclude'] = source['exclude']
                return
        self.data['sources'].append(source)

    def remove_source(self, path: str) -> bool:
        """Retire un dossier source."""
        path_str = str(Path(path).expanduser().resolve())
        original_len = len(self.data['sources'])
        self.data['sources'] = [s for s in self.data['sources'] if s['path'] != path_str]
        return len(self.data['sources']) < original_len

    def get_sources(self) -> List[Dict]:
        """Retourne la liste des sources."""
        return self.data.get('sources', [])

    def get_encryption_key(self) -> Optional[str]:
        """Retourne la clé de chiffrement."""
        return self.data.get('encryption', {}).get('key')

    def set_encryption_key(self, key: str):
        """Définit la clé de chiffrement."""
        if 'encryption' not in self.data:
            self.data['encryption'] = {}
        self.data['encryption']['key'] = key

    def is_watch_enabled(self) -> bool:
        return self.data.get('watch', {}).get('enabled', True)

    def get_watch_interval(self) -> int:
        return int(self.data.get('watch', {}).get('interval', DEFAULT_WATCH_INTERVAL))

    def is_realtime_watch(self) -> bool:
        return self.data.get('watch', {}).get('realtime', True)

    def get_compression_level(self) -> int:
        return self.data.get('compression', {}).get('level', DEFAULT_COMPRESSION_LEVEL)

    def is_compression_enabled(self) -> bool:
        return self.data.get('compression', {}).get('enabled', True)

    def validate(self) -> List[str]:
        """Valide la configuration."""
        errors = []

        if not self.get_encryption_key():
            errors.append("Clé de chiffrement manquante")

        if not self.get_sources():
            errors.append("Aucune source configurée")

        if not self.get_destination('primary'):
            errors.append("Destination primaire manquante")

        # Vérifier sources existantes
        for source in self.get_sources():
            if not Path(source['path']).expanduser().exists():
                errors.append(f"Source introuvable : {source['path']}")

        # Vérifier destinations accessibles
        primary = self.get_destination('primary')
        if primary:
            check = self.check_destination_accessible(primary)
            if not check['accessible']:
                errors.append(f"Destination primaire inaccessible : {check['error']}")

        return errors

    def __str__(self) -> str:
        return yaml.dump(self.data, default_flow_style=False, allow_unicode=True)


def create_default_config(encryption_key: str) -> Config:
    """Crée une configuration par défaut."""
    config = Config()
    config.set_encryption_key(encryption_key)
    config.data['created_at'] = datetime.now().isoformat()
    config._set_system_info()
    return config