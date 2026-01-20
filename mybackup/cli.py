"""
Interface CLI pour MyBackup
Utilise Typer pour une CLI moderne et intuitive
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from .config import Config, create_default_config
from .crypto import CryptoManager
from .database import BackupDatabase
from .utils import format_size, format_timestamp
from . import CONFIG_FILE, CONFIG_DIR

app = typer.Typer(
    name="mybackup",
    help="🔐 Système de backup incrémental intelligent avec chiffrement",
    add_completion=False
)
console = Console()


@app.command()
def init(force: bool = typer.Option(False, "--force", "-f", help="Écraser la config existante")):
    """
    🎯 Initialise MyBackup (première utilisation).
    
    Crée :
    - Fichier de configuration
    - Base de données
    - Clé de chiffrement
    
    Example:
        mybackup init
    """
    if CONFIG_FILE.exists() and not force:
        console.print(f"[yellow]⚠️  Configuration déjà existante : {CONFIG_FILE}[/yellow]")
        console.print("[yellow]Utilisez --force pour écraser[/yellow]")
        raise typer.Exit(1)
    
    console.print("[bold blue]🚀 Initialisation de MyBackup...[/bold blue]")
    
    # Créer le dossier de config
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Générer la clé de chiffrement
    console.print("[dim]Génération de la clé de chiffrement...[/dim]")
    crypto_key = CryptoManager.generate_key().decode('utf-8')
    
    # Créer la config par défaut
    config = create_default_config(crypto_key)
    config.save()
    
    # Initialiser la base de données
    console.print("[dim]Création de la base de données...[/dim]")
    db = BackupDatabase()
    
    console.print(f"\n[bold green]✅ MyBackup initialisé avec succès ![/bold green]")
    console.print(f"\n[dim]Configuration : {CONFIG_FILE}[/dim]")
    console.print(f"[dim]Base de données : {db.db_path}[/dim]")
    console.print(f"\n[yellow]⚠️  IMPORTANT : Sauvegardez votre clé de chiffrement ![/yellow]")
    console.print(f"[yellow]Sans elle, vous ne pourrez PAS restaurer vos backups.[/yellow]")
    console.print(f"\n[bold]Prochaines étapes :[/bold]")
    console.print("  1. Ajoutez des dossiers : [cyan]mybackup add C:\\Users\\...\\Documents[/cyan]")
    console.print("  2. Configurez la destination : [cyan]mybackup config set destination D:\\Backups[/cyan]")
    console.print("  3. Lancez un backup : [cyan]mybackup backup[/cyan]")


@app.command()
def add(
    path: str = typer.Argument(..., help="Chemin du dossier à sauvegarder"),
    exclude: Optional[str] = typer.Option(None, "--exclude", "-e", help="Patterns à exclure (séparés par ,)")
):
    """
    📁 Ajoute un dossier à surveiller.
    
    Example:
        mybackup add "C:\\Users\\Dev\\Documents" --exclude "*.tmp,~*"
        mybackup add "C:\\Users\\Dev\\Projects" -e "node_modules,venv,__pycache__"
    """
    _ensure_initialized()
    
    path_obj = Path(path)
    
    if not path_obj.exists():
        console.print(f"[red]❌ Dossier introuvable : {path}[/red]")
        raise typer.Exit(1)
    
    if not path_obj.is_dir():
        console.print(f"[red]❌ Ce n'est pas un dossier : {path}[/red]")
        raise typer.Exit(1)
    
    config = Config()
    
    # Parser les exclusions
    exclude_list = []
    if exclude:
        exclude_list = [e.strip() for e in exclude.split(',')]
    
    config.add_source(str(path_obj.absolute()), exclude_list)
    config.save()
    
    console.print(f"[green]✅ Dossier ajouté : {path_obj.absolute()}[/green]")
    if exclude_list:
        console.print(f"[dim]Exclusions : {', '.join(exclude_list)}[/dim]")


@app.command()
def remove(path: str = typer.Argument(..., help="Chemin du dossier à retirer")):
    """
    🗑️  Retire un dossier de la surveillance.
    
    Example:
        mybackup remove "C:\\Users\\Dev\\Documents"
    """
    _ensure_initialized()
    
    config = Config()
    
    if config.remove_source(path):
        config.save()
        console.print(f"[green]✅ Dossier retiré : {path}[/green]")
    else:
        console.print(f"[yellow]⚠️  Dossier non trouvé dans la config : {path}[/yellow]")
        raise typer.Exit(1)


@app.command(name="config")
def config_command(
    action: str = typer.Argument(..., help="Action: show, set, get"),
    key: Optional[str] = typer.Argument(None, help="Clé de config (pour set/get)"),
    value: Optional[str] = typer.Argument(None, help="Valeur (pour set)")
):
    """
    ⚙️  Gère la configuration.
    
    Examples:
        mybackup config show
        mybackup config set destination "D:\\Backups"
        mybackup config get compression.level
    """
    _ensure_initialized()
    
    config = Config()
    
    if action == "show":
        console.print("\n[bold]📋 Configuration actuelle :[/bold]\n")
        console.print(str(config))
    
    elif action == "set":
        if not key or value is None:
            console.print("[red]❌ Usage : mybackup config set <clé> <valeur>[/red]")
            raise typer.Exit(1)
        
        config.set(key, value)
        config.save()
        console.print(f"[green]✅ Configuration mise à jour : {key} = {value}[/green]")
    
    elif action == "get":
        if not key:
            console.print("[red]❌ Usage : mybackup config get <clé>[/red]")
            raise typer.Exit(1)
        
        value = config.get(key)
        if value is not None:
            console.print(f"{key} = {value}")
        else:
            console.print(f"[yellow]⚠️  Clé non trouvée : {key}[/yellow]")
    
    else:
        console.print(f"[red]❌ Action inconnue : {action}[/red]")
        console.print("Actions disponibles : show, set, get")
        raise typer.Exit(1)


@app.command()
def status():
    """
    📊 Affiche le statut du système de backup.
    
    Example:
        mybackup status
    """
    _ensure_initialized()
    
    config = Config()
    db = BackupDatabase()
    
    # Récupérer les stats
    stats = db.get_total_stats()
    sources = config.get_sources()
    destination = config.get_destination('primary')
    
    console.print("\n[bold blue]📊 État de MyBackup[/bold blue]\n")
    
    # Table de stats
    table = Table(show_header=False, box=None)
    table.add_column("Métrique", style="cyan")
    table.add_column("Valeur", style="bold")
    
    table.add_row("Fichiers uniques sauvegardés", str(stats['unique_files']))
    table.add_row("Versions totales", str(stats['total_versions']))
    table.add_row("Taille originale", format_size(stats['total_size_original']))
    table.add_row("Taille après chiffrement", format_size(stats['total_size_encrypted']))
    table.add_row("Espace économisé", format_size(stats['space_saved']))
    
    if stats['last_backup']:
        last_backup_dt = datetime.fromisoformat(stats['last_backup'])
        table.add_row("Dernier backup", format_timestamp(last_backup_dt))
    else:
        table.add_row("Dernier backup", "[dim]Aucun backup[/dim]")
    
    console.print(table)
    
    # Sources
    console.print(f"\n[bold]📁 Dossiers surveillés ({len(sources)}) :[/bold]")
    if sources:
        for source in sources:
            console.print(f"  • {source['path']}")
            if source.get('exclude'):
                console.print(f"    [dim]Exclusions : {', '.join(source['exclude'])}[/dim]")
    else:
        console.print("  [dim]Aucun dossier configuré[/dim]")
    
    # Destination
    console.print(f"\n[bold]💾 Destination :[/bold]")
    if destination:
        console.print(f"  • {destination}")
    else:
        console.print("  [yellow]⚠️  Aucune destination configurée[/yellow]")


@app.command(name="list")
def list_versions(
    file_path: str = typer.Argument(..., help="Chemin du fichier dont voir l'historique"),
    limit: int = typer.Option(10, "--limit", "-n", help="Nombre de versions à afficher")
):
    """
    📜 Liste l'historique des versions d'un fichier.
    
    Example:
        mybackup list "C:\\Users\\Dev\\Documents\\rapport.pdf"
        mybackup list "C:\\Users\\Dev\\app.py" --limit 5
    """
    _ensure_initialized()
    
    db = BackupDatabase()
    versions = db.get_all_versions(file_path)
    
    if not versions:
        console.print(f"[yellow]⚠️  Aucun backup trouvé pour : {file_path}[/yellow]")
        return
    
    # Limiter le nombre de résultats
    versions = versions[-limit:]
    
    console.print(f"\n[bold]📜 Historique de : {file_path}[/bold]\n")
    
    table = Table()
    table.add_column("Version", style="cyan")
    table.add_column("Date", style="magenta")
    table.add_column("Taille", style="green")
    table.add_column("Hash", style="dim")
    
    for v in versions:
        timestamp = datetime.fromisoformat(v['timestamp'])
        table.add_row(
            f"v{v['version']}",
            format_timestamp(timestamp),
            format_size(v['size_original']),
            v['hash_original'][:16] + "..."
        )
    
    console.print(table)
    console.print(f"\n[dim]Total : {len(versions)} version(s) affichée(s)[/dim]")


def _ensure_initialized():
    """Vérifie que MyBackup est initialisé."""
    if not CONFIG_FILE.exists():
        console.print("[red] MyBackup n'est pas initialisé.[/red]")
        console.print("[yellow]Lancez d'abord : mybackup init[/yellow]")
        raise typer.Exit(1)


def _validate_config() -> Config:
    """Valide la configuration et retourne l'objet Config."""
    config = Config()
    errors = config.validate()
    
    if errors:
        console.print("[red] Configuration invalide :[/red]")
        for error in errors:
            console.print(f"  • {error}")
        console.print("\n[yellow]Corrigez la configuration avant de continuer.[/yellow]")
        raise typer.Exit(1)
    
    return config


if __name__ == "__main__":
    app()