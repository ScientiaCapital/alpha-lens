#!/usr/bin/env python
from setuptools import setup, find_packages
import sys

long_description = ''

if 'upload' in sys.argv or 'sdist' in sys.argv:
    try:
        with open('README.md', encoding='utf-8') as f:
            long_description = f.read()
    except FileNotFoundError:
        long_description = 'AI-powered multi-asset alpha factor analysis platform'

# Core dependencies for basic alpha factor analysis
install_reqs = [
    'matplotlib>=3.3.0',
    'numpy>=1.19.0',
    'pandas>=1.1.0',
    'scipy>=1.5.0',
    'seaborn>=0.11.0',
    'statsmodels>=0.12.0',
    'IPython>=7.16.0',
]

# Optional AI agents and advanced features
agents_reqs = [
    'anthropic>=0.18.0',
    'langchain>=0.1.0',
    'langgraph>=0.0.20',
    'psycopg2-binary>=2.9.0',
    'redis>=5.0.0',
    'streamlit>=1.28.0',
    'alpaca-py>=0.8.0',
]

extra_reqs = {
    'test': [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "flake8>=6.0.0",
    ],
    'agents': agents_reqs,
    'all': agents_reqs,
}

if __name__ == "__main__":
    setup(
        name='alpha-lens',
        version='1.0.0',
        description='AI-powered multi-asset alpha factor analysis platform with autonomous trading agents',
        long_description=long_description,
        long_description_content_type='text/markdown',
        author='ScientiaCapital',
        author_email='info@scientiacapital.com',
        maintainer='ScientiaCapital',
        packages=find_packages(include=['alphalens', 'alphalens.*']),
        package_data={
            'alphalens': ['examples/*'],
        },
        classifiers=[
            'Development Status :: 4 - Beta',
            'Intended Audience :: Developers',
            'Intended Audience :: Financial and Insurance Industry',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: Apache Software License',
            'Natural Language :: English',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: 3.11',
            'Topic :: Office/Business :: Financial :: Investment',
            'Topic :: Scientific/Engineering :: Artificial Intelligence',
            'Topic :: Scientific/Engineering :: Information Analysis',
        ],
        url='https://github.com/ScientiaCapital/alpha-lens',
        project_urls={
            'Documentation': 'https://github.com/ScientiaCapital/alpha-lens',
            'Source': 'https://github.com/ScientiaCapital/alpha-lens',
            'Tracker': 'https://github.com/ScientiaCapital/alpha-lens/issues',
        },
        python_requires='>=3.8',
        install_requires=install_reqs,
        extras_require=extra_reqs,
        keywords='quantitative finance algorithmic trading alpha factors machine learning ai agents',
    )
