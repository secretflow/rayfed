import os

import setuptools
from setuptools import find_packages, setup

this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

plat_name = "any"


def read_requirements():
    requirements = []
    with open('requirements.txt') as file:
        requirements = file.read().splitlines()
    requirements = [req for req in requirements if not req.startswith('ray')]
    #TODO raplace with 'ant-ray'
    requirements.append('ray==1.13')
    print("Requirements: ", requirements)
    return requirements


# [ref](https://github.com/perwin/pyimfit/blob/master/setup.py)
# Modified cleanup command to remove build subdirectory
# Based on: https://stackoverflow.com/questions/1710839/custom-distutils-commands
class CleanCommand(setuptools.Command):
    description = "custom clean command that forcefully removes dist/build directories"
    user_options = []

    def initialize_options(self):
        self._cwd = None

    def finalize_options(self):
        self._cwd = os.getcwd()

    def run(self):
        assert os.getcwd() == self._cwd, 'Must be in package root: %s' % self._cwd
        os.system('rm -rf ./build ./dist')


setup(
    name='secretflow-rayfed-tee',
    version='0.1.1a0',
    license='Apache 2.0',
    description='A multiple parties joint, distributed execution engine based on Ray,'
                'to help build your own federated learning frameworks in minutes.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='RayFed Team',
    author_email='rayfed-dev@googlegroups.com',
    url='https://github.com/ray-project/rayfed',
    packages=find_packages(exclude=('examples', 'tests', 'tests.*')),
    install_requires=read_requirements(),
    extras_require={'dev': ['pylint']},
    options={'bdist_wheel': {'plat_name': plat_name}},
)
