# -*- coding: utf-8 -*-
"""
PySLM setup file
=================

Author:
    Leonardo Jacomussi, leonardo.jacomussi@eac.ufsm.br

"""

from setuptools import setup
import os

path_setup = os.path.join(os.path.dirname(os.path.realpath('__file__')), 'pyslm')
path_icon = os.path.join(path_setup, 'Icons')

with open("README.md", "r") as f:
    long_description = f.read()

settings = {
    'name': 'PySLM',
    'version': '1.2',
    'description': "Pythonic Sound Level Meter.",
    'long_description': long_description,
    'long_description_content_type': 'text/markdown',
    'url': 'https://github.com/leonardojacomussi/PySLM',
    'author': 'Leonardo Jacomussi',
    'author_email': 'leonardo.jacomussi@eac.ufsm.br',
    'license': 'MIT',
    'install_requires': ['numpy>=1.19.1', 'scipy>=1.5.0', 'matplotlib>=3.3.1', 'PyQt5',
                         'sounddevice>=0.4.0', 'h5py>=2.10.0', 'pyqtgraph>=0.11.0'],
    'packages': ['pyslm'],
    'package_dir': {'PySLM': 'pyslm'},
    'classifiers': [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent", ],
    'include_package_data': True
}

setup(**settings)