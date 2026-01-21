"""
Système de priorisation intelligente pour les backups
Utilise des scores basés sur des heuristiques et optionnellement du ML
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import time

from .utils import get_file_info


class FilePriority:
    """
    Calcule la priorité d'un fichier pour le backup.
    Plus le score est ÉLEVÉ, plus le fichier est prioritaire.
    """
    
    # Poids des facteurs
    WEIGHT_RECENCY = 10.0       # Fichiers récents = importants
    WEIGHT_SIZE = 0.001          # Gros fichiers = plus de données
    WEIGHT_EXTENSION = 50.0      # Certains types = critiques
    WEIGHT_FREQUENCY = 20.0      # Souvent modifié = important
    
    # Extensions critiques (code, documents)
    CRITICAL_EXTENSIONS = {
        # Code
        '.py', '.js', '.java', '.cpp', '.c', '.h', '.cs', '.go', '.rs',
        '.php', '.rb', '.swift', '.kt', '.ts', '.jsx', '.tsx', '.dart',
        
        # Documents
        '.docx', '.xlsx', '.pptx', '.pdf', '.odt', '.ods', '.odp',
        
        # Config
        '.json', '.yaml', '.yml', '.toml', '.xml', '.ini', '.cfg',
        
        # Base de données
        '.db', '.sqlite', '.sql',
    }
    
    # Extensions importantes (mais moins)
    IMPORTANT_EXTENSIONS = {
        '.txt', '.md', '.csv', '.log', '.html', '.css', '.svg',
    }
    
    # Extensions basse priorité (media, cache)
    LOW_PRIORITY_EXTENSIONS = {
        '.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mp3', '.avi',
        '.mov', '.zip', '.tar', '.gz', '.tmp', '.cache',
    }
    
    def __init__(self, history: Optional[Dict] = None):
        """
        Initialise le calculateur de priorité.
        
        Args:
            history: Historique des modifications (optionnel)
        """
        self.history = history or {}
    
    def calculate_score(self, file_path: Path) -> float:
        """
        Calcule le score de priorité d'un fichier.
        
        Args:
            file_path: Chemin du fichier
        
        Returns:
            Score de priorité (plus élevé = plus prioritaire)
        
        Example:
            >>> priority = FilePriority()
            >>> score = priority.calculate_score(Path("projet/app.py"))
            >>> print(score)  # Ex: 75.5
        """
        if not file_path.exists():
            return 0.0
        
        score = 0.0
        
        # Facteur 1 : Récence (dernière modification)
        score += self._score_recency(file_path)
        
        # Facteur 2 : Taille
        score += self._score_size(file_path)
        
        # Facteur 3 : Type de fichier (extension)
        score += self._score_extension(file_path)
        
        # Facteur 4 : Fréquence de modification
        score += self._score_frequency(file_path)
        
        return score
    
    def _score_recency(self, file_path: Path) -> float:
        """Score basé sur la date de dernière modification."""
        try:
            info = get_file_info(file_path)
            modified = info['modified']
            
            # Calcul : nombre de jours depuis modification
            days_ago = (datetime.now() - modified).days
            
            # Plus c'est récent, plus le score est élevé
            # 0 jours = score max, décroit avec le temps
            if days_ago == 0:
                return self.WEIGHT_RECENCY * 10  # Aujourd'hui = très important
            elif days_ago <= 7:
                return self.WEIGHT_RECENCY * 5   # Cette semaine
            elif days_ago <= 30:
                return self.WEIGHT_RECENCY * 2   # Ce mois
            else:
                return self.WEIGHT_RECENCY / (days_ago / 30)  # Décroit
        except:
            return 0.0
    
    def _score_size(self, file_path: Path) -> float:
        """Score basé sur la taille du fichier."""
        try:
            info = get_file_info(file_path)
            size_kb = info['size'] / 1024
            
            # Bonus pour fichiers entre 1 KB et 10 MB
            if 1 <= size_kb <= 10240:  # 1 KB - 10 MB
                return size_kb * self.WEIGHT_SIZE
            elif size_kb < 1:
                return 0.1  # Très petits fichiers = peu important
            else:
                return 10.0  # Gros fichiers = score fixe
        except:
            return 0.0
    
    def _score_extension(self, file_path: Path) -> float:
        """Score basé sur le type de fichier."""
        ext = file_path.suffix.lower()
        
        if ext in self.CRITICAL_EXTENSIONS:
            return self.WEIGHT_EXTENSION * 2
        elif ext in self.IMPORTANT_EXTENSIONS:
            return self.WEIGHT_EXTENSION
        elif ext in self.LOW_PRIORITY_EXTENSIONS:
            return self.WEIGHT_EXTENSION * 0.1
        else:
            return self.WEIGHT_EXTENSION * 0.5  # Inconnu = moyenne
    
    def _score_frequency(self, file_path: Path) -> float:
        """Score basé sur la fréquence de modification."""
        path_str = str(file_path)
        
        if path_str in self.history:
            modifications = self.history[path_str]
            # Plus modifié = plus important
            return min(modifications * self.WEIGHT_FREQUENCY, 100.0)
        
        return 0.0
    
    def update_history(self, file_path: Path):
        """Met à jour l'historique de modifications."""
        path_str = str(file_path)
        self.history[path_str] = self.history.get(path_str, 0) + 1


