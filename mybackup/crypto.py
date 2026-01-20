"""
Module de chiffrement pour MyBackup
Utilise Fernet (AES-256-GCM) pour un chiffrement sécurisé
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pathlib import Path
from typing import Union, Optional
import base64
import os


class CryptoManager:
    """
    Gestionnaire de chiffrement/déchiffrement.
    Utilise Fernet (AES-256-GCM) pour la sécurité.
    """
    
    def __init__(self, key: Optional[bytes] = None):
        """
        Initialise le gestionnaire de crypto.
        
        Args:
            key: Clé de chiffrement (génère une nouvelle si None)
        """
        if key is None:
            self.key = Fernet.generate_key()
        else:
            self.key = key
        
        self.fernet = Fernet(self.key)
    
    @staticmethod
    def generate_key() -> bytes:
        """
        Génère une nouvelle clé de chiffrement aléatoire.
        
        Returns:
            Clé de 44 bytes en base64
        
        Example:
            >>> key = CryptoManager.generate_key()
            >>> print(len(key))
            44
        """
        return Fernet.generate_key()
    
    @staticmethod
    def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> tuple:
        """
        Dérive une clé à partir d'un mot de passe (pour usage futur).
        
        Args:
            password: Mot de passe utilisateur
            salt: Salt pour la dérivation (génère si None)
        
        Returns:
            Tuple (clé, salt)
        
        Example:
            >>> key, salt = CryptoManager.derive_key_from_password("MonMotDePasse123")
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    def encrypt_bytes(self, data: bytes) -> bytes:
        """
        Chiffre des données binaires.
        
        Args:
            data: Données à chiffrer
        
        Returns:
            Données chiffrées
        
        Example:
            >>> crypto = CryptoManager()
            >>> encrypted = crypto.encrypt_bytes(b"secret data")
        """
        return self.fernet.encrypt(data)
    
    def decrypt_bytes(self, encrypted_data: bytes) -> bytes:
        """
        Déchiffre des données binaires.
        
        Args:
            encrypted_data: Données chiffrées
        
        Returns:
            Données déchiffrées
        
        Raises:
            cryptography.fernet.InvalidToken: Si la clé est incorrecte ou données corrompues
        
        Example:
            >>> crypto = CryptoManager()
            >>> encrypted = crypto.encrypt_bytes(b"secret")
            >>> decrypted = crypto.decrypt_bytes(encrypted)
        """
        return self.fernet.decrypt(encrypted_data)
    
    def encrypt_file(self, input_path: Union[str, Path], output_path: Union[str, Path]) -> dict:
        """
        Chiffre un fichier complet.
        
        Args:
            input_path: Chemin du fichier à chiffrer
            output_path: Chemin du fichier chiffré de sortie
        
        Returns:
            Dictionnaire avec stats (taille avant/après)
        
        Example:
            >>> crypto = CryptoManager()
            >>> stats = crypto.encrypt_file("document.txt", "document.txt.enc")
            >>> print(stats['original_size'], stats['encrypted_size'])
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Fichier introuvable : {input_path}")
        
        with open(input_path, 'rb') as f:
            data = f.read()
        
        original_size = len(data)
        encrypted_data = self.encrypt_bytes(data)
        
        with open(output_path, 'wb') as f:
            f.write(encrypted_data)
        
        encrypted_size = len(encrypted_data)
        
        return {
            'original_size': original_size,
            'encrypted_size': encrypted_size,
            'overhead': encrypted_size - original_size,
            'overhead_percentage': ((encrypted_size - original_size) / original_size * 100) if original_size > 0 else 0
        }
    
    def decrypt_file(self, input_path: Union[str, Path], output_path: Union[str, Path]) -> dict:
        """
        Déchiffre un fichier complet.
        
        Args:
            input_path: Chemin du fichier chiffré
            output_path: Chemin du fichier déchiffré de sortie
        
        Returns:
            Dictionnaire avec stats
        
        Raises:
            cryptography.fernet.InvalidToken: Si déchiffrement échoue
        
        Example:
            >>> crypto = CryptoManager()
            >>> stats = crypto.decrypt_file("document.txt.enc", "document_restored.txt")
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Fichier chiffré introuvable : {input_path}")
        
        with open(input_path, 'rb') as f:
            encrypted_data = f.read()
        
        encrypted_size = len(encrypted_data)
        
        try:
            decrypted_data = self.decrypt_bytes(encrypted_data)
        except Exception as e:
            raise ValueError(f"Échec du déchiffrement (clé incorrecte ou fichier corrompu) : {e}")
        
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
        
        decrypted_size = len(decrypted_data)
        
        return {
            'encrypted_size': encrypted_size,
            'decrypted_size': decrypted_size,
            'success': True
        }
    
    def save_key(self, filepath: Union[str, Path]):
        """
        Sauvegarde la clé dans un fichier (ATTENTION : à protéger !).
        
        Args:
            filepath: Chemin où sauvegarder la clé
        
        Example:
            >>> crypto = CryptoManager()
            >>> crypto.save_key("secret.key")
        """
        filepath = Path(filepath)
        with open(filepath, 'wb') as f:
            f.write(self.key)
    
    @staticmethod
    def load_key(filepath: Union[str, Path]) -> bytes:
        """
        Charge une clé depuis un fichier.
        
        Args:
            filepath: Chemin du fichier de clé
        
        Returns:
            Clé de chiffrement
        
        Example:
            >>> key = CryptoManager.load_key("secret.key")
            >>> crypto = CryptoManager(key)
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Fichier de clé introuvable : {filepath}")
        
        with open(filepath, 'rb') as f:
            return f.read()
    
    def get_key_string(self) -> str:
        """
        Retourne la clé en string base64 (pour stockage YAML).
        
        Returns:
            Clé en string
        
        Example:
            >>> crypto = CryptoManager()
            >>> key_str = crypto.get_key_string()
            >>> print(key_str)
        """
        return self.key.decode('utf-8')
    
    @staticmethod
    def from_key_string(key_string: str) -> 'CryptoManager':
        """
        Crée un CryptoManager depuis une clé en string.
        
        Args:
            key_string: Clé en string base64
        
        Returns:
            Instance de CryptoManager
        
        Example:
            >>> crypto = CryptoManager.from_key_string("X3k9Lp2mQr8...")
        """
        key_bytes = key_string.encode('utf-8')
        return CryptoManager(key=key_bytes)


def encrypt_data(data: bytes, key: bytes) -> bytes:
    """
    Fonction helper pour chiffrer rapidement des données.
    
    Args:
        data: Données à chiffrer
        key: Clé de chiffrement
    
    Returns:
        Données chiffrées
    """
    crypto = CryptoManager(key)
    return crypto.encrypt_bytes(data)


def decrypt_data(encrypted_data: bytes, key: bytes) -> bytes:
    """
    Fonction helper pour déchiffrer rapidement des données.
    
    Args:
        encrypted_data: Données chiffrées
        key: Clé de chiffrement
    
    Returns:
        Données déchiffrées
    """
    crypto = CryptoManager(key)
    return crypto.decrypt_bytes(encrypted_data)