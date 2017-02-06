from __future__ import print_function, division, absolute_import

from concurrent.futures import ThreadPoolExecutor
import logging
import uuid

from marathon import MarathonClient, MarathonApp
from marathon.models.container import MarathonContainer

logger = logging.getLogger(__file__)


class MarathonCluster(object):

    def __init__(self, scheduler,
                 executable='dask-worker',
                 docker_image='mrocklin/dask-distributed',
                 marathon_address='http://localhost:8080',
                 username=None, password=None, auth_token=None,
                 app_name=None, **kwargs):
        self.scheduler = scheduler
        self.executor = ThreadPoolExecutor(1)

        # Create Marathon App to run dask-worker
        args = [executable, scheduler.address,
                '--name', '$MESOS_TASK_ID',  # use Mesos task ID as worker name
                '--worker-port', '$PORT_WORKER',
                '--nanny-port', '$PORT_NANNY',
                '--http-port', '$PORT_HTTP']

        ports = [{'port': 0,
                  'protocol': 'tcp',
                  'name': port_name}
                 for port_name in ['worker', 'nanny', 'http']]

        if 'mem' in kwargs:
            args.extend(['--memory-limit',
                         str(int(kwargs['mem'] * 0.6 * 1e6))])

        kwargs['cmd'] = ' '.join(args)
        container = MarathonContainer({'image': docker_image})

        app = MarathonApp(instances=0,
                          container=container,
                          port_definitions=ports,
                          **kwargs)

        # Connect and register app
        self.client = MarathonClient(servers=marathon_address,
                                     username=username, password=password,
                                     auth_token=auth_token)
        self.app = self.client.create_app(
            app_name or 'dask-%s' % uuid.uuid4(), app)

    def scale_up(self, instances):
        self.executor.submit(self.client.scale_app,
                             self.app.id, instances=instances)

    def scale_down(self, workers):
        for w in workers:
            self.executor.submit(self.client.kill_task,
                                 self.app.id,
                                 self.scheduler.worker_info[w]['name'],
                                 scale=True)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self.client.delete_app(self.app.id, force=True)
