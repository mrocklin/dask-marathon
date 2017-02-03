from distributed.utils_test import gen_cluster, loop, slowinc

from time import time, sleep

from distributed import Client, Scheduler
from distributed.deploy import Adaptive
from dask_marathon import MarathonCluster
from threading import Thread

from marathon import MarathonClient
cg = MarathonClient('http://localhost:8080')

for app in cg.list_apps():
    cg.delete_app(app.id, force=True)


def test_simple(loop):
    thread = Thread(target=loop.start); thread.daemon = True
    thread.start()
    s = Scheduler(loop=loop)
    s.start(0)

    with MarathonCluster(s, cpus=1, mem=1000) as mc:
        mc.scale_up(1)
        while len(s.workers) < 1:
            sleep(0.01)

        mc.scale_down(s.workers)
        while s.workers:
            sleep(0.01)


def test_adapt(loop):
    thread = Thread(target=loop.start); thread.daemon = True
    thread.start()
    s = Scheduler(loop=loop)
    s.start(0)

    with MarathonCluster(s, cpus=1, mem=1000) as mc:
        ac = Adaptive(s, mc)
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
