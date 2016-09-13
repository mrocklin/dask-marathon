
from collections import deque
import logging
import time
from threading import Thread
import uuid

from mesos.interface import Scheduler
from mesos.native import MesosSchedulerDriver
from mesos.interface import mesos_pb2

logger = logging.getLogger(__file__)
logging.basicConfig(format='%(levelname)s - %(message)s',
                    level=logging.DEBUG)


class DaskMesosDeployment(object):
    def __init__(self, target, scheduler_address, **kwargs):
        self.scheduler = DaskMesosScheduler(target, scheduler_address, **kwargs)
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
    def __init__(self, target, scheduler, cpus=1, mem=4096, disk=2**16):
        self.target = target
        self.scheduler = scheduler
        self.cpus = cpus
        self.mem = mem
        self.disk = disk
        self.worker_executable = '/opt/anaconda/bin/dask-worker'
        self.status_messages = deque(maxlen=10000)
        self.recent_offers = deque(maxlen=100)
        self.submitted = set()
        self.acknowledged = set()

    def registered(self, driver, framework_id, master_info):
        logger.info("Registered with framework id: {}".format(framework_id))
        logger.debug("Registered with frameowrk, %s, %s", framework_id,
                master_info)

    def reregistered(self, driver, master_info):
        logger.debug("Reregistered with frameowrk, %s", master_info)

    def disconnected(self, driver):
        logger.debug("Disconnected")

    def parse_offer(self, offer):
        r = {r.name: r.scalar.value for r in offer.resources}
        r['hostname'] = offer.hostname
        return r

    def resourceOffers(self, driver, offers):
        self.recent_offers.extend(offers)
        logger.debug("Received offers: %s", offers)

        for offer in offers:
            if (len(self.scheduler.ncores)
              + len(self.submitted - self.acknowledged)) >= self.target:
                continue  # ignore if satisfied
            o = self.parse_offer(offer)
            logger.info("Considering offer %s", o)

            if (o.get('cpus', 0) > self.cpus and
                o.get('mem', 0) > self.mem and
                o.get('disk', 0) > self.disk):

                task = self.task_info(offer)
                options = {'--nthreads': self.cpus,
                           '--memory-limit': int(self.mem * 0.7)}
                command = '%s %s ' % (self.worker_executable, self.scheduler.address)
                command += ' '.join(' '.join(map(str, item)) for item in options.items())

                task.command.value = command

                logger.info("Launch task %s with offer %s", task.task_id.value,
                            offer.id.value)
                self.submitted.add(task.task_id.value)
                driver.launchTasks(offer.id, [task])

    def task_info(self, offer):
        task = mesos_pb2.TaskInfo()
        id = str(uuid.uuid4())
        task.task_id.value = id
        task.slave_id.value = offer.slave_id.value
        task.name = "dask-worker-%s" % id

        cpus = task.resources.add()
        cpus.name = "cpus"
        cpus.type = mesos_pb2.Value.SCALAR
        cpus.scalar.value = self.cpus

        mem = task.resources.add()
        mem.name = "mem"
        mem.type = mesos_pb2.Value.SCALAR
        mem.scalar.value = self.mem

        mem = task.resources.add()
        mem.name = "disk"
        mem.type = mesos_pb2.Value.SCALAR
        mem.scalar.value = self.disk

        return task

    def offerRescinded(self, driver, offerId):
        logger.debug("Offer rescinded: %s", offerId)

    def frameworkMessage(self, driver, executorId, slaveId, message):
        logger.debug("Framework message.  executorId: %s, slaveId: %s, message: %s", executorId, slaveId, message)

    def slaveLost(self, driver, slaveId):
        logger.debug("Slave lost: %s", slaveId)

    def executorLost(self, driver, executorId, slaveId, status):
        logger.debug("Executor lost: executorId: %s, slaveId: %s, status: %s", executorId, slaveId, status)

    def error(self, driver, message):
        logger.info("error: %s", message)

    def statusUpdate(self, driver, status):
        logger.debug("Status update: %s", status)
        self.status_messages.append(status)
