# 🔐 MyBackup - Système de Backup Incrémental Intelligent

<div align="center">

**Sauvegarde automatique avec chiffrement AES-256, compression Zstandard et détection temps réel**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-blue.svg)](https://www.microsoft.com/windows)

</div>

---

## 🎯 Fonctionnalités

✅ **Backup Incrémental** - Sauvegarde uniquement les fichiers modifiés  
🔐 **Chiffrement AES-256-GCM** - Sécurité militaire pour vos données  
🗜️ **Compression Zstandard** - Économise 40-60% d'espace disque  
👁️ **Surveillance Temps Réel** - Détection automatique des changements  
📊 **Multi-destinations** - Disque externe, NAS, partition, clé USB  
🕐 **Versioning Multiple** - Historique complet de tous vos fichiers  
💻 **Interface CLI Moderne** - Interface colorée et intuitive  
🔍 **Restauration Granulaire** - Par fichier, dossier ou date  

---

## 📋 Prérequis

- **Python 3.10+** (vous utilisez Python 3.10)
- **Windows 10/11**
- **Support de backup** : Disque dur externe, NAS, partition séparée, ou clé USB

---

## 🚀 Installation Rapide

### Étape 1 : Télécharger le Projet

Si vous avez Git :
```bash
git clone https://github.com/stephdeve/backup-system.git
cd backup-system
```

Sinon, téléchargez et extrayez le dossier ZIP.

### Étape 2 : Créer un Environnement Virtuel

```powershell
# Ouvrez PowerShell dans le dossier backup-system

# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement (PowerShell)
.\venv\Scripts\Activate.ps1

# Ou pour CMD
.\venv\Scripts\activate.bat

# Vérifier que l'environnement est activé (vous devriez voir (venv) dans le prompt)
```

### Étape 3 : Installer les Dépendances

```bash
# Mettre à jour pip
python -m pip install --upgrade pip

# Installer les dépendances
pip install -r requirements.txt

# Installer MyBackup en mode développement
pip install -e .
```

### Étape 4 : Initialiser MyBackup

```bash
mybackup init
```

Ceci va créer :
- Fichier de configuration : `%USERPROFILE%\.mybackup\config.yaml`
- Base de données : `%USERPROFILE%\.mybackup\backups.db`
- Clé de chiffrement unique

⚠️ **IMPORTANT** : Sauvegardez votre clé de chiffrement ! Sans elle, vous ne pourrez JAMAIS restaurer vos backups.

---

## 📖 Guide d'Utilisation

### Configuration Initiale

**1. Ajouter des dossiers à sauvegarder :**

```bash
# Ajouter vos documents
mybackup add "C:\Users\VotreNom\Documents" --exclude "*.tmp,~*,desktop.ini"

# Ajouter vos projets de code
mybackup add "C:\Users\VotreNom\Projects" --exclude "node_modules,venv,__pycache__,.git"

# Ajouter vos photos
mybackup add "C:\Users\VotreNom\Pictures"
```

**2. Configurer la destination du backup :**

```bash
# Disque externe
mybackup config set destination "D:\Backups"

# Ou partition
mybackup config set destination "E:\MesBackups"

# Ou NAS (réseau)
mybackup config set destination "\\192.168.1.100\backups"

# Ou clé USB
mybackup config set destination "F:\Backups"
```

**3. Vérifier la configuration :**

```bash
mybackup config show
```

### Lancer un Backup

**Backup de toutes les sources :**

```bash
mybackup backup
```

**Backup d'un dossier spécifique :**

```bash
mybackup backup --source "C:\Users\VotreNom\Documents"
```

**Simulation (dry-run) :**

```bash
mybackup backup --dry-run --verbose
```

### Voir le Statut

```bash
mybackup status
```

Affiche :
- Nombre de fichiers sauvegardés
- Espace utilisé vs économisé
- Dernier backup
- Liste des sources

### Voir l'Historique d'un Fichier

```bash
mybackup list "C:\Users\VotreNom\Documents\rapport.pdf"
```

Affiche toutes les versions sauvegardées avec :
- Numéro de version
- Date
- Taille
- Hash

### Restaurer des Fichiers

**Restaurer la dernière version d'un fichier :**

```bash
mybackup restore --file "C:\Users\VotreNom\Documents\important.docx"
```

**Restaurer à une date spécifique :**

```bash
mybackup restore --file "C:\Users\VotreNom\Documents\rapport.pdf" --date 2026-01-15
```

**Restaurer une version précise :**

```bash
mybackup restore --file "C:\Users\VotreNom\app.py" --version 3
```

**Restaurer vers un autre emplacement :**

```bash
mybackup restore --file "C:\Users\VotreNom\doc.txt" --destination "C:\Restored\doc.txt"
```

**Restaurer tout un dossier :**

```bash
mybackup restore --directory "C:\Users\VotreNom\Documents" --destination "C:\Restored"
```

**Lister tous les fichiers disponibles :**

```bash
mybackup restore --list
```

### Nettoyer les Anciennes Versions

```bash
# Garder 30 jours et 10 versions minimum par fichier
mybackup clean --keep-days 30 --keep-versions 10

# Simulation
mybackup clean --dry-run
```

---

## 🔧 Configuration Avancée

Le fichier de configuration se trouve dans : `%USERPROFILE%\.mybackup\config.yaml`

### Structure de la Configuration

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
  
  - path: C:\Users\VotreNom\Projects
    exclude: ['node_modules', 'venv', '__pycache__', '.git']
    added_at: '2026-01-20T14:36:00'

destinations:
  primary: D:\Backups
  secondary: null

watch:
  enabled: true
  interval: 300  # secondes (5 minutes)
  realtime: true

retention:
  keep_days: 30
  keep_versions: 10
  auto_clean: false

priority:
  enabled: false
  model: simple

notifications:
  enabled: false
  on_error: true
  on_success: false
```

### Modifier la Configuration

**Via CLI :**

```bash
# Changer le niveau de compression
mybackup config set compression.level 5

# Activer le nettoyage automatique
mybackup config set retention.auto_clean true

# Changer l'intervalle de surveillance
mybackup config set watch.interval 600
```

**Ou éditer directement** : `%USERPROFILE%\.mybackup\config.yaml`

---

## 📊 Comprendre le Système

### Comment Fonctionne le Backup Incrémental ?

**Premier backup (complet) :**
```
📁 Documents/ (10 fichiers, 50 MB)
    └─> Backup complet : 50 MB chiffrés
```

**Deuxième backup (incrémental) :**
```
📁 Documents/ (10 fichiers, 1 modifié)
    └─> Backup seulement : 1 fichier (5 MB)
    └─> Gain : 90% d'espace et de temps
```

### Processus de Sauvegarde

Pour chaque fichier :

1. **Calcul du hash SHA-256** → Détecte si le fichier a changé
2. **Compression Zstandard** → Réduit la taille de 40-60%
3. **Chiffrement AES-256-GCM** → Sécurise les données
4. **Stockage** → Fichier `.enc` dans destination
5. **Métadonnées** → Enregistrement dans base SQLite

### Structure du Backup

**Sur votre destination :**
```
D:\Backups\
├── a3f5c892e1b4...enc  (version 1 de app.py)
├── d9g3h456f2c8...enc  (version 2 de app.py)
├── b2d4e567a9f1...enc  (data.json)
└── c8f1a234d5e9...enc  (logo.png)
```

**Dans la base de données :**
```
backups.db contient :
- Chemin original de chaque fichier
- Numéro de version
- Hash original et chiffré
- Tailles (original, compressé, chiffré)
- Timestamp
- Ratio de compression
```

---

## 🔒 Sécurité

### Chiffrement

- **Algorithme** : AES-256-GCM (standard militaire)
- **Mode** : Galois/Counter Mode (authentifié)
- **Bibliothèque** : Cryptography.io (certifiée FIPS)

### Clé de Chiffrement

⚠️ **CRITIQUE** : Votre clé est stockée dans `config.yaml`

**Sauvegardez-la** :
```bash
# Copier sur clé USB sécurisée
copy %USERPROFILE%\.mybackup\config.yaml F:\backup_key.yaml

# Ou imprimer et mettre dans un coffre
notepad %USERPROFILE%\.mybackup\config.yaml
```

**Sans la clé** :
- ❌ Impossible de déchiffrer les backups
- ❌ Toutes vos données sont perdues définitivement
- ❌ Même vous ne pouvez pas récupérer les fichiers

### Intégrité

Chaque fichier est vérifié par :
- Hash SHA-256 avant chiffrement
- Hash SHA-256 après chiffrement
- Vérification lors de la restauration

Si un fichier est corrompu, la restauration échoue immédiatement.

---

## 🎓 Exemples d'Utilisation Réels

### Scénario 1 : Développeur

```bash
# Configuration
mybackup init
mybackup add "C:\Users\Dev\Projects" --exclude "node_modules,venv,.git,__pycache__"
mybackup config set destination "D:\DevBackups"

# Backup quotidien
mybackup backup

# Oh non ! Bug introduit hier...
mybackup list "C:\Users\Dev\Projects\app.py"
mybackup restore --file "C:\Users\Dev\Projects\app.py" --date 2026-01-19
```

### Scénario 2 : Étudiant

```bash
# Sauvegarder documents et mémoire
mybackup add "C:\Users\Etudiant\Documents"
mybackup add "C:\Users\Etudiant\Memoire"
mybackup config set destination "E:\BackupUSB"

# Backup avant chaque session
mybackup backup

# PC crash ! Restaurer sur nouveau PC
mybackup restore --directory "C:\Users\Etudiant\Memoire" --destination "C:\Restored"
```

### Scénario 3 : Freelance

```bash
# Multiples destinations
mybackup config set destination "D:\Backup"
# TODO: Ajouter destination secondaire NAS

# Backup projets clients
mybackup add "C:\Users\Freelance\ClientA"
mybackup add "C:\Users\Freelance\ClientB"

# Backup automatique toutes les 5 min
# (watchdog - à implémenter au Sprint 2)
```

---

## 🐛 Troubleshooting

### Erreur : "MyBackup n'est pas initialisé"

```bash
mybackup init
```

### Erreur : "Destination manquante"

```bash
mybackup config set destination "D:\Backups"
```

### Erreur : "Clé de chiffrement invalide"

Votre fichier `config.yaml` est corrompu. Si vous avez une sauvegarde de la clé :
```bash
# Restaurer depuis backup
copy F:\backup_key.yaml %USERPROFILE%\.mybackup\config.yaml
```

Sinon, vos backups chiffrés sont perdus.

### Le backup est lent

1. **Augmenter le niveau de compression** (plus rapide mais moins efficace) :
```bash
mybackup config set compression.level 1
```

2. **Désactiver la compression** (non recommandé) :
```bash
mybackup config set compression.enabled false
```

3. **Exclure plus de fichiers** :
```bash
mybackup remove "C:\Users\...\path"
mybackup add "C:\Users\...\path" --exclude "*.log,*.tmp,*.cache"
```

### Erreur "Permission denied"

- Exécutez PowerShell en administrateur
- Vérifiez que la destination est accessible
- Vérifiez les permissions NTFS

---

## 📈 Roadmap - Prochaines Features

### Sprint 2 (Semaine 2) - ✅ Planifié
- [ ] Daemon de surveillance en arrière-plan
- [ ] Backup automatique toutes les 5 minutes
- [ ] Notifications sur erreurs
- [ ] Commande `mybackup watch`

### Sprint 3 (Semaine 3) - 🎯 Futur
- [ ] Priorisation intelligente (IA)
- [ ] Dashboard web (FastAPI)
- [ ] Statistiques graphiques
- [ ] Export de rapports

### Sprint 4 (Semaine 4+) - 💡 Idées
- [ ] Support multi-plateformes (Linux, macOS)
- [ ] Intégration cloud (chiffré)
- [ ] Application mobile de monitoring
- [ ] IPFS pour décentralisation

---

## 🤝 Contribution

Ce projet est un projet personnel d'apprentissage, mais les suggestions sont bienvenues !

---

## 📄 Licence

MIT License - Libre d'utilisation

---

## 👨‍💻 Auteur

**StephDev** - Développeur à Cotonou, Bénin  
Projet réalisé dans le cadre d'un apprentissage Python avancé

---

## 🙏 Remerciements

- Cryptography.io pour le chiffrement robuste
- Zstandard pour la compression efficace
- Typer & Rich pour la CLI moderne
- Watchdog pour la surveillance de fichiers

---

## ⚡ Quick Start (Résumé)

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

**C'est tout ! Vos données sont maintenant protégées. 🎉**#   b a c k u p - s y s t e m  
 