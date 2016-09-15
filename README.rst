Dask-Marathon
==========

|Build Status|

.. |Build Status| image:: https://travis-ci.org/dask/dask-marathon.svg
   :target: https://travis-ci.org/dask/dask-marathon

A simple Mesos Scheduler to deploy Dask.distributed workers.


Test locally
------------

This sets up a docker cluster of one Mesos master and two Mesos slaves using
docker-compose.

**Requires**:

- docker version >= 1.11.1
- docker-compose version >= 1.7.1

::

   export DOCKER_IP=127.0.0.1
   docker-compose up

Run py.test::

   py.test dask-marathon

Additional notes
----------------

- Master and Slaves have dask.distributed installed its github repository
- Mesos container names:
  - mesos_master
  - mesos_slave_one
  - mesos_slave_two


Web UIs
-------

- http://localhost:5050/ for Mesos master UI
- http://localhost:5051/ for the first Mesos slave UI
- http://localhost:5052/ for the second Mesos slave UI
- http://localhost:8080/ for Marathon UI
- http://localhost:8888/ for Chronos UI


History
-------

Mesos Docker-compose solution originally forked from https://github.com/bobrik/mesos-compose

This project was then forked from dask-mesos.
