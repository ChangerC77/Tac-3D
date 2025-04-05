#! /usr/bin/python3
from dexhand_client import DexHandClient
import numpy as np
import PyTac3D
import time

# 用于存储Tac3D的测量结果
class Tac3D_info:
    def __init__(self, SN):
        self.SN = SN  # 传感器SN
        self.frameIndex = -1  # 帧序号
        self.sendTimestamp = None  # 时间戳
        self.recvTimestamp = None  # 时间戳
        self.P = np.zeros((400, 3))  # 三维形貌测量结果，400行分别对应400个标志点，3列分别为各标志点的x，y和z坐标
        self.D = np.zeros((400, 3))  # 三维变形场测量结果，400行分别对应400个标志点，3列分别为各标志点的x，y和z变形
        self.F = np.zeros((400, 3))  # 三维分布力场测量结果，400行分别对应400个标志点，3列分别为各标志点的x，y和z受力
        self.Fr = np.zeros((1, 3))  # 整个传感器接触面受到的x,y,z三维合力
        self.Mr = np.zeros((1, 3))  # 整个传感器接触面受到的x,y,z三维合力矩


if __name__ == "__main__":

    # Tac3D的回调函数，当传感器启动后，每次返回数据时均会执行该函数
    def Tac3DRecvCallback(frame, param):
        # 获取SN
        SN = frame["SN"]  # 由于机械手上安装了两个Tac3D传感器，通过SN号确定究竟是哪个Tac3D调用了该回调函数
        #print("SN: ",SN)
        #print("Next frame\n")
        tacinfo = param[SN]  # 由于机械手上安装了两个Tac3D传感器，通过SN号确定究竟是哪个Tac3D调用了该回调函数

        # 获取帧序号
        frameIndex = frame["index"]
        tacinfo.frameIndex = frameIndex

        # 获取时间戳
        sendTimestamp = frame["sendTimestamp"]
        recvTimestamp = frame["recvTimestamp"]
        tacinfo.sendTimestamp = sendTimestamp
        tacinfo.recvTimestamp = recvTimestamp

        # 获取标志点三维形貌
        # P矩阵（numpy.array）为400行3列，400行分别对应400个标志点，3列分别为各标志点的x，y和z坐标
        P = frame.get("3D_Positions")
        tacinfo.P = P

        # 获取标志点三维位移场
        # D矩阵为（numpy.array）400行3列，400行分别对应400个标志点，3列分别为各标志点的x，y和z位移
        D = frame.get("3D_Displacements")
        tacinfo.D = D

        # 获取三维分布力
        # F矩阵为（numpy.array）400行3列，400行分别对应400个标志点，3列分别为各标志点附近区域所受的x，y和z方向力
        F = frame.get("3D_Forces")
        tacinfo.F = F

        # 获得三维合力
        # Fr矩阵为1x3矩阵，3列分别为x，y和z方向合力
        Fr = frame.get("3D_ResultantForce")
        tacinfo.Fr = Fr

        # 获得三维合力矩
        # Mr矩阵为1x3矩阵，3列分别为x，y和z方向合力矩
        Mr = frame.get("3D_ResultantMoment")
        tacinfo.Mr = Mr

    # 机械手的回调函数，当机械手启动后，每次返回数据时均会执行该函数
    def HandRecvCallback(client: DexHandClient):
        info = client.hand_info
        if info._frame_cnt % 10 == 0:
            print(
                f"Error:{info.error_flag}, nowforce1: {info.now_force[0]:.3f}N nowforce2: {info.now_force[1]:.3f}N nowTacFz1: {tacinfo1.Fr[0][2]:.3f}N nowTacFz2: {tacinfo2.Fr[0][2]:.3f}N nowpos: {info.now_pos:.3f}mm",
                end=" ",
            )
            if info.now_task in ["GOTO", "POSSERVO"]:
                print(f"goalpos : {info.goal_pos:.2f}")
            elif info.now_task in ["SETFORCE", "FORCESERVO"]:
                print(f"goalforce : {info.goal_force:.2f}")
            else:
                print()

    # 创建机械手客户端
    client = DexHandClient(ip="192.168.2.100", port=60031, recvCallback_hand=HandRecvCallback)
    # 创建传感器数据存储实例
    Tac3D_name1 = "HDL1-0003"# 注意，'HDL1-0001'仅是举例，用户使用时请改成DexHand机械手上实际的Tac3D传感器编号
    Tac3D_name2 = "HDL1-0004"# 注意，'HDL1-0002'仅是举例，用户使用时请改成DexHand机械手上实际的Tac3D传感器编号
    tacinfo1 = Tac3D_info(Tac3D_name1)
    tacinfo2 = Tac3D_info(Tac3D_name2)
    tac_dict = {Tac3D_name1: tacinfo1, Tac3D_name2: tacinfo2}
    # 创建传感器实例，设置回调函数为上面写好的Tac3DRecvCallback，设置UDP接收端口为9988，数据帧缓存队列最大长度为5
    tac3d = PyTac3D.Sensor(recvCallback=Tac3DRecvCallback, port=9988, maxQSize=5, callbackParam=tac_dict)
    # 启动机械手
    client.start_server()  # 启动机械手和Tac3D，此后Tac3D开始进行测量，每传回一帧数据时就执行一次回调函数Tac3DRecvCallback
    client.acquire_hand()  # 获取机械手控制权限
    # 机械手零点校正
    client.set_home()  # 位置零点
    client.calibrate_force_zero()  # 力零点（一维力传感器）
    # 发送一次校准信号（应确保校准时传感器未与任何物体接触！否则会输出错误的数据！）
    tac3d.calibrate(Tac3D_name1)
    tac3d.calibrate(Tac3D_name2)
    # 接触并施加抓取力
    # client.contact(contact_speed=8, preload_force=2, quick_move_speed=15, quick_move_pos=10)
    # client.grasp(goal_force=5.0, load_time=5.0)
    # time.sleep(10)
    # # 解除机械手控制权限
    # client.release_hand()