#!/usr/bin/env python3
"""
Setup script for ISO Editor
"""

from setuptools import setup, find_packages
import os

# Read the long description from README
def read_long_description():
    """Read the README file for the long description."""
    here = os.path.abspath(os.path.dirname(__file__))
    readme_path = os.path.join(here, 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ''

# Read requirements from requirements.txt
def read_requirements():
    """Read the requirements file."""
    here = os.path.abspath(os.path.dirname(__file__))
    req_path = os.path.join(here, 'requirements.txt')
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name='iso-editor',
    version='1.0.0',
    author='ISO Editor Team',
    author_email='',
    description='A comprehensive ISO image editor with GUI',
    long_description=read_long_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/ivenhartford/ISO_editor',
    project_urls={
        'Bug Tracker': 'https://github.com/ivenhartford/ISO_editor/issues',
        'Documentation': 'https://github.com/ivenhartford/ISO_editor#readme',
        'Source Code': 'https://github.com/ivenhartford/ISO_editor',
    },
    py_modules=['ISO_edit', 'iso_logic', 'create_test_iso'],
    python_requires='>=3.8',
    install_requires=read_requirements(),
    extras_require={
        'dev': [
            'pytest>=7.0',
            'pytest-qt>=4.0',
            'pytest-cov>=3.0',
            'pylint>=2.0',
            'mypy>=0.9',
        ],
    },
    entry_points={
        'console_scripts': [
            'iso-editor=ISO_edit:main',
        ],
        'gui_scripts': [
            'iso-editor-gui=ISO_edit:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Archiving',
        'Topic :: System :: Filesystems',
        'Topic :: Utilities',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS',
        'Environment :: X11 Applications :: Qt',
        'Natural Language :: English',
    ],
    keywords='iso editor cd dvd image disk bootable eltorito udf joliet',
    license='Apache-2.0',
    platforms=['any'],
    include_package_data=True,
    zip_safe=False,
)
