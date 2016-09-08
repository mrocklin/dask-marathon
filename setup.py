#!/usr/bin/env python

from os.path import exists
from setuptools import setup

setup(name='dask_mesos',
      version='0.0.1',
      description='Deploy Dask on Mesos',
      url='http://github.com/dask/dask-mesos/',
      maintainer='Matthew Rocklin',
      maintainer_email='mrocklin@gmail.com',
      license='BSD',
      keywords='',
      packages=['dask_mesos'],
      install_requires=list(open('requirements.txt').read().strip().split('\n')),
      long_description=(open('README.rst').read() if exists('README.rst')
                        else ''),
      zip_safe=False)
