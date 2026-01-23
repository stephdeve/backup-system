# 🔐 MyBackup — Sauvegarde Intelligente et Sécurisée

## Présentation
MyBackup est un système de sauvegarde open-source conçu pour protéger vos données les plus précieuses avec une simplicité déconcertante.  
Il combine chiffrement (AES-256-GCM), compression intelligente (Zstandard) et surveillance en temps réel pour offrir une protection de niveau professionnel tout en restant facile à utiliser.

---

## Table des matières
- [Pourquoi MyBackup ?](#pourquoi-mybackup-)
- [Fonctionnalités clés](#fonctionnalités-clés)
- [Cas d'usage](#cas-dusage)
- [Chiffres](#chiffres)
- [Installation](#installation)
- [Commandes principales](#commandes-principales)
- [Sécurité](#sécurité)
- [Contribution & Communauté](#contribution--communauté)
- [Licence](#licence)

---

## 🎯 Pourquoi MyBackup ?
- Sécurité sans compromis : chiffrement avant écriture, clés sécurisées, intégrité vérifiée.
- Économie d’espace : backups incrémentaux et compression Zstandard.
- Facilité d’utilisation : CLI moderne, cross-platform et installation rapide.
- Flexibilité : destinations multiples (disque externe, NAS, clé USB, cloud chiffré).
- Versioning illimité et restauration granulaire.

---

## ✨ Fonctionnalités clés
- ✅ Chiffrement AES-256-GCM (authentifié)
- ✅ Zéro donnée en clair sur le disque
- ✅ Compression Zstandard (gain typique 40–60%)
- ✅ Sauvegarde incrémentale (ne sauvegarde que les changements)
- ✅ Surveillance en temps réel (détection automatique des modifications)
- ✅ Priorisation IA (sauvegarde en priorité des fichiers importants)
- ✅ Versioning illimité (récupération par date/version)
- ✅ Restauration granulaire (fichier, dossier, date, version)
- ✅ CLI moderne avec Typer et Rich
- ✅ Multi-plateforme : Windows, macOS, Linux (Python 3.10+)
- ✅ Open Source — Licence MIT

---

## 🚀 Cas d'usage
- Professionnels : documents, données clients, conformité RGPD  
- Développeurs : code source, configurations, projets critiques  
- Créateurs : photos, vidéos, designs originaux  
- Étudiants : mémoires, recherches, travaux académiques  
- Entreprises : infrastructure de backup décentralisée

---

## 📊 Chiffres
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
pip install mybackup
mybackup init
mybackup watch  # C'est lancé !
```

---

## 🔗 Commandes principales

### Initialisation
```bash
mybackup init
```

### Configuration
```bash
mybackup config set source "C:\Users\User\Documents"
mybackup config set destination "E:\Backups"
```

### Sauvegarde
```bash
mybackup backup       # Backup immédiat
mybackup watch        # Surveillance temps réel
mybackup status       # Vérifier le statut
```

### Restauration
```bash
mybackup restore --list                       # Lister les backups
mybackup restore --file "document.pdf" --date "2024-01-20"  # Restaurer un fichier à une date donnée
```

---

## 🛡️ Sécurité garantie
- Chiffrement AES-256-GCM avant chaque écriture sur destination.
- Vérification d'intégrité par hash SHA-256.
- Clé de chiffrement unique et sécurisée : jamais exposée en clair sur le disque.
- Authentification cryptographique pour garantir l'intégrité des sauvegardes.
- Audit trail complet de toutes les opérations (logs horodatés).

---

## 🤝 Contribution & Communauté
- Documentation complète disponible dans le dépôt.
- Signaler un bug : ouvrez une issue.
- Proposer une fonctionnalité : ouvrez une issue ou une pull request.
- Contributions bienvenues — suivez le guide de contribution dans le dépôt.

GitHub : [stephdeve/backup-system](https://github.com/stephdeve/backup-system)

---

## 📜 Licence
MIT License — Libre d'utilisation, modification et distribution.

---

MyBackup : votre tranquillité d'esprit en ligne de commande.
