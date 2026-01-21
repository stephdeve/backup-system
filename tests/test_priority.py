from pathlib import Path
from mybackup.priority import explain_priority, prioritize_files

# Tester avec vos fichiers
files = [
    Path("D:/TestBackup/fichier1.txt"),
    Path("D:/TestBackup/document.txt"),
    Path("D:/TestBackup/photos/photo1.jpg"),
]

print("=" * 50)
print("ANALYSE DE PRIORITÉ")
print("=" * 50)

for file in files:
    if file.exists():
        explanation = explain_priority(file)
        print(f"\nFichier: {file.name}")
        print(f"Score total: {explanation['total_score']:.2f}")
        print(f"  - Récence: {explanation['breakdown']['recency']:.2f}")
        print(f"  - Taille: {explanation['breakdown']['size']:.2f}")
        print(f"  - Extension: {explanation['breakdown']['extension']:.2f}")

print("\n" + "=" * 50)
print("ORDRE DE PRIORITÉ")
print("=" * 50)

prioritized = prioritize_files(files)
for i, file in enumerate(prioritized, 1):
    print(f"{i}. {file.name}")