Dask-Marathon
==========

|Build Status|

.. |Build Status| image:: https://travis-ci.org/dask/dask-marathon.svg
   :target: https://travis-ci.org/dask/dask-marathon

Deploy ``dask-worker`` processes on Marathon in response to load on a Dask
scheduler.  This creates a Marathon application of dask-worker processes.  It
watches a Dask Scheduler object in the local process and, based on current
requested load, scales the Marathon application up and down.

This project is a proof of concept only.  No guarantee of quality or future
maintenance is made.

Run
---

It's not yet clear how to expose all of the necessary options to a command line
interface.  For now we're doing everything manually.

Make an IOLoop running in a separate thread:

.. code-block:: python

    from threading import Thread
    from tornado.ioloop import IOLoop
    loop = IOLoop()
    thread = Thread(target=loop.start); thread.daemon = True
    thread.start()

Start a Scheduler in that IOLoop

.. code-block:: python

    from distributed import Scheduler
    s = Scheduler(loop=loop)
    s.start()

Start a dask-marathon cluster.  Give it the scheduler, information about the
application, and the address of the Marathon master.  This example assumes that
``dask-worker`` is available in the system environment, but see see
``marathon.MarathonApp`` for possible keyword args to define the application,
including docker containers, etc..

.. code-block:: python

   from dask_marathon import MarathonCluster
   cluster = MarathonCluster(s, marathon_address='http://localhost:8080',
                             cpus=1, mem=1000, executable='dask-worker',
                             **kwargs)

Create a Client and submit work to the scheduler.  Marathon will scale workers
up and down as neccessary in response to current workload.

.. code-block:: python

   from distributed import Client
   c = Client(s.address)

   future = c.submit(lambda x: x + 1, 10)


TODO
----

-  Deploy the scheduler on the cluster
-  Support a command line interface


Docker Testing Harness
----------------------

This sets up a docker cluster of one Mesos master and two Mesos agents using
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
~~~~~~~~~~~~~~~~

- Master and Agents have dask.distributed installed its github repository
- Mesos container names:
  - mesos_master
  - mesos_slave_one
  - mesos_slave_two


Web UIs
~~~~~~~

- http://localhost:5050/ for Mesos master UI
- http://localhost:5051/ for the first Mesos agent UI
- http://localhost:5052/ for the second Mesos agent UI
- http://localhost:8080/ for Marathon UI
- http://localhost:8888/ for Chronos UI


History
~~~~~~~

Mesos Docker-compose solution originally forked from https://github.com/bobrik/mesos-compose

This project was then forked from dask-mesos.