class PriorityQueue:
    """
    File de priorité pour trier les fichiers à sauvegarder.
    """
    
    def __init__(self, priority_calculator: Optional[FilePriority] = None):
        """
        Initialise la file de priorité.
        
        Args:
            priority_calculator: Calculateur de priorité personnalisé
        """
        self.calculator = priority_calculator or FilePriority()
        self.items: List[Tuple[float, Path]] = []
    
    def add(self, file_path: Path):
        """Ajoute un fichier à la file."""
        score = self.calculator.calculate_score(file_path)
        self.items.append((score, file_path))
    
    def add_multiple(self, file_paths: List[Path]):
        """Ajoute plusieurs fichiers."""
        for path in file_paths:
            self.add(path)
    
    def get_sorted(self, reverse: bool = True) -> List[Tuple[float, Path]]:
        """
        Retourne les fichiers triés par priorité.
        
        Args:
            reverse: True = plus prioritaire en premier
        
        Returns:
            Liste de tuples (score, path)
        """
        return sorted(self.items, key=lambda x: x[0], reverse=reverse)
    
    def get_top(self, n: int) -> List[Path]:
        """
        Retourne les N fichiers les plus prioritaires.
        
        Args:
            n: Nombre de fichiers à retourner
        
        Returns:
            Liste des chemins de fichiers
        """
        sorted_items = self.get_sorted(reverse=True)
        return [path for score, path in sorted_items[:n]]
    
    def clear(self):
        """Vide la file."""
        self.items.clear()


def prioritize_files(file_paths: List[Path], 
                     top_n: Optional[int] = None) -> List[Path]:
    """
    Fonction helper pour prioriser rapidement des fichiers.
    
    Args:
        file_paths: Liste de fichiers
        top_n: Nombre de fichiers à retourner (None = tous)
    
    Returns:
        Liste de fichiers triés par priorité
    
    Example:
        >>> files = [Path("a.txt"), Path("code.py"), Path("image.jpg")]
        >>> prioritized = prioritize_files(files, top_n=2)
        >>> # Retourne : [Path("code.py"), Path("a.txt")]
    """
    queue = PriorityQueue()
    queue.add_multiple(file_paths)
    
    if top_n:
        return queue.get_top(top_n)
    else:
        sorted_items = queue.get_sorted(reverse=True)
        return [path for score, path in sorted_items]


def explain_priority(file_path: Path) -> Dict[str, any]:
    """
    Explique pourquoi un fichier a un certain score.
    Utile pour debugging et compréhension.
    
    Args:
        file_path: Fichier à analyser
    
    Returns:
        Dictionnaire avec détails du score
    
    Example:
        >>> explanation = explain_priority(Path("projet/app.py"))
        >>> print(explanation)
        {
            'total_score': 125.5,
            'recency_score': 100.0,
            'size_score': 0.5,
            'extension_score': 100.0,
            'frequency_score': 0.0,
            'details': {...}
        }
    """
    calculator = FilePriority()
    
    total = calculator.calculate_score(file_path)
    recency = calculator._score_recency(file_path)
    size = calculator._score_size(file_path)
    extension = calculator._score_extension(file_path)
    frequency = calculator._score_frequency(file_path)
    
    return {
        'file': str(file_path),
        'total_score': total,
        'breakdown': {
            'recency': recency,
            'size': size,
            'extension': extension,
            'frequency': frequency
        },
        'details': {
            'extension': file_path.suffix,
            'size': file_path.stat().st_size if file_path.exists() else 0,
            'modified': datetime.fromtimestamp(file_path.stat().st_mtime) if file_path.exists() else None
        }
    }