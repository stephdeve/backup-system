from pathlib import Path
from mybackup.priority import explain_priority

print("=" * 70)
print("ANALYSE DÉTAILLÉE DE PRIORITÉ")
print("=" * 70)

files = [
    "D:/TestBackup/script.py",
    "D:/TestBackup/app.js",
    "D:/TestBackup/rapport.docx",
    "D:/TestBackup/fichier1.txt",
    "D:/TestBackup/vacation.jpg",
    "D:/TestBackup/cache.tmp",
]

results = []

for filepath in files:
    path = Path(filepath)
    if path.exists():
        explanation = explain_priority(path)
        results.append(explanation)

# Trier par score
results.sort(key=lambda x: x['total_score'], reverse=True)

for i, result in enumerate(results, 1):
    print(f"\n{i}. {result['file']}")
    print(f"   Score total: {result['total_score']:.2f}")
    print(f"   ├─ Récence:    {result['breakdown']['recency']:.2f}")
    print(f"   ├─ Taille:     {result['breakdown']['size']:.2f}")
    print(f"   ├─ Extension:  {result['breakdown']['extension']:.2f}")
    print(f"   └─ Fréquence:  {result['breakdown']['frequency']:.2f}")
    print(f"   Extension: {result['details']['extension']}")

print("\n" + "=" * 70)
print("CONCLUSION:")
print("=" * 70)
print(f"Fichier le plus prioritaire: {results[0]['file']}")
print(f"Score: {results[0]['total_score']:.2f}")