import logging
import time
from threading import Thread
import uuid

from mesos.interface import Scheduler
from mesos.native import MesosSchedulerDriver
from mesos.interface import mesos_pb2

logger = logging.getLogger(__file__)

def new_task(offer):
    task = mesos_pb2.TaskInfo()
    id = str(uuid.uuid4())
    task.task_id.value = id
    task.slave_id.value = offer.slave_id.value
    task.name = "dask-worker: %s" % id

    cpus = task.resources.add()
    cpus.name = "cpus"
    cpus.type = mesos_pb2.Value.SCALAR
    cpus.scalar.value = 1

    mem = task.resources.add()
    mem.name = "mem"
    mem.type = mesos_pb2.Value.SCALAR
    mem.scalar.value = 1024

    return task

class DaskMesosDeployment(object):
    def __init__(self, target, scheduler_address):
        self.scheduler = DaskMesosScheduler(target, scheduler_address)
        self.framework = mesos_pb2.FrameworkInfo()
        self.framework.user = ""
        self.framework.name = "dask-scheduler"
        self.driver = MesosSchedulerDriver(self.scheduler, self.framework,
                "zk://localhost:2181/mesos")  # assumes running on the master
        self._thread = None

    def start(self):
        if self._thread:
            return
        self._thread = Thread(target=self.driver.run)
        self._thread.daemon = True
        self._thread.start()


class DaskMesosScheduler(Scheduler):
    def __init__(self, target, scheduler_address):
        self.target = target
        self.workers = 0
        self.scheduler_address = scheduler_address

    def registered(self, driver, framework_id, master_info):
        logger.info("Registered with framework id: {}".format(framework_id))

    def resourceOffers(self, driver, offers):
        logger.debug("Received offers: %s", offers)
        for offer in offers:
            if self.workers >= self.target:  # ignore if satisfied
                continue
            task = new_task(offer)
            task.command.value = ("/opt/anaconda/bin/dask-worker %s" %
                    self.scheduler_address)
            self.workers += 1
            logging.info("Launch task %s with offer %s", task.task_id.value,
                    offer.id.value)
            driver.launchTasks(offer.id, [task])
