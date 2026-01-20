"""
MyBackup - Système de Backup Incrémental Intelligent
Installation Package
"""

from setuptools import setup, find_packages
from pathlib import Path

# Lire le README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Lire les requirements
requirements = []
with open("requirements.txt", "r", encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if line and not line.startswith("#"):
            requirements.append(line)

setup(
    name="mybackup",
    version="1.0.0",
    author="StephDev",
    author_email="dev@example.com",
    description="Système de backup incrémental avec chiffrement, compression et IA",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/stephdev/mybackup",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: System :: Archiving :: Backup",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "mybackup=mybackup.__main__:main",
        ],
    },
    include_package_data=True,
)