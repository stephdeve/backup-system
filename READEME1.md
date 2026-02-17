# 🔐 CryptBackup — Sauvegarde Intelligente et Sécurisée

## Présentation
CryptBackup est un système de sauvegarde open-source conçu pour protéger vos données les plus précieuses avec une simplicité déconcertante.  
Il combine chiffrement (AES-256-GCM), compression intelligente (Zstandard) et surveillance en temps réel pour offrir une protection de niveau professionnel tout en restant facile à utiliser.

---

## Table des matières
- [Pourquoi CryptBackup ?](#pourquoi-cryptbackup-)
- [Fonctionnalités clés](#fonctionnalités-clés)
- [Cas d'usage](#cas-dusage)
- [Chiffres](#chiffres)
- [Installation](#installation)
- [Commandes principales](#commandes-principales)
- [Destinations supportées](#destinations-supportées)
- [Sécurité](#sécurité)
- [Contribution & Communauté](#contribution--communauté)
- [Licence](#licence)

---

##  Pourquoi CryptBackup ?
- Sécurité sans compromis : chiffrement avant écriture, clés sécurisées, intégrité vérifiée.
- Économie d'espace : backups incrémentaux et compression Zstandard.
- Facilité d'utilisation : CLI moderne, cross-platform et installation rapide.
- Flexibilité : destinations multiples (dossier local, disque externe, NAS, clé USB).
- Versioning illimité et restauration granulaire.

---

##  Fonctionnalités clés
-  Chiffrement AES-256-GCM (authentifié)
-  Zéro donnée en clair sur le disque
-  Compression Zstandard (gain typique 40–60%)
-  Sauvegarde incrémentale (ne sauvegarde que les changements)
-  Surveillance en temps réel (détection automatique des modifications)
-  Priorisation IA (sauvegarde en priorité des fichiers importants)
-  Versioning illimité (récupération par date/version)
-  Restauration granulaire (fichier, dossier, date, version)
-  Destinations multiples : PC local, clé USB, disque externe, NAS
-  Détection automatique des périphériques (USB débranché, NAS inaccessible)
-  CLI moderne avec Typer et Rich
-  Multi-plateforme : Windows, macOS, Linux (Python 3.10+)
-  Open Source — Licence MIT

---

##  Cas d'usage
- Professionnels : documents, données clients, conformité RGPD  
- Développeurs : code source, configurations, projets critiques  
- Créateurs : photos, vidéos, designs originaux  
- Étudiants : mémoires, recherches, travaux académiques  
- Entreprises : infrastructure de backup décentralisée

---

##  Chiffres
| Composant     | Détail                                 |
|--------------:|----------------------------------------|
| Chiffrement   | AES-256-GCM (authentifié)              |
| Compression   | Zstandard (40–60% économie)            |
| Modules       | 11 modules spécialisés                 |
| Tests         | 15+ tests unitaires                    |
| Plateformes   | Windows 10/11, macOS, Linux            |

---

## Installation
```bash
pip install cryptbackup
cryptbackup init
cryptbackup watch  # C'est lancé !
```

---

##  Commandes principales

### Initialisation
```bash
cryptbackup init
```

### Configuration
```bash
cryptbackup config set destinations.primary "C:\Users\User\Documents"
cryptbackup config set destinations.secondary "E:\Backups"
```

### Sauvegarde
```bash
cryptbackup backup       # Backup immédiat
cryptbackup watch        # Surveillance temps réel
cryptbackup status       # Vérifier le statut
```

### Restauration
```bash
cryptbackup restore --list                                              # Lister les backups
cryptbackup restore --file "document.pdf" --date "2024-01-20"          # Restaurer à une date
cryptbackup restore --file "document.pdf" --destination "C:\Restored"  # Restaurer ailleurs
```

---

##  Destinations supportées

CryptBackup supporte **4 types de destinations** simultanément.  
Vous pouvez configurer jusqu'à 3 destinations (primaire, secondaire, tertiaire) pour une protection maximale selon la règle **3-2-1** *(3 copies, 2 supports différents, 1 hors site)*.

### Types de destinations

| Icône | Type | Exemple |
|-------|------|---------|
| 🖥️ | Dossier local (PC) | `C:\Users\Steve\Backup` |
| 🔌 | Clé USB | `E:\Backup` |
| 💽 | Disque dur externe | `F:\Backup` |
| 🌐 | NAS (réseau) | `\\192.168.1.100\backup` |

### Configuration des destinations

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
# Dossier local sur le PC
cryptbackup config set destinations.primary "/home/user/backup"

# Disque externe monté
cryptbackup config set destinations.secondary "/media/user/disk/backup"

# NAS monté
cryptbackup config set destinations.tertiary "/mnt/nas/backup"
```

### Vérification des destinations

```bash
cryptbackup status
```

**Sortie exemple — tout connecté :**
```
 Destinations :
  🖥️  [primary]   C:\Users\Steve\Backup        Libre : 45.2 GB
  🔌  [secondary] E:\Backup                    Libre : 120.5 GB
  🌐  [tertiary]  \\192.168.1.100\backup       Libre : 1.2 TB
```

**Sortie exemple — USB débranché :**
```
    Destinations :
  🖥️  [primary]   C:\Users\Steve\Backup        Libre : 45.2 GB
  🔌  [secondary] E:\Backup                    Destination non trouvée (périphérique débranché ?)
  🌐  [tertiary]  \\192.168.1.100\backup       Libre : 1.2 TB
```

> **Note :** Si une destination est inaccessible au moment du backup (USB débranché, NAS hors ligne), CryptBackup continue automatiquement vers les destinations disponibles et vous avertit.

---

##  Sécurité garantie
- Chiffrement AES-256-GCM avant chaque écriture sur destination.
- Vérification d'intégrité par hash SHA-256.
- Clé de chiffrement unique et sécurisée : jamais exposée en clair sur le disque.
- Authentification cryptographique pour garantir l'intégrité des sauvegardes.
- Audit trail complet de toutes les opérations (logs horodatés).
- Permissions sécurisées sur Unix : 700 (dossiers) / 600 (fichiers sensibles).

>  **IMPORTANT** : Sauvegardez votre clé de chiffrement (`config.yaml`) sur un support séparé.  
> Sans elle, vos données sont **irrécupérables**.

---

## 🤝 Contribution & Communauté
- Documentation complète disponible dans le dépôt.
- Signaler un bug : ouvrez une issue.
- Proposer une fonctionnalité : ouvrez une issue ou une pull request.
- Contributions bienvenues — suivez le guide de contribution dans le dépôt.

GitHub : [stephdeve/cryptbackup](https://github.com/stephdeve/cryptbackup)
PyPI : [pypi.org/project/cryptbackup](https://pypi.org/project/cryptbackup)

---

## 📜 Licence
MIT License — Libre d'utilisation, modification et distribution.

---

*CryptBackup : votre tranquillité d'esprit en ligne de commande.*