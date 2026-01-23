# restore_all.py - Restaurer tous les fichiers

import sqlite3
from pathlib import Path
from mybackup.restore import RestoreEngine
from mybackup.config import Config
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

console = Console()

def restore_all_files(old_base_path, new_base_path):
    """
    Restaurer tous les fichiers d'un ancien chemin vers un nouveau
    
    Args:
        old_base_path: Ancien chemin (ex: C:/Users/AncienPC/Documents)
        new_base_path: Nouveau chemin (ex: C:/Users/NouveauPC/Documents)
    """
    
    console.print(f"\n[cyan] Restauration complète[/cyan]")
    console.print(f"[dim]De : {old_base_path}[/dim]")
    console.print(f"[dim]Vers : {new_base_path}[/dim]\n")
    
    # Charger config et database
    config = Config()
    db_path = Path.home() / '.mybackup' / 'backups.db'
    
    if not db_path.exists():
        console.print("[red] Base de données non trouvée ![/red]")
        console.print(f"[yellow]Cherché dans : {db_path}[/yellow]")
        return
    
    # Connexion database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Récupérer tous les fichiers commençant par old_base_path
    cursor.execute("""
        SELECT DISTINCT path_original 
        FROM backups 
        WHERE path_original LIKE ?
        ORDER BY path_original
    """, (f"{old_base_path}%",))
    
    files = cursor.fetchall()
    
    if not files:
        console.print(f"[yellow] Aucun fichier trouvé pour {old_base_path}[/yellow]")
        conn.close()
        return
    
    console.print(f"[green] {len(files)} fichier(s) trouvé(s)[/green]\n")
    
    # Restaurer chaque fichier
    restored = 0
    errors = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        
        task = progress.add_task("[cyan]Restauration...", total=len(files))
        
        for (old_path,) in files:
            # Calculer nouveau chemin
            relative_path = old_path.replace(old_base_path, "")
            new_path = new_base_path + relative_path
            
            # Créer dossiers si besoin
            Path(new_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Restaurer
            try:
                # Récupérer dernière version
                cursor.execute("""
                    SELECT path_encrypted, hash_original, size_original
                    FROM backups
                    WHERE path_original = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (old_path,))
                
                result = cursor.fetchone()
                if not result:
                    console.print(f"[yellow]  Pas de backup pour {old_path}[/yellow]")
                    errors += 1
                    progress.update(task, advance=1)
                    continue
                
                encrypted_path, hash_original, size_original = result
                
                # Restaurer le fichier
                engine = RestoreEngine(config)
                engine.restore_file_from_path(encrypted_path, new_path, hash_original)
                
                restored += 1
                
            except Exception as e:
                console.print(f"[red] Erreur : {old_path}[/red]")
                console.print(f"[dim]{e}[/dim]")
                errors += 1
            
            progress.update(task, advance=1)
    
    conn.close()
    
    # Résumé
    console.print(f"\n[bold green] Restauration terminée ![/bold green]")
    console.print(f"[cyan]Fichiers restaurés :[/cyan] {restored}")
    if errors > 0:
        console.print(f"[red]Erreurs :[/red] {errors}")
    console.print(f"\n[dim]Dossier de destination : {new_base_path}[/dim]")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        console.print("[yellow]Usage :[/yellow]")
        console.print("  python restore_all.py <ancien_chemin> <nouveau_chemin>")
        console.print("\n[cyan]Exemple :[/cyan]")
        console.print('  python restore_all.py "C:/Users/AncienPC/Documents" "C:/Users/NouveauPC/Documents"')
        sys.exit(1)
    
    old_path = sys.argv[1]
    new_path = sys.argv[2]
    
    restore_all_files(old_path, new_path)