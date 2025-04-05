from dexhand_client import DexHandClient
import numpy as np
import sys
# 将子目录添加到模块搜索路径中
sys.path.append("..")
from examples import PyTac3D

class Tac3D_info:
    def __init__(self,SN):
        self.SN = SN # 传感器 SN
        self.frameIndex = -1 # 帧序号
        self.sendTimestamp = None # 时间戳
        self.recvTimestamp = None # 时间戳
        self.P = np.zeros((400,3)) # 三维形貌测量结果，400 行分别对应 400 个标志点，3 列分别为各标志点的 x，y 和 z 坐标
        self.D = np.zeros((400,3)) # 三维变形场测量结果，400 行分别对应 400个标志点，3 列分别为各标志点的 x，y 和 z 变形
        self.F = np.zeros((400,3)) # 三维分布力场测量结果，400 行分别对应400 个标志点，3 列分别为各标志点的 x，y 和 z 受力
        self.Fr = np.zeros((1,3)) # 整个传感器接触面受到的 x,y,z 三维合力
        self.Mr = np.zeros((1,3)) # 整个传感器接触面受到的 x,y,z 三维合力矩