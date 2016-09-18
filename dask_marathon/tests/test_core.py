from distributed.utils_test import gen_cluster

from time import time

from dask_marathon import ResponsiveCluster
from tornado import gen

from marathon import MarathonClient
cg = MarathonClient('http://localhost:8080')

for app in cg.list_apps():
    cg.delete_app(app.id)


@gen_cluster(client=True, ncores=[])
def test_simple(c, s):
    with ResponsiveCluster(s, cpus=1, mem=256,
            executable='/opt/anaconda/bin/dask-worker') as C:
        C.adapt()
        yield gen.sleep(0.1)
        assert not s.ncores

        futures = c.map(lambda x: x + 1, range(10))
        start = time()
        while not s.ready:
            yield gen.sleep(0.01)
            assert time() < start + 5

        C.adapt()

        results = yield c._gather(futures)
        assert s.transition_log

        if s.worker_info:
            names = {d['name'] for d in s.worker_info.values()}
            tasks = C.client.list_tasks(app_id=C.app.id)
            assert names == {t.id for t in tasks}

        to_release = C.workers_to_close()
