import os
import sys
from codecs import open

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "vcsi", "VERSION")) as f:
    VERSION = f.readline().strip()

install_requires = ['numpy', 'pillow', 'jinja2', 'texttable', 'parsedatetime', 'beautifulsoup4', 'lxml']

if sys.version_info < (3, 4):
    install_requires += ['enum34']

setup(
    name='vcsi',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=VERSION,

    description='Create video contact sheets, thumbnails, screenshots',
    long_description='',

    # The project's main homepage.
    url='https://github.com/amietn/vcsi',

    # Author details
    author='Nils Amiet',
    author_email='amietn@foobar.tld',

    # Choose your license
    license='MIT',

    # What does your project relate to?
    keywords='video thumbnail contact sheet multimedia',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=install_requires,

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
        'dev': ['check-manifest'],
        'test': ['coverage'],
    },

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'vcsi=vcsi:main',
        ],
    },

    # Additional files to install in the package directory
    package_data={
        "vcsi": ["VERSION"]
    }
)
