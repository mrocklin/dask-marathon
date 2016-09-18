from marathon import MarathonClient, MarathonApp
import uuid


class ResponsiveCluster(object):
    def __init__(self, scheduler, executable='dask-worker',
            marathon_address='http://localhost:8080', name=None,
            minimum_instances=0, **kwargs):

        self.client = MarathonClient(marathon_address)
        self.scheduler = scheduler
        self.minimum_instances = minimum_instances
        self.marathon_address = marathon_address

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

    def adapt(self):
        if self.should_scale_up():
            instances = max(2, len(self.scheduler.ncores) * 2)
            self.client.scale_app(self.app.id, instances=instances)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self.client.delete_app(self.app.id)
