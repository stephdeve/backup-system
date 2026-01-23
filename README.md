# 🔐 MyBackup — Système de backup incrémental intelligent

<div align="center">

**Sauvegarde automatique avec chiffrement AES-256, compression Zstandard et détection en temps réel**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)  
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)  
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-blue.svg)](https://www.microsoft.com/windows)

</div>

---

Table des matières
- [Fonctionnalités](#-fonctionnalités)
- [Prérequis](#-prérequis)
- [Installation rapide](#-installation-rapide)
- [Initialisation](#-initialisation)
- [Utilisation](#-utilisation)
  - [Configurer les sources et destinations](#configurer-les-sources-et-destinations)
  - [Lancer un backup](#lancer-un-backup)
  - [Statut et historique](#statut-et-historique)
  - [Restaurations](#restaurations)
  - [Nettoyage (retention)](#nettoyage-retention)
- [Configuration avancée](#-configuration-avancée)
- [Comment ça marche](#-comment-ça-marche)
- [Sécurité](#-sécurité)
- [Dépannage](#-dépannage)
- [Roadmap](#-roadmap)
- [Contribution](#-contribution)
- [Licence et auteur](#-licence-et-auteur)
- [Remerciements](#-remerciements)

---

## 🎯 Fonctionnalités

- Backup incrémental : sauvegarde uniquement les fichiers modifiés depuis la dernière version  
- Chiffrement : AES-256-GCM (authentifié)  
- Compression : Zstandard (zstd)  
- Surveillance en temps réel (watch) / intervalle configurable  
- Destinations multiples : disque externe, NAS, partition, clé USB  
- Versioning : historique par fichier (versions datées)  
- CLI moderne (Typer + Rich) avec options dry-run et verbose  
- Restauration granulaire : par fichier, dossier, date ou version

---

## 📋 Prérequis

- Python 3.10+  
- Système ciblé : Windows 10/11 (actuellement orienté Windows)  
- Destination de backup : disque externe, NAS, partition séparée, clé USB, etc.

---

## 🚀 Installation rapide

1. Cloner le dépôt :
```bash
git clone https://github.com/stephdeve/backup-system.git
cd backup-system
```

2. Créer et activer un environnement virtuel (PowerShell) :
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
(Si vous utilisez CMD : `.\venv\Scripts\activate.bat`)

3. Installer les dépendances et le package en mode dev :
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

---

## ⚙️ Initialisation

Initialiser MyBackup (crée configuration, DB et clé de chiffrement) :
```bash
mybackup init
```

Ceci crée :
- `%USERPROFILE%\.mybackup\config.yaml` (config + clé de chiffrement)
- `%USERPROFILE%\.mybackup\backups.db` (base SQLite)
- Un emplacement de stockage sur la ou les destinations configurées

Important : sauvegardez votre clé de chiffrement ! Sans elle, la restauration est impossible.

---

## 📖 Utilisation

### Configurer les sources et destinations

Ajouter des dossiers à sauvegarder :
```bash
mybackup add "C:\Users\VotreNom\Documents" --exclude "*.tmp,~*,desktop.ini"
mybackup add "C:\Users\VotreNom\Projects" --exclude "node_modules,venv,__pycache__,.git"
mybackup add "C:\Users\VotreNom\Pictures"
```

Configurer la destination :
```bash
# Disque externe
mybackup config set destination "D:\Backups"

# NAS
mybackup config set destination "\\192.168.1.100\backups"
```

Afficher la configuration :
```bash
mybackup config show
```

### Lancer un backup

Backup de toutes les sources :
```bash
mybackup backup
```

Backup d'une source particulière :
```bash
mybackup backup --source "C:\Users\VotreNom\Documents"
```

Simulation (dry-run) :
```bash
mybackup backup --dry-run --verbose
```

### Statut et historique

Afficher le statut :
```bash
mybackup status
```
Affiche : nombre de fichiers sauvegardés, espace utilisé / économisé, dernier backup, sources.

Lister les versions d'un fichier :
```bash
mybackup list "C:\Users\VotreNom\Documents\rapport.pdf"
```

### Restaurations

Restaurer la dernière version d'un fichier :
```bash
mybackup restore --file "C:\Users\VotreNom\Documents\important.docx"
```

Restaurer à une date spécifique :
```bash
mybackup restore --file "C:\Users\VotreNom\Documents\rapport.pdf" --date 2026-01-15
```

Restaurer une version précise :
```bash
mybackup restore --file "C:\Users\VotreNom\app.py" --version 3
```

Restaurer vers un autre emplacement :
```bash
mybackup restore --file "C:\Users\VotreNom\doc.txt" --destination "C:\Restored\doc.txt"
```

Restaurer tout un dossier :
```bash
mybackup restore --directory "C:\Users\VotreNom\Documents" --destination "C:\Restored"
```

Lister tous les fichiers disponibles pour restauration :
```bash
mybackup restore --list
```

### Nettoyage / Rétention

Conserver N jours et un nombre de versions par fichier :
```bash
mybackup clean --keep-days 30 --keep-versions 10
# Simulation
mybackup clean --dry-run
```

---

## 🔧 Configuration avancée

Fichier de configuration : `%USERPROFILE%\.mybackup\config.yaml`

Exemple structure :
```yaml
version: '1.0.0'
created_at: '2026-01-20T14:30:00'

encryption:
  algorithm: AES-256-GCM
  key: 'VOTRE_CLE_SECRETE_ICI'

compression:
  enabled: true
  algorithm: zstd
  level: 3  # 1 (rapide) à 22 (max compression)

sources:
  - path: C:\Users\VotreNom\Documents
    exclude: ['*.tmp', '~*', 'desktop.ini']
    added_at: '2026-01-20T14:35:00'

destinations:
  primary: D:\Backups
  secondary: null

watch:
  enabled: true
  interval: 300  # secondes
  realtime: true

retention:
  keep_days: 30
  keep_versions: 10
  auto_clean: false
```

Modifier via CLI :
```bash
mybackup config set compression.level 5
mybackup config set retention.auto_clean true
mybackup config set watch.interval 600
```

Ou éditer directement `%USERPROFILE%\.mybackup\config.yaml`.

---

## 📊 Comment ça marche (aperçu technique)

Pour chaque fichier :
1. Calcul du hash SHA-256 (détecte modifications)  
2. Compression Zstandard (zstd)  
3. Chiffrement AES-256-GCM (Cryptography.io)  
4. Stockage du binaire chiffré (.enc) sur la destination  
5. Enregistrement des métadonnées dans la base SQLite (hash, taille, timestamp, version)

Structure sur destination (exemple) :
```
D:\Backups\
├── a3f5c892e1b4...enc  (version 1 de app.py)
├── d9g3h456f2c8...enc  (version 2 de app.py)
└── ...
```

La DB contient : chemin original, version, hash, tailles (original/compressé/chiffré), timestamps, ratio de compression.

---

## 🔒 Sécurité

- Algorithme : AES-256-GCM (authentifié)  
- Bibliothèque : cryptography (best-effort FIPS-aware usage)  
- Clé : stockée dans `config.yaml` par défaut — sauvegardez-la hors-site !

Sauvegarde de la clé (exemples Windows) :
```powershell
copy %USERPROFILE%\.mybackup\config.yaml F:\backup_key.yaml
```

Sans la clé : restauration impossible. Conservez plusieurs copies sécurisées.

Intégrité : vérification SHA-256 avant et après chiffrement ; corruption détectée à la restauration.

---

## 🐛 Dépannage rapide

- "MyBackup n'est pas initialisé" → exécuter `mybackup init`  
- "Destination manquante" → `mybackup config set destination "D:\Backups"`  
- "Clé de chiffrement invalide" → restaurer votre `config.yaml` depuis votre copie de sauvegarde
- Backup lent : diminuer la compression (niveau 1), désactiver la compression ou exclure plus de fichiers  
- Permission denied : exécuter PowerShell en administrateur et vérifier permissions NTFS

---

## 📈 Roadmap

Sprint 2 (prévu)
- Daemon de surveillance en arrière-plan
- Backup automatique toutes les 5 minutes
- Notifications d'erreur
- Commande `mybackup watch`

Futurs
- Priorisation intelligente (IA)
- Dashboard web (FastAPI)
- Support multi-plateformes (Linux, macOS)
- Intégration cloud chiffrée

---

## 🤝 Contribution

Ce projet est un projet personnel d'apprentissage — suggestions et contributions bienvenues. Ouvrez une issue ou une PR avec des propositions concrètes.

---

## 📄 Licence

MIT License — utilisation libre.

---

## 👨‍💻 Auteur

**StephDev** — Développeur (Cotonou, Bénin). Projet réalisé dans le cadre d'un apprentissage Python avancé.

---

## 🙏 Remerciements

- cryptography.io  
- Zstandard (zstd)  
- Typer & Rich  
- Watchdog

---

## ⚡ Quick Start (résumé)

```bash
# 1. Installer
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .

# 2. Initialiser
mybackup init

# 3. Configurer
mybackup add "C:\Users\VotreNom\Documents"
mybackup config set destination "D:\Backups"

# 4. Backup
mybackup backup

# 5. Restaurer
mybackup restore --file "C:\Users\...\fichier.txt"
```

**Vos données sont maintenant protégées. 🎉**
