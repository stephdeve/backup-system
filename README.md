# 🔐 CryptBackup — Système de backup incrémental intelligent

<div align="center">

**Sauvegarde automatique avec chiffrement AES-256, compression Zstandard et détection en temps réel**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Cross-platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-brightgreen.svg)](https://github.com/stephdeve/cryptbackup)
[![PyPI](https://img.shields.io/pypi/v/cryptbackup)](https://pypi.org/project/cryptbackup/)
[![Downloads](https://img.shields.io/pypi/dm/cryptbackup)](https://pypi.org/project/cryptbackup/)

</div>

---

## Table des matières
- [Fonctionnalités](#-fonctionnalités)
- [Prérequis](#-prérequis)
- [Installation rapide](#-installation-rapide)
- [Initialisation](#-initialisation)
- [Utilisation](#-utilisation)
  - [Configurer les sources et destinations](#configurer-les-sources-et-destinations)
  - [Lancer un backup](#lancer-un-backup)
  - [Statut et historique](#statut-et-historique)
  - [Restaurations](#restaurations)
  - [Nettoyage (rétention)](#nettoyage-rétention)
- [Destinations supportées](#-destinations-supportées)
- [Configuration avancée](#-configuration-avancée)
- [Comment ça marche](#-comment-ça-marche)
- [Sécurité](#-sécurité)
- [Dépannage](#-dépannage)
- [Roadmap](#-roadmap)
- [Contribution](#-contribution)
- [Licence et auteur](#-licence-et-auteur)
- [Remerciements](#-remerciements)

---

##  Fonctionnalités

- Backup incrémental : sauvegarde uniquement les fichiers modifiés depuis la dernière version
- Chiffrement : AES-256-GCM (authentifié)
- Compression : Zstandard (zstd)
- Surveillance en temps réel (watch) / intervalle configurable
- Destinations multiples : PC local, disque externe, NAS, clé USB — jusqu'à 3 destinations simultanées
- Détection automatique des périphériques (USB débranché, NAS hors ligne)
- Versioning : historique par fichier (versions datées)
- CLI moderne (Typer + Rich) avec options dry-run et verbose
- Restauration granulaire : par fichier, dossier, date ou version

---

##  Prérequis

- Python 3.10+
- Systèmes supportés : Windows 10/11, macOS (Intel/Apple Silicon) et distributions Linux modernes
- Destination de backup : dossier local, disque externe, NAS, clé USB, etc.

---

##  Installation rapide

### Option A — Via PyPI (recommandé)
```bash
pip install cryptbackup
cryptbackup init
```

### Option B — Depuis le code source (développement)

1. Cloner le dépôt :
```bash
git clone https://github.com/stephdeve/backup-system.git
cd backup-system
```

2. Créer et activer un environnement virtuel :

- Windows PowerShell :
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
- Windows CMD :
```bat
python -m venv venv
.\venv\Scripts\activate.bat
```
- macOS / Linux :
```bash
python -m venv venv
source venv/bin/activate
```

3. Installer les dépendances :
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

---

##  Initialisation

Initialiser CryptBackup (crée configuration, base de données et clé de chiffrement) :
```bash
cryptbackup init
```

Ceci crée automatiquement selon votre OS :
- Windows : `%USERPROFILE%\.mybackup\config.yaml` et `%USERPROFILE%\.mybackup\backups.db`
- macOS / Linux : `~/.mybackup/config.yaml` et `~/.mybackup/backups.db`

>  **IMPORTANT** : Sauvegardez immédiatement votre `config.yaml` sur un support externe.
> Sans votre clé de chiffrement, la restauration est **impossible**.

---

##  Utilisation

### Configurer les sources et destinations

Ajouter des dossiers à sauvegarder :
```bash
# Windows
cryptbackup add "C:\Users\VotreNom\Documents" --exclude "*.tmp,~*,desktop.ini"

# macOS / Linux
cryptbackup add "/home/votreuser/Documents" --exclude "*.tmp,~*,.DS_Store"
```

Configurer les destinations (voir section complète [Destinations supportées](#-destinations-supportées)) :
```bash
# Destination principale (dossier local)
cryptbackup config set destinations.primary "C:\Users\VotreNom\Backup"

# Destination secondaire (clé USB ou disque externe)
cryptbackup config set destinations.secondary "E:\Backup"

# Destination tertiaire (NAS réseau)
cryptbackup config set destinations.tertiary "\\192.168.1.100\backup"
```

Afficher la configuration :
```bash
cryptbackup config show
```

### Lancer un backup

Backup de toutes les sources :
```bash
cryptbackup backup
```

Backup d'une source particulière :
```bash
# Windows
cryptbackup backup --source "C:\Users\VotreNom\Documents"

# macOS / Linux
cryptbackup backup --source "/home/votreuser/Documents"
```

Backup intelligent (priorisation des fichiers importants) :
```bash
cryptbackup backup --smart
```

Simulation (dry-run) :
```bash
cryptbackup backup --dry-run --verbose
```

### Statut et historique

Afficher le statut :
```bash
cryptbackup status
```

Affiche : fichiers sauvegardés, espace utilisé / économisé, dernier backup, sources et **état de toutes les destinations**.

Lister les versions d'un fichier :
```bash
# Windows
cryptbackup list "C:\Users\VotreNom\Documents\rapport.pdf"

# macOS / Linux
cryptbackup list "/home/votreuser/Documents/rapport.pdf"
```

### Restaurations

Restaurer la dernière version d'un fichier :
```bash
# Windows
cryptbackup restore --file "C:\Users\VotreNom\Documents\important.docx"

# macOS / Linux
cryptbackup restore --file "/home/votreuser/Documents/important.docx"
```

Restaurer à une date spécifique :
```bash
cryptbackup restore --file "C:\Users\VotreNom\Documents\rapport.pdf" --date 2026-01-15
```

Restaurer une version précise :
```bash
cryptbackup restore --file "C:\Users\VotreNom\app.py" --version 3
```

Restaurer vers un autre emplacement :
```bash
# Windows
cryptbackup restore --file "C:\Users\VotreNom\doc.txt" --destination "C:\Restored\doc.txt"

# macOS / Linux
cryptbackup restore --file "/home/votreuser/doc.txt" --destination "/home/votreuser/Restored/doc.txt"
```

Restaurer tout un dossier :
```bash
# Windows
cryptbackup restore --directory "C:\Users\VotreNom\Documents" --destination "C:\Restored"

# macOS / Linux
cryptbackup restore --directory "/home/votreuser/Documents" --destination "/home/votreuser/Restored"
```

Lister tous les fichiers disponibles pour restauration :
```bash
cryptbackup restore --list
```

### Nettoyage / Rétention

```bash
# Conserver 30 jours et 10 versions par fichier
cryptbackup clean --keep-days 30 --keep-versions 10

# Simulation avant suppression
cryptbackup clean --dry-run
```

---

##  Destinations supportées

CryptBackup supporte **4 types de destinations** simultanément.
Configurez jusqu'à 3 destinations pour une protection maximale selon la règle **3-2-1** :
*3 copies, 2 supports différents, 1 hors site.*

### Types de destinations

| Icône | Type | Exemple Windows | Exemple Linux/macOS |
|-------|------|-----------------|---------------------|
| 🖥️ | Dossier local (PC) | `C:\Users\Steve\Backup` | `/home/user/backup` |
| 🔌 | Clé USB | `E:\Backup` | `/media/user/usb/backup` |
| 💽 | Disque dur externe | `F:\Backup` | `/media/user/disk/backup` |
| 🌐 | NAS (réseau) | `\\192.168.1.100\backup` | `/mnt/nas/backup` |

### Configuration complète

#### Windows
```bash
# Dossier local sur le PC
cryptbackup config set destinations.primary "C:\Users\Steve\Backup"

# Clé USB ou disque externe
cryptbackup config set destinations.secondary "E:\Backup"

# NAS sur le réseau local
cryptbackup config set destinations.tertiary "\\192.168.1.100\backup"
```

#### Linux / macOS
```bash
# Dossier local
cryptbackup config set destinations.primary "/home/user/backup"

# Disque externe monté
cryptbackup config set destinations.secondary "/media/user/disk/backup"

# NAS monté
cryptbackup config set destinations.tertiary "/mnt/nas/backup"
```

### Vérification de l'état des destinations

```bash
cryptbackup status
```

**Toutes les destinations connectées :**
```
 Destinations :
  🖥️  [primary]   C:\Users\Steve\Backup        Libre : 45.2 GB
  🔌  [secondary] E:\Backup                    Libre : 120.5 GB
  🌐  [tertiary]  \\192.168.1.100\backup       Libre : 1.2 TB
```

**USB débranché — CryptBackup continue sur les autres :**
```
 Destinations :
  🖥️  [primary]   C:\Users\Steve\Backup        Libre : 45.2 GB
  🔌  [secondary] E:\Backup                    Destination non trouvée (périphérique débranché ?)
  🌐  [tertiary]  \\192.168.1.100\backup       Libre : 1.2 TB
```

> **Note :** Si une destination est inaccessible (USB débranché, NAS hors ligne), CryptBackup continue automatiquement vers les destinations disponibles et vous en informe.

---

## 🔧 Configuration avancée

Fichier de configuration :
- Windows : `%USERPROFILE%\.mybackup\config.yaml`
- macOS / Linux : `~/.mybackup/config.yaml`

Exemple de structure complète :
```yaml
version: '1.0.1'
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
  primary: C:\Users\VotreNom\Backup     # Dossier local
  secondary: E:\Backup                  # Clé USB / disque externe
  tertiary: \\192.168.1.100\backup      # NAS

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
cryptbackup config set compression.level 5
cryptbackup config set retention.auto_clean true
cryptbackup config set watch.interval 600
```

---

##  Comment ça marche (aperçu technique)

Pour chaque fichier modifié :
1. Calcul du hash SHA-256 (détecte les modifications)
2. Compression Zstandard (zstd)
3. Chiffrement AES-256-GCM (Cryptography.io)
4. Stockage du binaire chiffré (`.enc`) sur chaque destination accessible
5. Enregistrement des métadonnées dans SQLite (hash, taille, timestamp, version)

Structure sur destination :
```
D:\Backups\
├── a3f5c892e1b4...enc   (version 1 de app.py)
├── d9g3h456f2c8...enc   (version 2 de app.py)
└── ...
```

La base de données contient : chemin original, version, hash, tailles (original / compressé / chiffré), timestamps, ratio de compression.

---

## 🔒 Sécurité

- Algorithme : AES-256-GCM (authentifié)
- Bibliothèque : cryptography (best-effort FIPS-aware usage)
- Intégrité : vérification SHA-256 avant et après chiffrement — corruption détectée à la restauration
- Permissions Unix : 700 (dossiers) / 600 (fichiers sensibles)
- Clé stockée dans `config.yaml` — **à sauvegarder hors-site impérativement**

Sauvegarde de la clé :
```powershell
# Windows
copy $env:USERPROFILE\.mybackup\config.yaml F:\backup_key.yaml
```
```bash
# macOS / Linux
cp ~/.mybackup/config.yaml /mnt/secure/backup_key.yaml
```

>  Sans la clé : restauration **impossible**. Conservez plusieurs copies (clé USB, cloud chiffré, coffre physique).

---

##  Dépannage

| Erreur | Solution |
|--------|----------|
| "CryptBackup n'est pas initialisé" | Exécuter `cryptbackup init` |
| "Destination manquante" | `cryptbackup config set destinations.primary "D:\Backups"` |
| "Clé de chiffrement invalide" | Restaurer votre `config.yaml` depuis votre copie de sauvegarde |
| Backup lent | Diminuer la compression (`level 1`) ou exclure plus de fichiers |
| Permission denied | Vérifier permissions NTFS (Windows) ou POSIX (Linux/macOS) |
| USB non détecté | Vérifier que le périphérique est monté, relancer `cryptbackup status` |
| NAS inaccessible | Vérifier la connexion réseau, les identifiants et le montage |

---

##  Roadmap

### Terminé 
- Backup incrémental avec chiffrement AES-256-GCM
- Compression Zstandard
- CLI moderne (Typer + Rich)
- Surveillance temps réel (watchdog)
- Priorisation intelligente des fichiers
- Destinations multiples (local, USB, disque externe, NAS)
- Détection automatique des périphériques

### En cours 
- Dashboard web (FastAPI + interface graphique)
- Daemon de surveillance en arrière-plan (service système)

### Futur 
- Support cloud chiffré (Backblaze B2, AWS S3)
- Application mobile (monitoring)
- Multi-utilisateurs (entreprises)
- API REST

---

## 🤝 Contribution

Suggestions et contributions bienvenues. Ouvrez une issue ou une pull request sur GitHub.

GitHub : [stephdeve/cryptbackup](https://github.com/stephdeve/cryptbackup)
PyPI : [pypi.org/project/cryptbackup](https://pypi.org/project/cryptbackup)

---

##  Licence

MIT License — utilisation libre, modification et distribution autorisées.

---

##  Auteur

**StephDev** — Développeur (Cotonou, Bénin). Projet réalisé dans le cadre d'un apprentissage Python avancé.

---

##  Remerciements

- [cryptography.io](https://cryptography.io/) — Chiffrement AES-256
- [Zstandard](https://python-zstandard.readthedocs.io/) — Compression
- [Typer](https://typer.tiangolo.com/) — CLI moderne
- [Rich](https://rich.readthedocs.io/) — Interface terminal
- [Watchdog](https://python-watchdog.readthedocs.io/) — Surveillance fichiers

---

## ⚡ Quick Start (résumé)

```bash
# 1. Installer
pip install cryptbackup

# 2. Initialiser
cryptbackup init

# 3. Ajouter une source
cryptbackup add "C:\Users\VotreNom\Documents"   # Windows
cryptbackup add "/home/votreuser/Documents"       # Linux/macOS

# 4. Configurer les destinations
cryptbackup config set destinations.primary "C:\Users\VotreNom\Backup"   # Local
cryptbackup config set destinations.secondary "E:\Backup"                 # USB / Externe
cryptbackup config set destinations.tertiary "\\192.168.1.100\backup"    # NAS

# 5. Lancer un backup
cryptbackup backup

# 6. Vérifier l'état
cryptbackup status

# 7. Restaurer un fichier
cryptbackup restore --file "C:\Users\VotreNom\Documents\fichier.txt"
```

**Vos données sont maintenant protégées. 🎉**