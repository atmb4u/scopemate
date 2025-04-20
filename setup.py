#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="scopemate",
    version="0.2.0",
    description="🪜 A CLI tool for Purpose/Scope/Outcome planning",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Anoop Thomas Mathew",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "openai>=1.0.0",
        "pydantic>=2.0.0",
    ],
    entry_points={
        'console_scripts': [
            'scopemate=scopemate.cli:main',
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
) 