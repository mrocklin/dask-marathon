import logging
import uuid

from marathon import MarathonClient, MarathonApp
from tornado.ioloop import PeriodicCallback
from tornado import gen

logger = logging.getLogger(__file__)


class ResponsiveCluster(object):
    def __init__(self, scheduler, executable='dask-worker',
            marathon_address='http://localhost:8080', name=None,
            minimum_instances=0, **kwargs):

        self.client = MarathonClient(marathon_address)
        self.scheduler = scheduler
        self.minimum_instances = minimum_instances
        self.marathon_address = marathon_address
        self._adapt_callback = PeriodicCallback(self.adapt, 1000,
                self.scheduler.loop)
        self._adapt_callback.start()

        args = [executable, scheduler.address,
                '--name', '$MESOS_TASK_ID']
        if 'mem' in kwargs:
            args.extend(['--memory-limit',
                         str(int(kwargs['mem'] * 0.6 * 1e6))])
        kwargs['cmd'] = ' '.join(args)

        app = MarathonApp(instances=minimum_instances, **kwargs)
        self.app = self.client.create_app(name or 'dask-%s' % uuid.uuid4(), app)

    def should_scale_up(self):
        return (self.scheduler.ready or
            any(self.scheduler.stealable) and not self.scheduler.idle)

    def workers_to_close(self):
        if not self.scheduler.idle:
            return []
        limit_bytes = {w: self.scheduler.worker_info[w]['memory_limit']
                        for w in self.scheduler.worker_info}
        worker_bytes = self.scheduler.worker_bytes

        limit = sum(limit_bytes.values())
        total = sum(worker_bytes.values())
        idle = sorted(self.scheduler.idle, key=worker_bytes.get)

        to_release = []

        while idle:
            w = idle.pop()
            limit -= limit_bytes[w]
            if limit >= 2 * total:  # still plenty of space
                to_release.append(w)
            else:
                break

        return to_release

    def retire_workers(self):
        self.scheduler.loop.add_callback(self._retire_workers)

    @gen.coroutine
    def _retire_workers(self):
        workers = set(self.workers_to_close())
        if not workers:
            return
        keys = set.union(*[self.scheduler.has_what[w] for w in workers])
        keys = {k for k in keys if self.scheduler.who_has[k].issubset(workers)}

        other_workers = set(self.scheduler.worker_info) - workers
        if keys:
            if other_workers:
                yield self.scheduler.replicate(keys=keys, workers=other_workers,
                                               n=1, delete=False)
            else:
                raise gen.Return()

        logger.info("Retiring workers %s", workers)
        for w in workers:
            self.client.kill_task(self.app.id,
                                  self.scheduler.worker_info[w]['name'],
                                  scale=True)

    def adapt(self):
        if self.should_scale_up():
            instances = max(1, len(self.scheduler.ncores) * 2)
            self.client.scale_app(self.app.id, instances=instances)

        self.retire_workers()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self.client.delete_app(self.app.id, force=True)
