#!/usr/bin/env python

from os.path import exists
from setuptools import setup

setup(name='dask_marathon',
      version='0.0.1',
      description='Deploy Dask on Marathon',
      url='http://github.com/mrocklin/dask-marathon/',
      maintainer='Matthew Rocklin',
      maintainer_email='mrocklin@gmail.com',
      license='BSD',
      keywords='',
      packages=['dask_marathon'],
      tests_require=['pytest'],
      setup_requires=['pytest-runner'],
      install_requires=['distributed', 'marathon==0.8.9'],
      long_description=(open('README.rst').read() if exists('README.rst')
                        else ''),
      zip_safe=False)
