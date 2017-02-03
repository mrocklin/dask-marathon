from distributed.utils_test import gen_cluster, loop, slowinc

from time import time, sleep

from distributed import Client
from distributed.deploy import Adaptive
from dask_marathon import MarathonCluster
from tornado import gen

from marathon import MarathonClient
cg = MarathonClient('http://localhost:8080')

for app in cg.list_apps():
    cg.delete_app(app.id, force=True)


@gen_cluster(client=True, ncores=[], timeout=20)
def test_simple(c, s):
    with MarathonCluster(s, cpus=1, mem=1024) as mc:
        mc.scale_up(1)
        while len(s.workers) < 1:
            yield gen.sleep(0.01)

        mc.scale_down(s.workers)
        while s.workers:
            yield gen.sleep(0.01)
