
from concurrent.futures import ThreadPoolExecutor
import logging
import uuid

from distributed.deploy import Adaptive

from marathon import MarathonClient, MarathonApp
from tornado.ioloop import PeriodicCallback
from tornado import gen

logger = logging.getLogger(__file__)


class AdaptiveCluster(Adaptive):
    def __init__(self, scheduler, executable='dask-worker',
            marathon_address='http://localhost:8080', name=None, **kwargs):
        self.scheduler = scheduler
        self.executor = ThreadPoolExecutor(1)

        # Create Marathon App to run dask-worker
        args = [executable, scheduler.address,
                '--name', '$MESOS_TASK_ID']
        if 'mem' in kwargs:
            args.extend(['--memory-limit',
                         str(int(kwargs['mem'] * 0.6 * 1e6))])
        kwargs['cmd'] = ' '.join(args)
        app = MarathonApp(instances=0, **kwargs)

        # Connect and register app
        self.client = MarathonClient(marathon_address)
        self.app = self.client.create_app(name or 'dask-%s' % uuid.uuid4(), app)

        super(AdaptiveCluster, self).__init__()

    @gen.coroutine
    def scale_up(self, instances):
        instances = max(1, len(self.scheduler.ncores) * 2)
        yield self.executor.submit(self.client.scale_app,
                self.app.id, instances=instances)

    @gen.coroutine
    def scale_down(self, workers):
        for w in workers:
            yield self.executor.submit(self.client.kill_task,
                                       self.app.id,
                                       self.scheduler.worker_info[w]['name'],
                                       scale=True)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self.client.delete_app(self.app.id, force=True)
