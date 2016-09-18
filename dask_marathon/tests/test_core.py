from distributed.utils_test import gen_cluster, loop, slowinc

from time import time, sleep

from distributed import Client
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
            tasks = C.client.list_tasks(app_id=C.app.id)
            names = {d['name'] for d in s.worker_info.values()}
            assert names == {t.id for t in tasks}

        yield C._retire_workers()

        start = time()
        while len(s.worker_info) > 1:
            yield gen.sleep(0.01)
            assert time() < start + 5

        assert len(s.who_has) == len(futures)



def test_sync(loop):
    from threading import Thread
    thread = Thread(target=loop.start); thread.daemon = True
    thread.start()
    from distributed import Scheduler
    s = Scheduler(loop=loop)
    s.start(0)
    with ResponsiveCluster(s, cpus=1, mem=1000,
            executable='/opt/anaconda/bin/dask-worker') as cluster:
        with Client(s.address, loop=loop) as c:
            assert not s.ncores
            x = c.submit(lambda x: x + 1, 1)
            x.result()
            assert len(s.ncores) == 1

            del x

            start = time()
            while s.ncores:
                sleep(0.01)
                assert time() < start + 5
