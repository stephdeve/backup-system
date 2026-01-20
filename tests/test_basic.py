"""
Tests basiques pour MyBackup
À exécuter avec: pytest tests/test_basic.py
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from mybackup.crypto import CryptoManager
from mybackup.config import Config, create_default_config
from mybackup.database import BackupDatabase
from mybackup.utils import calculate_file_hash, format_size, is_excluded
from mybackup.backup import BackupEngine
from mybackup.restore import RestoreEngine


class TestCrypto:
    """Tests pour le module de chiffrement."""
    
    def test_generate_key(self):
        """Test génération de clé."""
        key = CryptoManager.generate_key()
        assert len(key) == 44  # Clé Fernet en base64
        assert isinstance(key, bytes)
    
    def test_encrypt_decrypt_bytes(self):
        """Test chiffrement/déchiffrement de données."""
        crypto = CryptoManager()
        original_data = b"Ceci est un test secret"
        
        # Chiffrer
        encrypted = crypto.encrypt_bytes(original_data)
        assert encrypted != original_data
        assert len(encrypted) > len(original_data)
        
        # Déchiffrer
        decrypted = crypto.decrypt_bytes(encrypted)
        assert decrypted == original_data
    
    def test_encrypt_decrypt_file(self):
        """Test chiffrement/déchiffrement de fichiers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Créer fichier de test
            test_file = tmpdir / "test.txt"
            test_content = "Contenu de test très secret !"
            test_file.write_text(test_content, encoding='utf-8')
            
            # Chiffrer
            crypto = CryptoManager()
            encrypted_file = tmpdir / "test.txt.enc"
            stats = crypto.encrypt_file(test_file, encrypted_file)
            
            assert encrypted_file.exists()
            assert stats['encrypted_size'] > 0
            
            # Déchiffrer
            decrypted_file = tmpdir / "test_decrypted.txt"
            crypto.decrypt_file(encrypted_file, decrypted_file)
            
            assert decrypted_file.read_text(encoding='utf-8') == test_content
    
    def test_key_string_conversion(self):
        """Test conversion clé bytes <-> string."""
        crypto = CryptoManager()
        key_string = crypto.get_key_string()
        
        # Recréer depuis string
        crypto2 = CryptoManager.from_key_string(key_string)
        
        # Vérifier compatibilité
        data = b"test"
        encrypted = crypto.encrypt_bytes(data)
        decrypted = crypto2.decrypt_bytes(encrypted)
        
        assert decrypted == data


class TestUtils:
    """Tests pour les utilitaires."""
    
    def test_calculate_file_hash(self):
        """Test calcul de hash."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test content")
            filepath = f.name
        
        try:
            hash1 = calculate_file_hash(filepath)
            assert len(hash1) == 64  # SHA-256 en hex
            
            # Hash identique pour même contenu
            hash2 = calculate_file_hash(filepath)
            assert hash1 == hash2
        finally:
            Path(filepath).unlink()
    
    def test_format_size(self):
        """Test formatage de tailles."""
        assert "1.00 KB" in format_size(1024)
        assert "1.00 MB" in format_size(1024 * 1024)
        assert "1.00 GB" in format_size(1024 * 1024 * 1024)
    
    def test_is_excluded(self):
        """Test patterns d'exclusion."""
        assert is_excluded("projet/node_modules/lib.js", ["node_modules"])
        assert is_excluded("fichier.tmp", ["*.tmp"])
        assert not is_excluded("fichier.py", ["*.tmp"])


