#!/usr/bin/env python3
"""
Setup script for EnvGuard.

Install in development mode:
    pip install -e .

Install for use:
    pip install .
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read version from main module
version = "1.0.0"

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    long_description = readme_path.read_text(encoding='utf-8')

setup(
    name="envguard",
    version=version,
    author="Forge (Team Brain)",
    author_email="logan@metaphy.io",
    description=".env Configuration Validator & Conflict Detector",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DonkRonk17/EnvGuard",
    py_modules=["envguard"],
    python_requires=">=3.8",
    install_requires=[],  # Zero external dependencies!
    entry_points={
        "console_scripts": [
            "envguard=envguard:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    keywords=[
        "env", "dotenv", "environment", "configuration", "validation",
        "conflict", "detection", "cli", "devops", "automation"
    ],
    project_urls={
        "Bug Reports": "https://github.com/DonkRonk17/EnvGuard/issues",
        "Source": "https://github.com/DonkRonk17/EnvGuard",
        "Documentation": "https://github.com/DonkRonk17/EnvGuard#readme",
    },
)
