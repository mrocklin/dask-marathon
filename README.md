## Dask-Mesos

(Originally forked from https://github.com/bobrik/mesos-compose)


## Setup

- docker version >1.11.1
- docker-compose version >1.7.1

```bash
export DOCKER_IP=127.0.0.1
docker-compose up
```

Web UIs

That's it, use the following URLs:

- http://localhost:5050/ for Mesos master UI
- http://localhost:5051/ for the first Mesos slave UI
- http://localhost:5052/ for the second Mesos slave UI
- http://localhost:8080/ for Marathon UI
- http://localhost:8888/ for Chronos UI

