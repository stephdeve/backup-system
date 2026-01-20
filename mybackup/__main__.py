"""
Point d'entrée principal pour MyBackup CLI
"""

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from pathlib import Path
from typing import Optional
from datetime import datetime
import sys

from .cli import app, _ensure_initialized, _validate_config
from .backup import BackupEngine
from .restore import RestoreEngine
from .utils import format_size
from .database import BackupDatabase

console = Console()


@app.command()
def backup(
    source: Optional[str] = typer.Option(None, "--source", "-s", help="Dossier spécifique à sauvegarder"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulation sans sauvegarder"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Affichage détaillé")
):
    """
     Lance un backup (complet ou incrémental).
    
    Sans --source : sauvegarde toutes les sources configurées
    Avec --source : sauvegarde uniquement ce dossier
    
    Examples:
        mybackup backup
        mybackup backup --source "C:\\Users\\Dev\\Documents"
        mybackup backup --dry-run --verbose
    """
    _ensure_initialized()
    config = _validate_config()
    
    console.print("\n[bold blue] Démarrage du backup...[/bold blue]\n")
    
    if dry_run:
        console.print("[yellow] MODE DRY-RUN (simulation uniquement)[/yellow]\n")
    
    try:
        engine = BackupEngine(config)
        
        if source:
            # Backup d'une source spécifique
            destination = config.get_destination('primary')
            if not destination:
                console.print("[red] Aucune destination configurée[/red]")
                raise typer.Exit(1)
            
            # Trouver la config de la source
            sources = config.get_sources()
            source_config = next((s for s in sources if s['path'] == str(Path(source).absolute())), None)
            
            if source_config:
                exclude = source_config.get('exclude', [])
            else:
                console.print(f"[yellow]  Source non configurée, utilisation sans exclusions[/yellow]")
                exclude = []
            
            if not dry_run:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=console
                ) as progress:
                    task = progress.add_task(f"[cyan]Backup de {source}...", total=None)
                    stats = engine.backup_source(source, destination, exclude)
                    progress.update(task, completed=True)
            else:
                # Dry run - juste scanner
                files = engine.get_files_to_backup(Path(source), exclude)
                stats = {
                    'files_backed_up': len(files),
                    'files_skipped': 0,
                    'files_errors': 0,
                    'total_size_original': sum(f.stat().st_size for f in files),
                    'total_size_encrypted': 0
                }
        else:
            # Backup de toutes les sources
            if not dry_run:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    console=console
                ) as progress:
                    task = progress.add_task("[cyan]Backup de toutes les sources...", total=None)
                    stats = engine.backup_all_sources()
                    progress.update(task, completed=True)
            else:
                console.print("[yellow]Dry-run pour toutes les sources non implémenté[/yellow]")
                raise typer.Exit(0)
        
        # Afficher les résultats
        console.print("\n[bold green] Backup terminé ![/bold green]\n")
        console.print(f"[cyan]Fichiers sauvegardés :[/cyan] {stats['files_backed_up']}")
        console.print(f"[dim]Fichiers ignorés :[/dim] {stats['files_skipped']}")
        
        if stats['files_errors'] > 0:
            console.print(f"[red]Erreurs :[/red] {stats['files_errors']}")
        
        if not dry_run:
            console.print(f"\n[cyan]Taille originale :[/cyan] {format_size(stats['total_size_original'])}")
            console.print(f"[cyan]Taille chiffrée :[/cyan] {format_size(stats['total_size_encrypted'])}")
            
            if stats['total_size_original'] > 0:
                saved = stats['total_size_original'] - stats['total_size_encrypted']
                percentage = (saved / stats['total_size_original']) * 100
                console.print(f"[green]Espace économisé :[/green] {format_size(saved)} ({percentage:.1f}%)")
            
            if 'duration' in stats:
                console.print(f"\n[dim]Durée : {stats['duration']:.2f} secondes[/dim]")
        
        if verbose and stats.get('errors'):
            console.print("\n[red]Erreurs détaillées :[/red]")
            for error in stats['errors'][:10]:  # Limiter à 10 erreurs
                console.print(f"  • {error}")
    
    except Exception as e:
        console.print(f"\n[red] Erreur lors du backup : {e}[/red]")
        if verbose:
            import traceback
            console.print(f"\n[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(1)


@app.command()
def restore(
    file_path: Optional[str] = typer.Option(None, "--file", "-f", help="Fichier spécifique à restaurer"),
    directory: Optional[str] = typer.Option(None, "--directory", "-d", help="Dossier à restaurer"),
    destination: Optional[str] = typer.Option(None, "--destination", help="Où restaurer (emplacement original si omis)"),
    date: Optional[str] = typer.Option(None, "--date", help="Restaurer à cette date (format: YYYY-MM-DD)"),
    version: Optional[int] = typer.Option(None, "--version", "-v", help="Numéro de version spécifique"),
    list_only: bool = typer.Option(False, "--list", "-l", help="Lister les fichiers disponibles seulement")
):
    """
    📥 Restaure des fichiers sauvegardés.
    
    Examples:
        mybackup restore --file "C:\\Users\\Dev\\doc.txt"
        mybackup restore --directory "C:\\Users\\Dev\\Documents" --destination "C:\\Restored"
        mybackup restore --file "C:\\Users\\Dev\\app.py" --date 2026-01-15
        mybackup restore --file "C:\\Users\\Dev\\app.py" --version 3
        mybackup restore --list
    """
    _ensure_initialized()
    config = _validate_config()
    
    try:
        restore_engine = RestoreEngine(config)
        
        # Mode liste
        if list_only:
            console.print("\n[bold blue] Fichiers disponibles pour restauration :[/bold blue]\n")
            files = restore_engine.list_available_files()
            
            if not files:
                console.print("[yellow]Aucun fichier sauvegardé[/yellow]")
                return
            
            for file_info in files[:20]:  # Limiter à 20
                console.print(f"[cyan]{file_info['path']}[/cyan]")
                console.print(f"  Versions : {file_info['total_versions']} | Dernier backup : {file_info['latest_backup']}")
            
            if len(files) > 20:
                console.print(f"\n[dim]... et {len(files) - 20} autres fichiers[/dim]")
            
            return
        
        # Parser la date si fournie
        target_date = None
        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                console.print("[red] Format de date invalide. Utilisez YYYY-MM-DD[/red]")
                raise typer.Exit(1)
        
        # Restaurer un fichier
        if file_path:
            console.print(f"\n[bold blue] Restauration de {file_path}...[/bold blue]\n")
            
            result = restore_engine.restore_file(
                original_path=file_path,
                destination_path=destination,
                version=version,
                target_date=target_date
            )
            
            console.print("[bold green] Fichier restauré avec succès ![/bold green]")
            console.print(f"\n[cyan]Chemin :[/cyan] {result['restored_path']}")
            console.print(f"[cyan]Version :[/cyan] {result['version']}")
            console.print(f"[cyan]Date du backup :[/cyan] {result['timestamp']}")
            console.print(f"[cyan]Taille :[/cyan] {result['size_formatted']}")
        
        # Restaurer un dossier
        elif directory:
            console.print(f"\n[bold blue] Restauration du dossier {directory}...[/bold blue]\n")
            
            if not destination:
                console.print("[red] --destination requis pour restaurer un dossier[/red]")
                raise typer.Exit(1)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("[cyan]Restauration en cours...", total=None)
                stats = restore_engine.restore_directory(
                    source_directory=directory,
                    destination_directory=destination,
                    target_date=target_date
                )
                progress.update(task, completed=True)
            
            console.print("\n[bold green] Dossier restauré ![/bold green]")
            console.print(f"\n[cyan]Fichiers trouvés :[/cyan] {stats['files_found']}")
            console.print(f"[cyan]Fichiers restaurés :[/cyan] {stats['files_restored']}")
            
            if stats['files_failed'] > 0:
                console.print(f"[red]Échecs :[/red] {stats['files_failed']}")
            
            console.print(f"[cyan]Taille totale :[/cyan] {format_size(stats['total_size'])}")
        
        else:
            console.print("[red] Spécifiez --file ou --directory[/red]")
            console.print("Ou utilisez --list pour voir les fichiers disponibles")
            raise typer.Exit(1)
    
    except Exception as e:
        console.print(f"\n[red] Erreur lors de la restauration : {e}[/red]")
        raise typer.Exit(1)


@app.command()
def clean(
    keep_days: int = typer.Option(30, "--keep-days", help="Garder les versions des N derniers jours"),
    keep_versions: int = typer.Option(10, "--keep-versions", help="Garder au moins N versions par fichier"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulation sans supprimer")
):
    """
     Nettoie les anciennes versions selon la politique de rétention.
    
    Examples:
        mybackup clean
        mybackup clean --keep-days 60 --keep-versions 20
        mybackup clean --dry-run
    """
    _ensure_initialized()
    
    db = BackupDatabase()
    
    console.print(f"\n[bold blue] Nettoyage des anciennes versions...[/bold blue]")
    console.print(f"Politique : Garder {keep_days} jours et {keep_versions} versions minimum\n")
    
    if dry_run:
        console.print("[yellow]MODE DRY-RUN (simulation)[/yellow]\n")
        # TODO: Implémenter simulation
        console.print("[dim]Simulation du nettoyage non implémentée[/dim]")
        return
    
    deleted = db.clean_old_versions(keep_days, keep_versions)
    
    console.print(f"[green] {deleted} version(s) supprimée(s)[/green]")


def main():
    """Point d'entrée principal."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]  Opération annulée par l'utilisateur[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red] Erreur inattendue : {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()