class TestConfig:
    """Tests pour la configuration."""
    
    def test_create_default_config(self):
        """Test création config par défaut."""
        key = CryptoManager.generate_key().decode('utf-8')
        config = create_default_config(key)
        
        assert config.get_encryption_key() == key
        assert config.is_compression_enabled() == True
        assert config.get_compression_level() == 3
    
    def test_add_remove_source(self):
        """Test ajout/retrait de sources."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config()
            
            # Ajouter
            config.add_source(tmpdir, exclude=["*.tmp"])
            sources = config.get_sources()
            assert len(sources) == 1
            assert sources[0]['path'] == str(Path(tmpdir).resolve())
            
            # Retirer
            removed = config.remove_source(tmpdir)
            assert removed == True
            assert len(config.get_sources()) == 0
    
    def test_set_get_values(self):
        """Test set/get de valeurs."""
        config = Config()
        
        config.set('compression.level', 5)
        assert config.get('compression.level') == 5
        
        config.set('watch.enabled', False)
        assert config.is_watch_enabled() == False


class TestDatabase:
    """Tests pour la base de données."""
    
    def test_add_backup(self):
        """Test ajout d'un backup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = BackupDatabase(db_path)
            
            backup_id = db.add_backup(
                path_original="C:/test/file.txt",
                path_encrypted="D:/backup/abc123.enc",
                hash_original="abc123",
                hash_encrypted="xyz789",
                size_original=1000,
                size_encrypted=800
            )
            
            assert backup_id > 0
    
    def test_versioning(self):
        """Test versioning automatique."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = BackupDatabase(db_path)
            
            path = "C:/test/file.txt"
            
            # Premier backup
            assert db.get_next_version(path) == 1
            db.add_backup(path, "backup1.enc", "hash1", "ehash1", 100, 80)
            
            # Deuxième backup
            assert db.get_next_version(path) == 2
            db.add_backup(path, "backup2.enc", "hash2", "ehash2", 100, 80)
            
            # Vérifier
            versions = db.get_all_versions(path)
            assert len(versions) == 2
            assert versions[0]['version'] == 1
            assert versions[1]['version'] == 2
    
    def test_has_file_changed(self):
        """Test détection de changements."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = BackupDatabase(db_path)
            
            path = "C:/test/file.txt"
            hash1 = "abc123"
            hash2 = "def456"
            
            # Pas de backup → considéré comme changé
            assert db.has_file_changed(path, hash1) == True
            
            # Ajouter backup
            db.add_backup(path, "backup.enc", hash1, "ehash", 100, 80)
            
            # Même hash → pas changé
            assert db.has_file_changed(path, hash1) == False
            
            # Hash différent → changé
            assert db.has_file_changed(path, hash2) == True


class TestBackupRestore:
    """Tests d'intégration backup/restore."""
    
    def test_full_backup_restore_cycle(self):
        """Test cycle complet : backup puis restore."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Setup
            source_dir = tmpdir / "source"
            backup_dir = tmpdir / "backup"
            restore_dir = tmpdir / "restored"
            
            source_dir.mkdir()
            backup_dir.mkdir()
            restore_dir.mkdir()
            
            # Créer fichier de test
            test_file = source_dir / "document.txt"
            test_content = "Contenu important à sauvegarder !"
            test_file.write_text(test_content, encoding='utf-8')
            
            # Config
            config = Config()
            key = CryptoManager.generate_key().decode('utf-8')
            config.set_encryption_key(key)
            config.add_source(str(source_dir))
            config.set_destination(str(backup_dir))
            
            db_path = tmpdir / "test.db"
            db = BackupDatabase(db_path)
            
            # BACKUP
            engine = BackupEngine(config, db)
            result = engine.backup_file(test_file, backup_dir)
            
            assert result['backed_up'] == True
            assert result['size_original'] > 0
            
            # Vérifier fichier chiffré existe
            encrypted_files = list(backup_dir.glob("*.enc"))
            assert len(encrypted_files) == 1
            
            # RESTORE
            restore_engine = RestoreEngine(config, db)
            restored_file = restore_dir / "document.txt"
            
            restore_result = restore_engine.restore_file(
                original_path=str(test_file),
                destination_path=str(restored_file)
            )
            
            assert restore_result['success'] == True
            
            # Vérifier contenu
            restored_content = restored_file.read_text(encoding='utf-8')
            assert restored_content == test_content
    
    def test_incremental_backup(self):
        """Test backup incrémental."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            source_dir = tmpdir / "source"
            backup_dir = tmpdir / "backup"
            source_dir.mkdir()
            backup_dir.mkdir()
            
            test_file = source_dir / "data.txt"
            test_file.write_text("Version 1", encoding='utf-8')
            
            # Config
            config = Config()
            key = CryptoManager.generate_key().decode('utf-8')
            config.set_encryption_key(key)
            
            db_path = tmpdir / "test.db"
            db = BackupDatabase(db_path)
            
            engine = BackupEngine(config, db)
            
            # Premier backup
            result1 = engine.backup_file(test_file, backup_dir)
            assert result1['backed_up'] == True
            
            # Même fichier → skip
            result2 = engine.backup_file(test_file, backup_dir)
            assert result2['backed_up'] == False
            assert result2['reason'] == 'unchanged'
            
            # Modifier fichier
            test_file.write_text("Version 2 modifiée", encoding='utf-8')
            
            # Nouveau backup
            result3 = engine.backup_file(test_file, backup_dir)
            assert result3['backed_up'] == True
            
            # Vérifier 2 versions
            versions = db.get_all_versions(str(test_file))
            assert len(versions) == 2


def test_installation():
    """Test que toutes les dépendances sont installées."""
    import cryptography
    import watchdog
    import zstandard
    import typer
    import rich
    import yaml
    
    assert True  # Si on arrive ici, tout est installé


if __name__ == "__main__":
    pytest.main([__file__, "-v"])