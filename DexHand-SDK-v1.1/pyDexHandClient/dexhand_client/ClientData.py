from .ClientLogger import ClientLogger
import logging
import numpy as np


class DexHandDataManager:
    def __init__(self, info_config, logger, recvCallback, client_ptr):
        self._recv_time = None
        self._frame_cnt = 0
        self._watchdog = 0
        self._recvCallback = recvCallback
        self._logger: ClientLogger = logger
        self._auto_extract = info_config["auto_extract"]
        self._client_ptr = client_ptr
        if not self._auto_extract:
            self.frame = None
            return

        self._components = info_config["InfoComponents"]
        if "Ego" in self._components:
            self.now_pos = None
            self.goal_pos = None
            self.now_speed = None
            self.goal_speed = None
            self.now_current = None
            self.goal_current = None
            self._task_info = {}
            self.now_task = None
            self.recent_task = None
            self.recent_task_status = None
            self.error_flag = None


        if "Force" in self._components:
            self.now_force = []
            self.avg_force = None
            self.goal_force = None
            self.stiffness = None

        if "Imu" in self._components:
            self.imu_acc = np.empty(3, dtype=np.float32)
            self.imu_gyr = np.empty(3, dtype=np.float32)

        if "Contact" in self._components:
            self.is_contact = []

    def _unpack_data(self, data, recv_time):
        self._watchdog = 0
        if self._recv_time is not None and self._recv_time > recv_time:
            return

        self._recv_time = recv_time
        self._frame_cnt += 1
        if not self._auto_extract:
            self.frame = data

        else:
            log_str = ""
            if "Ego" in self._components:
                self.now_pos = data["now_pos"]
                self.goal_pos = data["goal_pos"]
                self.now_speed = data["now_speed"]
                self.goal_speed = data["goal_speed"]
                self.now_current = data["now_current"]
                self.goal_current = data["goal_current"]
                self._task_info = data["task_info"]
                self.now_task = self._task_info["now_task"]
                self.recent_task = self._task_info["recent_task"]
                self.recent_task_status = self._task_info["recent_task_status"]
                self.error_flag = self._task_info["error_flag"]
                log_str += (
                    f"error:{self.error_flag}, {self.now_task} ({self.recent_task},{self.recent_task_status})"
                    + f"Pos:{self.now_pos:.2f}/{self.goal_pos:.2f} Speed:{self.now_speed:.2f}/{self.goal_speed:.2f}, Current:{self.now_current:.2f} "
                )

            if "Force" in self._components:
                self.now_force = data["now_force"]
                self.avg_force = data["avg_force"]
                self.goal_force = data["goal_force"]
                self.stiffness = data["stiffness"]
                log_str += f"Force:{self.avg_force:.3f}/{self.goal_force:.3f}"

            if "Imu" in self._components:
                self.imu_acc[:] = data["imu_acc"]
                self.imu_gyr[:] = data["imu_gyr"]

            if "Contact" in self._components:
                self.is_contact = data["is_contact"]

            if self._frame_cnt % 10 == 0:
                self._logger.push_log(ClientLogger.DEBUG, log_str)

        # print(self.recvCallback)
        if self._recvCallback is not None:
            self._recvCallback(self._client_ptr)


class Tac3D_Data:
    def __init__(self, SN, auto_extract, components):
        self.recv_time = None
        self.SN = SN
        self._auto_extract = auto_extract
        self._components = components
        self._frame_cnt = 0

        if not self._auto_extract:
            self.frame = None
            return

        if "Basic" in components:
            self.P = np.empty((20, 20, 3), dtype=np.float32)
            self.D = np.empty((20, 20, 3), dtype=np.float32)
            self.F = np.empty((20, 20, 3), dtype=np.float32)
            self.Fr = np.empty(3, dtype=np.float32)
            self.Mr = np.empty(3, dtype=np.float32)
        if "Contact" in components:
            self.is_contact: bool = False

    def extract_data(self, frame, recv_time) -> bool:
        if self.recv_time is not None and self.recv_time > recv_time:
            return False

        self.recv_time = recv_time
        self._frame_cnt += 1
        if not self._auto_extract:
            self.frame = frame
            return True
        if "Basic" in self._components:
            self.P[...] = frame["3D_Positions"].reshape(20, 20, 3)
            self.D[...] = frame["3D_Displacements"].reshape(20, 20, 3)
            self.F[...] = frame["3D_Forces"].reshape(20, 20, 3)
            self.Fr[:] = frame["3D_ResultantForce"].reshape(-1)
            self.Mr[:] = frame["3D_ResultantMoment"].reshape(-1)

        return True


class Tac3DDataManager:
    def __init__(self, info_config, logger, recvCallback, client_ptr):
        self.logger: ClientLogger = logger
        self.recvCallback = recvCallback
        self.client_ptr = client_ptr

        self._auto_extract = info_config["auto_extract"]
        self._info_components = info_config["InfoComponents"]
        self.SN_list = []
        self.tac_info = {}

    def _unpack_data(self, data, recv_time, SN):
        if SN not in self.SN_list:
            self.SN_list.append(SN)
            self.tac_info[SN] = Tac3D_Data(SN, self._auto_extract, self._info_components)

        ret = self.tac_info[SN].extract_data(data, recv_time)
        if ret and self.recvCallback is not None:
            self.recvCallback(self.client_ptr, SN)


class DataManager:
    def __init__(self, config, logger: ClientLogger, recvCallback_hand=None, recvCallback_tac=None, client_ptr=None):
        self.logger: ClientLogger = logger
        if "HandControl" in config["DexHandComponents"]:
            self.hand_data = DexHandDataManager(config["HandInfoConfig"], logger, recvCallback_hand, client_ptr)
        else:
            self.hand_data = None
        if "Tac3D" in config["DexHandComponents"]:
            self.tac3d_data = Tac3DDataManager(config["Tac3DInfoConfig"], logger, recvCallback_tac, client_ptr)
        else:
            self.tac3d_data = None

    def unpack_msg(self, msg):
        if msg["Device"] == "Hand":
            if self.hand_data is None:
                self.logger.push_log(logging.ERROR, "Client has no DexHand device.", from_server=True)
                return
            self.hand_data._unpack_data(msg["Data"], msg["Time"])

        elif msg["Device"] == "Tac3D":
            if self.hand_data is None:
                self.logger.push_log(logging.ERROR, "Client has no Tac3D device.", from_server=True)
                return
            self.tac3d_data._unpack_data(msg["Data"], msg["Time"], msg["SN"])

        else:
            self.logger.push_log(logging.ERROR, "a msg from unknown device was received.", from_server=True)
