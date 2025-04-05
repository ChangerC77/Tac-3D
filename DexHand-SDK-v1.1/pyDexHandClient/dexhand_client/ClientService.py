from .ClientLogger import ClientLogger
import numpy as np
import time
from enum import Enum

class TASKRET(Enum):
    succeeded = 1
    failed = 0
    lost = -1


class TaskInfo:
    def __init__(self, task_id: int):
        self.id = task_id
        self.sent = False
        self.state = ServiceTaskManager.TASK_UNKNOWN
        self.started = False
        self.stopped = False


class ServiceTaskManager:
    TASK_UNKNOWN = 0
    TASK_ARG_ERROR = 1
    TASK_START = 2
    TASK_UPDATE = 3
    TASK_FAILED = 4
    TASK_SUCCEED = 5

    def __init__(self, parent, logger: ClientLogger):
        self.parent = parent
        self.task_id = np.random.randint(0, 65536)
        self.task_list = []
        self.logger = logger
        self._need_popout = False

    def get_task_id(self):
        assigned_task_id = self.task_id
        self.task_id = (self.task_id + 1) % 65536
        return assigned_task_id

    def check_task_copy(self, task_id: int, task_name: str) -> TASKRET:
        now_task = TaskInfo(task_id)
        st_time = time.time()
        self.task_list.append(now_task)

        while now_task.sent == False and not self._need_popout:
            time.sleep(0.001)
            if self._check_timeout(st_time):
                self.task_list.remove(now_task)
                return TASKRET.lost.value

        # check arg error
        if now_task.state == ServiceTaskManager.TASK_ARG_ERROR or self._need_popout:
            self.task_list.remove(now_task)
            return TASKRET.failed.value

        while now_task.started == False and not self._need_popout:
            time.sleep(0.001)

        self.task_list.remove(now_task)
        return TASKRET.failed.value if self._need_popout else TASKRET.succeeded.value

    def listen_in_task(self, task_id: int, task_name: str)-> TASKRET:
        now_task = TaskInfo(task_id)
        st_time = time.time()
        self.task_list.append(now_task)

        while now_task.sent == False and not self._need_popout:
            time.sleep(0.001)
            if self._check_timeout(st_time):
                self.task_list.remove(now_task)
                return TASKRET.lost.value

        # check arg error
        if now_task.state == ServiceTaskManager.TASK_ARG_ERROR or self._need_popout:
            self.task_list.remove(now_task)
            return TASKRET.failed.value
        while now_task.started == False and not self._need_popout:
            time.sleep(0.001)
        while now_task.stopped == False and not self._need_popout:
            time.sleep(0.001)

        if self._need_popout:
            self.task_list.remove(now_task)
            return TASKRET.failed.value
        self.task_list.remove(now_task)
        return TASKRET.succeeded.value if now_task.state == ServiceTaskManager.TASK_SUCCEED else TASKRET.failed.value

    def unpack_msg(self, data):
        for now_task in self.task_list:
            if data["TaskID"] == now_task.id:
                if data["SubTask"] == False:
                    now_task.state = data["TaskInfo"]
                    # got message
                    if (
                        now_task.state == ServiceTaskManager.TASK_ARG_ERROR
                        or now_task.state == ServiceTaskManager.TASK_START
                        or now_task.state == ServiceTaskManager.TASK_UPDATE
                        or now_task.state == ServiceTaskManager.TASK_FAILED
                        or now_task.state == ServiceTaskManager.TASK_SUCCEED
                    ):
                        now_task.sent = True
                    # start
                    if (
                        now_task.state == ServiceTaskManager.TASK_START
                        or now_task.state == ServiceTaskManager.TASK_UPDATE
                        or now_task.state == ServiceTaskManager.TASK_FAILED
                        or now_task.state == ServiceTaskManager.TASK_SUCCEED
                    ):
                        now_task.started = True
                    # end
                    if (
                        now_task.state == ServiceTaskManager.TASK_FAILED
                        or now_task.state == ServiceTaskManager.TASK_SUCCEED
                    ):
                        now_task.stopped = True

                if data["Msg"] is None:
                    return
                msg = data["Msg"]
                device = data["Device"]
                self.logger.push_log(data["LogLevel"], f"{device}: {msg}", from_server=True)

    def _check_timeout(self, st_time):
        if time.time() > st_time + 1:
            self.logger.push_log(self.logger.WARN,"Client: Timeout. The package may be lost.")
            return True
        return False
