# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

# Get the long description from the README file
with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='jaeger_lab_to_nwb',
    version='0.1.0',
    description='NWB conversion scripts and tutorials.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Luiz Tauffer and Ben Dichter',
    email='ben.dichter@gmail.com',
    packages=find_packages(),
    include_package_data=True,
    package_data={'': ['*.yml']},
    install_requires=[
        'matplotlib', 'cycler', 'scipy', 'numpy', 'jupyter', 'h5py', 'pynwb',
        'pyintan', 'nwbn-conversion-tools', 'ndx-fret'],
    entry_points={
        'console_scripts': ['nwbn-gui-jaeger=jaeger_lab_to_nwb.gui_command_line:main'],
    }
)
