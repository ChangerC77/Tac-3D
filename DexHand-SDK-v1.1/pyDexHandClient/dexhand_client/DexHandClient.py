from .ClientData import DataManager
from .ClientLogger import ClientLogger
from .ClientService import ServiceTaskManager
from .UDPManager import UDP_Manager
from .UDPMCManager import UDP_MC_Manager

import json
import logging
import sys
import threading
import time
import pkg_resources
from enum import Enum

class TASKRET(Enum):
    succeeded = 1
    failed = 0
    lost = -1


class DexHandClient:
    def __init__(self, ip: str, port: int, recvCallback_hand=None, ignore_myself=False):
        self.local_ip = ""  # any IP address
        self.local_port = 0  # any available port
        self.server_ip = ip
        self.server_port = port
        self.goal_addr = (self.server_ip, self.server_port)
        self.acquired_hand = False

        ### Initialize modules ###
        config_path = pkg_resources.resource_filename("dexhand_client", "config/DexHandConfig.json")

        with open(config_path, "r+") as f:
            self.config = json.load(f)
            self.components = self.config["DexHandComponents"]

        self.logger = ClientLogger(ignore_myself=ignore_myself)
        self.task_manager = ServiceTaskManager(self, self.logger)
        self.data_manager = DataManager(
            self.config,
            self.logger,
            recvCallback_hand=recvCallback_hand,
            recvCallback_tac=None,
            client_ptr=self,
        )

        # command client
        self.udp_manager = UDP_Manager(
            callback=self.udp_callback,
            isServer=False,
            ip=self.local_ip,
            port=self.local_port,
            frequency=200,
        )
        self.udp_manager.start()
        # data receiver
        self.udp_mc_manager = UDP_MC_Manager(
            callback=self.udp_callback,
            isSender=False,
            ip=self.server_ip,
            group="224.0.2.100",
            port=60031,
            frequency=200,
        )
        self.udp_mc_manager.start()

        self._suppress_keyboard_interupt_msg()
        self._config_auto_exit()

        self.logger.push_log(logging.INFO, "Client: Start DexHand client.")
        self._in_emg_stop = False

        # hand heart beat pack
        self.ctrl_worker = threading.Thread(
            target=self.hb_sender,
            args=(),
        )
        self.ctrl_worker.setDaemon(True)
        self.ctrl_worker.start()
        self.hb_time = time.time()

    ####################################################################
    #####                                                          #####
    #####              Belows are callback functions.              #####
    #####                                                          #####
    ####################################################################

    def hb_sender(self):
        while True:
            if self._in_emg_stop:
                break
            if self.acquired_hand:
                task_id = self.task_manager.get_task_id()
                self._pack_and_send_msg("Hand", "Acquire", task_id)
                self.hb_time = time.time()
            self.hand_info._watchdog +=1
            if self.hand_info._watchdog >= 10:
                self.logger.push_log(ClientLogger.ERROR, "Client: Timeout. DexHand Server may be not available.")
                self.acquired_hand = False
                raise TimeoutError("DexHand Server may be not available.")
            time.sleep(0.1)

    def udp_callback(self, recvData, recvAddr):
        data = json.loads(recvData)
        if data["Type"] == "Message":
            self.logger.unpack_msg(data)
        elif data["Type"] == "Task":
            self.task_manager.unpack_msg(data)
        elif data["Type"] == "Data":
            self.data_manager.unpack_msg(data)

    ####################################################################
    #####                                                          #####
    #####              Belows are shortcut properties.             #####
    #####                                                          #####
    ####################################################################

    @property
    def tac_info(self):
        return self.data_manager.tac3d_data.tac_info

    @property
    def hand_info(self):
        return self.data_manager.hand_data

    ####################################################################
    #####                                                          #####
    ##### Belows are detailed implementations of all the features. #####
    #####                                                          #####
    ####################################################################

    def start_server(self):
        """
        Start DexHand server.

        Parameters:
        ---
            - None
        """
        self.logger.push_log(logging.INFO, "Client: Try to start DexHand server.")
        task_id = self.task_manager.get_task_id()
        self._pack_and_send_msg("Server", "Start", task_id)
        return self.task_manager.listen_in_task(task_id, "StartServer")
         

    def acquire_hand(self):
        """
        Obtain the control access of DexHand hardware. If the DexHand has not initialized,
        this function will initialize DexHand hardware. The DexHand will find its position
        zero point and calibrate force sensor. Note that before initialization, other hand
        commands will be IGNORED by the server.
        This function may fail if other client is controlling. In that case, the client
        controlling DexHand should release DexHand control access first.

        Parameters:
        ---
            - None
        """
        self.logger.push_log(logging.INFO, "Client: Acquire DexHand control.")
        task_id = self.task_manager.get_task_id()
        self._pack_and_send_msg("Hand", "Acquire", task_id)
        ret = self.task_manager.listen_in_task(task_id, "Acquire")
        self.acquired_hand = self.acquired_hand or ret
        return ret

    def set_home(self, goal_speed: float = 4.0):
        """
        Find DexHand's gripper zero point.

        Parameters:
        ---
            - goal_speed: set home goal speed (in mm/s)
        """
        self._wait_heartbeat()
        self.logger.push_log(logging.INFO, "Client: Set DexHand's position zeropoint.")
        task_id = self.task_manager.get_task_id()
        self._pack_and_send_msg("Hand", "SetHome", task_id, goal_speed=goal_speed)
        return self.task_manager.listen_in_task(task_id, "SetHome")

    def calibrate_force_zero(self):
        """
        Calibrate DexHand's 1D force sensors' zero points.

        Parameter(s):
        ---
            - None
        """
        self._wait_heartbeat()
        self.logger.push_log(logging.INFO, "Client: Calibrate DexHand force zeropoints.")
        task_id = self.task_manager.get_task_id()
        self._pack_and_send_msg("Hand", "CalibrateZero", task_id)
        return self.task_manager.listen_in_task(task_id, "CalibrateZero")

    def contact(
        self,
        contact_speed=8.0,
        preload_force=1.0,
        quick_move_speed=None,
        quick_move_pos=None,
    ):
        """
        Close DexHand's fingers until they contact an object.
        The function will not return until DexHand has indeed contacted an object and set contact force to `preload_force`.
        For a quicker contact, you can specified `quick_move_pos` and `quick_move_speed` so that the gripper will move to `quick_move_pos` in `quick_move_speed` first then try to contact an object in `contact_speed`.

        Parameters:
        ---
            - contact_speed: contact goal speed (in mm/s)
            - preload_force: the force needed when the function return (in N)
            - quick_move_speed: the moving speed when a quick approach is needed (in mm/s). Must be specified with `quick_move_pos` at the same time
            - quick_move_pos: the terminal pos of quick approach (in mm). Must be specified with `quick_move_speed` at the same time
        """
        self._wait_heartbeat()
        task_id = self.task_manager.get_task_id()
        self._pack_and_send_msg(
            "Hand",
            "Contact",
            task_id,
            contact_speed=contact_speed,
            preload_force=preload_force,
            quick_move_speed=quick_move_speed,
            quick_move_pos=quick_move_pos,
        )
        return self.task_manager.listen_in_task(task_id, "Contact")

    def grasp(self, goal_force: float = 5.0, load_time: float = 1.0):
        """
        Control the grasping force of DexHand.
        A linear time-dependent force planning is applied before sending to the driver.

        Before control, DexHand must has contact an object. If not, this function will first make it contact.
        The function will not return until the desired force is reached.

        During preloading, the stiffness will be estimated and used in force control.

        Parameters:
        ---
            - goal_force: desired preload force (in N)
            - load_time: time to load (in s). If set to 0, it means a step signal
        """
        self._wait_heartbeat()
        task_id = self.task_manager.get_task_id()
        self._pack_and_send_msg("Hand", "Grasp", task_id, goal_force=goal_force, load_time=load_time)
        return self.task_manager.listen_in_task(task_id, "Grasp")

    def force_servo(self, goal_force):
        """
        Control the grasping force of DexHand. It's a non-blocking version of `grasp()`.
        There are no force planning, the goal_force will be send to the driver directly.

        Before control, DexHand must has contact an object. If not, this function will first make it contact.
        The function will not return until the desired force is reached.

        During preloading, the stiffness will be estimated and used in force control.

        Parameters:
        ---
            - goal_force: desired grasping force (in N)
        """
        self._wait_heartbeat()
        task_id = self.task_manager.get_task_id()
        self._pack_and_send_msg("Hand", "ForceServo", task_id, goal_force=goal_force)
        return self.task_manager.check_task_copy(task_id, "ForceServo")

    def pos_goto(
        self,
        goal_pos: float,
        max_speed: float = 16.0,
        max_acc: float = 20.0,
        max_f: float = 1.0,
    ):
        """
        Move DexHand's gripper to appointed position.
        If the contact force exceed `max_f`, the gripper will stop immediately with motor maximum deceleration (160 mm/s^2).

        Parameters:
        ---
            - goal_pos: the assigned position (in mm)
            - max_speed: the maximum absolute speed assigned to the gripper when moving (in mm/s)
            - max_acc: the maximum acceleration assigned to the gripper when moving (in mm/s^2)
            - max_f: the maximum force that is allowed when moving (in N)
        """
        self._wait_heartbeat()
        task_id = self.task_manager.get_task_id()
        self._pack_and_send_msg(
            "Hand", "Goto", task_id, goal_pos=goal_pos, max_speed=max_speed, max_acc=max_acc, max_f=max_f
        )
        return self.task_manager.listen_in_task(task_id, "Goto")

    def pos_servo(
        self,
        goal_pos: float,
        max_f: float = 1.0,
    ):
        """
        Move DexHand's gripper to appointed position. It's a non-blocking version of `goto()`.
        If the contact force exceed `max_f`, the gripper will stop immediately with motor maximum deceleration (160 mm/s^2).

        Parameters:
        ---
            - goal_pos: the assigned position (in mm)
            - max_f: the maximum force that is allowed when moving (in N)
        """
        self._wait_heartbeat()
        task_id = self.task_manager.get_task_id()
        self._pack_and_send_msg("Hand", "PosServo", task_id, goal_pos=goal_pos, max_f=max_f)
        return self.task_manager.check_task_copy(task_id, "PosServo")

    def impedance(self, M: float = 1.0, B: float = 0.001, K: float = 0.06, x0: float = 10.0):
        """
        Simulate the Dexhand with as an inpedance system, with mass, damp and spring.

        Parameters:
        ---
            - `M` : mass(kg), nonegative and less than 300
            - `B` : damping(N/(mm/s)), nonegative and less than 0.15
            - `K` : stiffness(N/mm), nonegative and less than 1.5
            - `x0` : the balance point of the spring(mm). betwen 0 and 50.0
        """
        self._wait_heartbeat()
        task_id = self.task_manager.get_task_id()
        self._pack_and_send_msg("Hand", "Impedance", task_id, M=M, B=B, K=K, x0=x0)
        return self.task_manager.check_task_copy(task_id, "Impedance")

    def set_speed(self, goal_speed: float):
        """
        Move DexHand in the assigned speed.

        Parameters:
        ---
        - `goal_speed`: the goal speed that is assigned to DexHand (in mm/s, not greater than 110mm/s)
        """
        self._wait_heartbeat()
        task_id = self.task_manager.get_task_id()
        self._pack_and_send_msg("Hand", "SetSpeed", task_id, goal_speed=goal_speed)
        return self.task_manager.check_task_copy(task_id, "SetSpeed")

    def set_weight_param(self, weightgain1, weightgain2=None):
        """
        TODO

        Parameters:
        ---
            - TODO
        """
        self._wait_heartbeat()
        if weightgain2 is None:
            weightgain2 = weightgain1
        self.logger.push_log(logging.INFO, "Client: Calibrate DexHand force zeropoints.")
        task_id = self.task_manager.get_task_id()
        self._pack_and_send_msg("Hand", "SetWeightParam", task_id, weightgain1=weightgain1, weightgain2=weightgain2)
        return self.task_manager.listen_in_task(task_id, "SetWeightParam")

    def set_pid_param(self, Kp=1, Ki=0.0016, maxi=60):
        """
        TODO

        Parameters:
        ---
            - TODO
        """
        self._wait_heartbeat()
        self.logger.push_log(logging.INFO, "Client: Setting DexHand force PID parameters.")
        task_id = self.task_manager.get_task_id()
        self._pack_and_send_msg("Hand", "SetPIDParam", task_id, Kp=Kp, Ki=Ki, maxi=maxi)
        return self.task_manager.check_task_copy(task_id, "SetPIDParam")

    def switch_k_mode(self, use_estimator: bool, default_k: float = 0.04):
        """
        TODO

        Parameters:
        ---
            - TODO
        """
        self._wait_heartbeat()
        self.logger.push_log(logging.INFO, "Client: Switch stiffness estimation mode.")
        task_id = self.task_manager.get_task_id()
        self._pack_and_send_msg("Hand", "SwitchKMode", task_id, use_estimator=use_estimator, default_k=default_k)
        return self.task_manager.check_task_copy(task_id, "SwitchKMode")

    def halt(self):
        """
        Stop the gripper. Can interrupt all hand movement command.
        This command will clean all unfinished task in queue.
        This command can be send by ANY client.

        Parameters:
        ---
            - None
        """
        self.logger.push_log(logging.INFO, "Client: Halt DexHand.")
        task_id = self.task_manager.get_task_id()
        self._pack_and_send_msg("Hand", "Halt", task_id)
        return self.task_manager.listen_in_task(task_id, "Halt")

    def clear_hand_error(self):
        """
        When DexHand is in error, call this function to try to clear error.
        DexHand will not accept any other command until the error is cleared.
        use hand_info.error_flag to check if DexHand is in error.

        Parameters:
        ---
            - None
        """
        self._wait_heartbeat()
        self.logger.push_log(logging.INFO, "Client: Clear Hand error signal.")
        task_id = self.task_manager.get_task_id()
        self._pack_and_send_msg("Hand", "ClearError", task_id)
        return self.task_manager.check_task_copy(task_id, "ClearError")

    def release_hand(self):
        """
        Release the control of DexHand.
        Then other client can call `acquire_hand()` to acquire control.

        Parameters:
        ---
            - None
        """
        if self.acquired_hand == False:
            self.logger.push_log(logging.WARNING, "Client has not acquired DexHand control access.")
            return
        self._wait_heartbeat()
        self.logger.push_log(logging.WARNING, "Client: Release DexHand.")
        task_id = self.task_manager.get_task_id()
        self._pack_and_send_msg("Hand", "Release", task_id)
        ret = self.task_manager.listen_in_task(task_id, "Release")
        self.acquired_hand = not ret
        return ret

    def stop_server(self):
        """
        Stop DexHand server. Will call `halt()` and `release_hand()` internally.

        Parameters:
        ---
            - None
        """
        self.logger.push_log(logging.INFO, "Client: Stop DexHand and server.")
        task_id = self.task_manager.get_task_id()
        self._pack_and_send_msg("Server", "Stop", task_id)
        return self.task_manager.listen_in_task(task_id, "Stop")

    ####################################################################
    #####                                                          #####
    #####               Belows are private functions.              #####
    #####                                                          #####
    ####################################################################

    def _suppress_keyboard_interupt_msg(self):
        old_excepthook = sys.excepthook

        def new_hook(exctype, value, traceback):
            if exctype != KeyboardInterrupt:
                self.logger.push_log(ClientLogger.CRITICAL, f"Client: FATAL ERROR OCCUR({exctype.__name__})")
                self._emergency_exit_func()
                old_excepthook(exctype, value, traceback)

        sys.excepthook = new_hook

    def _config_auto_exit(self):
        import sys
        import atexit

        atexit.register(self._emergency_exit_func)

        if sys.platform == "linux":
            import signal

            signal.signal(signal.SIGTERM, self._emergency_exit_func)
            signal.signal(signal.SIGINT, self._emergency_exit_func)
            signal.signal(signal.SIGHUP, self._emergency_exit_func)
        else:
            import time
            import ctypes
            from ctypes import wintypes

            _HandlerRoutine = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.DWORD)

            CTRL_C_EVENT = 0
            CTRL_BREAK_EVENT = 1
            CTRL_CLOSE_EVENT = 2

            def ctrl_handler(ctrl_type):
                if ctrl_type in (CTRL_C_EVENT, CTRL_BREAK_EVENT, CTRL_CLOSE_EVENT):
                    self._emergency_exit_func()
                    return False

                return False

            self._ctrl_handler = _HandlerRoutine(ctrl_handler)
            kernel32 = ctypes.windll.kernel32
            if not kernel32.SetConsoleCtrlHandler(self._ctrl_handler, True):
                raise ctypes.WinError(ctypes.get_last_error())

    def _emergency_exit_func(self, signum=0, frame=None):
        import os
        self.logger.push_log(ClientLogger.INFO, "Client: exiting program.")
        if not self.acquired_hand or self._in_emg_stop:
            return
        self._in_emg_stop = True
        self.task_manager._need_popout = True
        time.sleep(0.005)
        self.task_manager._need_popout = False
        self.halt()
        self.release_hand()
        self.task_manager._need_popout = True
        os._exit(0)

    def _pack_and_send_msg(self, device, cmd_type, task_id, **kwargs):
        if self._in_emg_stop and not cmd_type in ["Halt", "Release"]:
            self.logger.push_log(
                ClientLogger.WARNING, f"Client: the task {cmd_type} is aborted since program is halting."
            )
            return
        command = {
            "Time": time.time(),
            "Command": {
                "Device": device,
                "Type": cmd_type,
                "args": kwargs,
                "TaskID": task_id,
            },
        }
        msg_data = json.dumps(command)
        self.udp_manager.send(msg_data.encode(), self.goal_addr)

    def _wait_heartbeat(self):
        if self.acquired_hand:
            while time.time() - self.hb_time > 0.5:
                time.sleep(0.01)


if __name__ == "__main__":
    client = DexHandClient(ip="192.168.2.100", port=60031)
    client.start_server()
