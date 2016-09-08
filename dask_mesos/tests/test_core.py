from dask_mesos import DaskMesosDeployment

from distributed.utils_test import gen_cluster

from tornado import gen

from time import time

@gen_cluster(ncores=[])
def test_simple(s):
    DM = DaskMesosDeployment(2, s.address)
    DM.start()

    start = time()
    while len(s.ncores) < 2:
        yield gen.sleep(0.1)
        assert time() < start + 5

    yield gen.sleep(0.2)
    assert len(s.ncores) == 2  # still 2 after some time
