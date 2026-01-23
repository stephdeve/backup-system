# restore_from_github.ps1
# Restauration MyBackup depuis GitHub

param(
    [string]$GithubRepo = "votre-username/mybackup",  # À personnaliser
    [string]$ConfigUSB = "E:",
    [string]$BackupUSB = "F:"
)

Write-Host "🔄 RESTAURATION MYBACKUP DEPUIS GITHUB" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan

# 1. Vérifier Git
Write-Host "`n📦 Vérification Git..." -ForegroundColor Yellow
git --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Git non installé !" -ForegroundColor Red
    Write-Host "Téléchargez Git : https://git-scm.com/downloads" -ForegroundColor Yellow
    pause
    exit 1
}

# 2. Vérifier Python
Write-Host "`n📦 Vérification Python..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python non installé !" -ForegroundColor Red
    Write-Host "Téléchargez Python 3.10+ : https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "⚠️  IMPORTANT : Cochez 'Add Python to PATH'" -ForegroundColor Yellow
    pause
    exit 1
}

# 3. Créer dossier .mybackup
Write-Host "`n📁 Création dossier configuration..." -ForegroundColor Yellow
$mybackupDir = "$env:USERPROFILE\.mybackup"
New-Item -ItemType Directory -Force -Path $mybackupDir | Out-Null
Write-Host "✅ Dossier créé : $mybackupDir" -ForegroundColor Green

# 4. Copier config.yaml depuis clé USB
Write-Host "`n🔑 Copie clé de chiffrement..." -ForegroundColor Yellow
$configSource = "$ConfigUSB\config.yaml"

if (-not (Test-Path $configSource)) {
    # Chercher avec nom alternatif
    $configSource = "$ConfigUSB\BACKUP_KEY_CRITICAL.yaml"
}

if (Test-Path $configSource) {
    Copy-Item $configSource "$mybackupDir\config.yaml" -Force
    Write-Host "✅ config.yaml copié" -ForegroundColor Green
} else {
    Write-Host "❌ config.yaml non trouvé sur $ConfigUSB" -ForegroundColor Red
    Write-Host "Fichiers cherchés :" -ForegroundColor Yellow
    Write-Host "  - $ConfigUSB\config.yaml" -ForegroundColor White
    Write-Host "  - $ConfigUSB\BACKUP_KEY_CRITICAL.yaml" -ForegroundColor White
    pause
    exit 1
}

# 5. Copier backups.db (si existe)
Write-Host "`n💾 Copie base de données..." -ForegroundColor Yellow
$dbSource = "$ConfigUSB\backups.db"
if (Test-Path $dbSource) {
    Copy-Item $dbSource "$mybackupDir\backups.db" -Force
    Write-Host "✅ backups.db copié" -ForegroundColor Green
} else {
    Write-Host "⚠️  backups.db non trouvé (sera créé si besoin)" -ForegroundColor Yellow
}

# 6. Mettre à jour destination dans config
Write-Host "`n⚙️  Mise à jour destination backups..." -ForegroundColor Yellow
$configPath = "$mybackupDir\config.yaml"
$config = Get-Content $configPath -Raw
$config = $config -replace "destinations:\s*\n\s*primary:.*", "destinations:`n  primary: $BackupUSB\Backups"
$config | Set-Content $configPath
Write-Host "✅ Destination mise à jour : $BackupUSB\Backups" -ForegroundColor Green

# 7. Cloner depuis GitHub
Write-Host "`n📥 Téléchargement code depuis GitHub..." -ForegroundColor Yellow
$installDir = "$env:USERPROFILE\mybackup"

if (Test-Path $installDir) {
    Write-Host "⚠️  Dossier $installDir existe déjà" -ForegroundColor Yellow
    $response = Read-Host "Supprimer et re-télécharger ? (o/n)"
    if ($response -eq "o") {
        Remove-Item $installDir -Recurse -Force
    } else {
        Write-Host "Utilisation du code existant..." -ForegroundColor Cyan
        cd $installDir
    }
}

if (-not (Test-Path $installDir)) {
    git clone "https://github.com/$GithubRepo.git" $installDir
    cd $installDir
}

Write-Host "✅ Code téléchargé" -ForegroundColor Green

# 8. Créer environnement virtuel
Write-Host "`n🐍 Création environnement Python..." -ForegroundColor Yellow
python -m venv venv
Write-Host "✅ Environnement virtuel créé" -ForegroundColor Green

# 9. Activer et installer
Write-Host "`n📦 Installation dépendances..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
pip install -e . --quiet
Write-Host "✅ MyBackup installé" -ForegroundColor Green

# 10. Vérification
Write-Host "`n✅ INSTALLATION TERMINÉE !" -ForegroundColor Green
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

# Test
Write-Host "`n🧪 Test installation..." -ForegroundColor Yellow
mybackup --version

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ MyBackup fonctionne parfaitement !" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  Erreur lors du test" -ForegroundColor Yellow
}

# Instructions
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "PROCHAINES ÉTAPES :" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

Write-Host "`n1️⃣  Voir vos fichiers sauvegardés :" -ForegroundColor Yellow
Write-Host "   mybackup restore --list" -ForegroundColor White

Write-Host "`n2️⃣  Restaurer UN fichier :" -ForegroundColor Yellow
Write-Host '   mybackup restore --file "C:\Users\AncienPC\Documents\rapport.pdf"' -ForegroundColor White

Write-Host "`n3️⃣  Restaurer avec nouveau chemin :" -ForegroundColor Yellow
Write-Host '   mybackup restore --file "C:\Users\AncienPC\doc.pdf" --destination "C:\Users\' + $env:USERNAME + '\doc.pdf"' -ForegroundColor White

Write-Host "`n4️⃣  Voir statut :" -ForegroundColor Yellow
Write-Host "   mybackup status" -ForegroundColor White

Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

Write-Host "`n📂 Localisation :" -ForegroundColor Cyan
Write-Host "   Code : $installDir" -ForegroundColor White
Write-Host "   Config : $mybackupDir" -ForegroundColor White
Write-Host "   Backups : $BackupUSB\Backups" -ForegroundColor White

pause