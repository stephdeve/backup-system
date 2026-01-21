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
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Affichage détaillé"),
    smart: bool = typer.Option(False, "--smart", help="Priorisation intelligente des fichiers")
):
    """
     Lance un backup (complet ou incrémental).
    
    Sans --source : sauvegarde toutes les sources configurées
    Avec --source : sauvegarde uniquement ce dossier
    Avec --smart : priorise les fichiers importants
    
    Examples:
        mybackup backup
        mybackup backup --source "C:\\Users\\Dev\\Documents"
        mybackup backup --smart
        mybackup backup --dry-run --verbose
    """
    _ensure_initialized()
    config = _validate_config()
    
    console.print("\n[bold blue] Démarrage du backup...[/bold blue]\n")
    
    if dry_run:
        console.print("[yellow] MODE DRY-RUN (simulation uniquement)[/yellow]\n")
    
    if smart:
        console.print("[cyan] Mode intelligent activé - Priorisation des fichiers...[/cyan]\n")
    
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
                # MODE SMART : Prioriser les fichiers
                if smart:
                    from .priority import PriorityQueue
                    
                    # Obtenir tous les fichiers
                    all_files = engine.get_files_to_backup(Path(source), exclude)
                    
                    # Créer file de priorité
                    priority_queue = PriorityQueue()
                    priority_queue.add_multiple(all_files)
                    
                    # Obtenir fichiers triés
                    sorted_files = priority_queue.get_sorted(reverse=True)
                    
                    console.print(f"[cyan] {len(sorted_files)} fichiers analysés et triés[/cyan]\n")
                    
                    if verbose:
                        # Afficher top 10
                        console.print("[cyan] Top 10 fichiers prioritaires :[/cyan]")
                        for i, (score, filepath) in enumerate(sorted_files[:10], 1):
                            console.print(f"  {i}. {filepath.name} (score: {score:.1f})")
                        console.print()
                    
                    # Backup dans l'ordre de priorité
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        BarColumn(),
                        TaskProgressColumn(),
                        console=console
                    ) as progress:
                        task = progress.add_task(
                            f"[cyan]Backup intelligent de {source}...", 
                            total=len(sorted_files)
                        )
                        
                        stats = {
                            'files_backed_up': 0,
                            'files_skipped': 0,
                            'files_errors': 0,
                            'total_size_original': 0,
                            'total_size_encrypted': 0,
                            'errors': []
                        }
                        
                        # Backup chaque fichier dans l'ordre de priorité
                        for score, file_path in sorted_files:
                            try:
                                result = engine.backup_file(file_path, Path(destination))
                                
                                if result['backed_up']:
                                    stats['files_backed_up'] += 1
                                    stats['total_size_original'] += result['size_original']
                                    stats['total_size_encrypted'] += result['size_encrypted']
                                else:
                                    stats['files_skipped'] += 1
                                
                                progress.update(task, advance=1)
                                
                            except Exception as e:
                                stats['files_errors'] += 1
                                stats['errors'].append(f"{file_path}: {e}")
                                progress.update(task, advance=1)
                        
                        progress.update(task, completed=len(sorted_files))
                
                else:
                    # MODE NORMAL : Sans priorisation
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
                
                if smart:
                    from .priority import PriorityQueue, explain_priority
                    
                    priority_queue = PriorityQueue()
                    priority_queue.add_multiple(files)
                    sorted_files = priority_queue.get_sorted(reverse=True)
                    
                    console.print(f"[cyan] {len(sorted_files)} fichiers analysés[/cyan]\n")
                    console.print("[cyan] Top 20 fichiers prioritaires :[/cyan]\n")
                    
                    for i, (score, filepath) in enumerate(sorted_files[:20], 1):
                        console.print(f"  {i}. {filepath.name:40} | Score: {score:6.1f}")
                    
                    console.print(f"\n[dim]... et {len(sorted_files) - 20} autres fichiers[/dim]")
                
                stats = {
                    'files_backed_up': len(files),
                    'files_skipped': 0,
                    'files_errors': 0,
                    'total_size_original': sum(f.stat().st_size for f in files),
                    'total_size_encrypted': 0
                }
        else:
            # Backup de toutes les sources
            if smart:
                console.print("[yellow]  Mode smart non disponible pour backup complet[/yellow]")
                console.print("[yellow]Utilisez --source pour activer la priorisation[/yellow]\n")
            
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
    

@app.command()
def watch(
    daemon: bool = typer.Option(False, "--daemon", "-d", help="Lancer en arrière-plan")
    ):
    """
    👁️  Lance la surveillance automatique des fichiers.
    
    Détecte les changements en temps réel et effectue des backups automatiques
    toutes les N minutes (configuré dans watch.interval).
    
    Examples:
        mybackup watch
        mybackup watch --daemon
    """
    _ensure_initialized()
    config = _validate_config()
    
    from .watcher import WatcherDaemon
    
    try:
        daemon_watcher = WatcherDaemon(config)
        daemon_watcher.start()
    except KeyboardInterrupt:
        console.print("\n[yellow]Arrêt de la surveillance...[/yellow]")
    except Exception as e:
        console.print(f"\n[red] Erreur : {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    main()