#!/usr/bin/env python3
"""
AI Agent Automation Hub - Setup Configuration

This setup.py file configures the AI Agent Automation Hub package for installation
and distribution. It includes all dependencies, entry points, and package metadata.
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_file(filename):
    """Read file contents."""
    filepath = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return ''

# Read version from file
def get_version():
    """Get version from version file or default."""
    version_file = os.path.join(os.path.dirname(__file__), 'VERSION')
    if os.path.exists(version_file):
        with open(version_file, 'r') as f:
            return f.read().strip()
    return '1.0.0'

# Read requirements
def get_requirements():
    """Parse requirements from requirements.txt."""
    requirements_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_file):
        with open(requirements_file, 'r') as f:
            requirements = []
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    # Handle git+https:// and other special cases
                    if line.startswith('git+') or line.startswith('-e'):
                        continue
                    requirements.append(line)
            return requirements
    return []

setup(
    name="ai-agent-automation-hub",
    version=get_version(),
    author="AI Dev Team",
    author_email="team@example.com",
    description="AI Agent Automation Hub with Discord Bot Integration",
    long_description=read_file('README.md'),
    long_description_content_type="text/markdown",
    url="https://github.com/VictorGavo/ai-agent-automation-hub",
    project_urls={
        "Bug Tracker": "https://github.com/VictorGavo/ai-agent-automation-hub/issues",
        "Documentation": "https://github.com/VictorGavo/ai-agent-automation-hub/blob/main/README.md",
        "Source Code": "https://github.com/VictorGavo/ai-agent-automation-hub",
    },
    
    # Package configuration
    packages=find_packages(exclude=["tests*", "docs*", "examples*"]),
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml", "*.json"],
        "dev_bible": ["**/*.md"],
        "database": ["migrations/*.py", "models/*.py"],
    },
    
    # Dependencies
    install_requires=get_requirements(),
    extras_require={
        'dev': [
            'pytest>=7.4.3',
            'pytest-asyncio>=0.21.1',
            'pytest-mock>=3.12.0',
            'pytest-cov>=4.0.0',
            'black>=23.11.0',
            'flake8>=5.0.0',
            'isort>=5.12.0',
            'mypy>=1.7.1',
            'pre-commit>=3.6.0',
        ],
        'monitoring': [
            'prometheus-client>=0.17.0',
            'grafana-api>=1.0.3',
        ],
        'all': [
            'pytest>=7.4.3',
            'pytest-asyncio>=0.21.1',
            'pytest-mock>=3.12.0',
            'pytest-cov>=4.0.0',
            'black>=23.11.0',
            'flake8>=5.0.0',
            'isort>=5.12.0',
            'mypy>=1.7.1',
            'pre-commit>=3.6.0',
            'prometheus-client>=0.17.0',
            'grafana-api>=1.0.3',
        ]
    },
    
    # Entry points for command-line interfaces
    entry_points={
        'console_scripts': [
            'automation-hub-bot=bot.run_bot:main',
            'automation-hub-setup=scripts.init_database:main',
            'automation-hub-health=deploy.health_check:main',
        ],
    },
    
    # Python version requirement
    python_requires='>=3.11',
    
    # Classifiers for PyPI
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications :: Chat",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
        "Framework :: AsyncIO",
        "Framework :: Flask",
    ],
    
    # Keywords for discovery
    keywords=[
        "ai", "automation", "discord", "bot", "agents", "tasks", 
        "orchestration", "backend", "database", "testing", "docker"
    ],
    
    # Zip safety
    zip_safe=False,
)