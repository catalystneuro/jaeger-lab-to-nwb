# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


# Get requirements
with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

# Get the long description from the README file
with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='jaeger_lab_to_nwb',
    version='0.1.1',
    description='NWB conversion scripts and tutorials.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Luiz Tauffer and Ben Dichter',
    email='ben.dichter@gmail.com',
    packages=find_packages(),
    include_package_data=True,
    package_data={'jaeger_lab_to_nwb': [
        'bpodconverter/*.yml',
    ]},
    install_requires=install_requires,
    entry_points={
        'console_scripts': ['nwbgui-jaeger=jaeger_lab_to_nwb.cmd_line:cmd_line_shortcut'],
    }
)
