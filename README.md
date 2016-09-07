## Dask-Mesos

(Originally forked from https://github.com/bobrik/mesos-compose)


## Setup

- docker version >1.11.1
- docker-compose version >1.7.1

```bash
export DOCKER_IP=127.0.0.1
docker-compose up
```

With the Mesos docker setup operational, move *into* the `mesos_master` docker container
and execute mesos and marathon job submissions

```bash
docker exec -it mesos_master /bin/bash
```

Note: this directory, `dask-mesos` is an attached volume in the `mesos_master`.  

In the `mesos_master` docker container,

```
cd /dask-mesos
python hello-mesos.py
```

## Additional notes

- Master and Slaves have distributed and dask installed from their respective github repos
- Mesos container names:
  - mesos_master
  - mesos_slave_one
  - mesos_slave_two

## Web UIs

- http://localhost:5050/ for Mesos master UI
- http://localhost:5051/ for the first Mesos slave UI
- http://localhost:5052/ for the second Mesos slave UI
- http://localhost:8080/ for Marathon UI
- http://localhost:8888/ for Chronos UI

