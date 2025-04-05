import PyTac3D
from dexhand_client import DexHandClient
import ruamel.yaml
import vedo
import numpy as np
import time

mesh_table = { 'A1': (20,20),
               'AD2': (20,20),
               'HDL1': (20,20),
               'DM1': (20,20),
               'DS1': (16,16),
               'DSt1': (16,16),
               'B1': (16,16),
               'UNKNOWN': (20,20),
               }
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

def getModelName(SN):
    model = SN.split('-')[0]
    if model[0] == 'Y':
        model = model[1:]

    if model in mesh_table.keys():
        return model
    else:
        return 'UNKNOWN'

class Tac3D_Displayer:
    
    def __init__(self, port=9988):
        self._scaleF = 30 * 1
        self._scaleD = 5 * 1
        self._connect = None
        self._recvFirstFrame = False
        self.Tac3D_name1 = "HDL1-0003"# 注意，'HDL1-0001'仅是举例，用户使用时请改成DexHand机械手上实际的Tac3D传感器编号
        self.Tac3D_name2 = "HDL1-0004"# 注意，'HDL1-0002'仅是举例，用户使用时请改成DexHand机械手上实际的Tac3D传感器编号
        self.tacinfo1 = Tac3D_info(self.Tac3D_name1)
        self.tacinfo2 = Tac3D_info(self.Tac3D_name2)
        self.tac_dict = {self.Tac3D_name1: self.tacinfo1, self.Tac3D_name2: self.tacinfo2}
        self.Tac3DSensor = PyTac3D.Sensor(recvCallback=self._recvCallback, port=port, maxQSize=1,callbackParam=self.tac_dict)
        self.SN = ''
        self.SN_list = []
        self.frameCache = {}
        self.updateFlag = True
        
        self.frames_data = {} # collect data from each frame
        
        self._plotter = vedo.Plotter(N=2)
        
        self._box = vedo.Box(pos=(0,0,0), length=16, width=16, height=8).alpha(0.03)
        self._axs = vedo.Axes(self._box, c='k', xygrid=False)  # returns an Assembly object

        self._enable_Mesh0 = True
        self._enable_Displacements = True
        self._enable_Mesh1 = True
        self._enable_Forces = True

        self._refPoints_org = None

        self._button_calibrate = self._plotter.at(1).add_button(
                    self._ButtonFunc_Calibrate,
                    states=["calibrate"],
                    font="Kanopus",
                    pos=(0.7, 0.9),
                    size=32,
                )
        self._button_switch = self._plotter.at(1).add_button(
                    self._ButtonFunc_Switch,
                    states=["switch sensor"],
                    font="Kanopus",
                    pos=(0.2, 0.9),
                    size=32,
                )

        self._sensor_SN = vedo.Text2D('SN: None', s=1)
                
        self._button_mesh0 = self._plotter.at(0).add_button(
                    self._ButtonFunc_Mesh0,
                    states=["\u23F8 Geometry","\u23F5 Geometry"],
                    font="Kanopus",
                    pos=(0.3, 0.05),
                    size=32,
                )
        self._button_displacements = self._plotter.at(0).add_button(
                    self._ButtonFunc_Displacements,
                    states=["\u23F8 Displacements","\u23F5 Displacements"],
                    font="Kanopus",
                    pos=(0.7, 0.05),
                    size=32,
                )
                
        self._button_mesh1 = self._plotter.at(1).add_button(
                    self._ButtonFunc_Mesh1,
                    states=["\u23F8 Geometry","\u23F5 Geometry"],
                    font="Kanopus",
                    pos=(0.3, 0.05),
                    size=32,
                )
        self._button_force = self._plotter.at(1).add_button(
                    self._ButtonFunc_Forces,
                    states=["\u23F8 Forces","\u23F5 Forces"],
                    font="Kanopus",
                    pos=(0.7, 0.05),
                    size=32,
                )
        
    def _recvCallback(self, frame, param):
        SN = frame['SN']
        self.frameCache[SN] = frame
        if not SN in self.SN_list:
            if len(self.SN_list) == 0:
                self.SN = SN
                self.updateFlag = True
                self._sensor_SN.text('SN: ' + self.SN)
            self.SN_list.append(SN)
            print('Sensor {} connected !'.format(SN))
        print("self.SN_list: ",self.SN_list)
        print("Next loop\n")
        # time.sleep(120)
    
    def Run(self):
        self._plotter.at(0).show(self._sensor_SN)
        self._plotter.at(0).show()
        self._plotter.at(1).show()
        self._timerevt = self._plotter.add_callback('timer', self._ShowFrame)
        self._timer_id = self._plotter.timer_callback('create', dt=10)
        self._plotter.interactive().close()
        
    def _ShowFrame(self, event):
        if self.SN != '': #此时self.SN_list中有两个sensor,遍历获取信息即可
            # print("self.SN_list: ",self.SN_list)
            # print("self.SN: ",self.SN)
            # time.sleep(120)
            frame = self.frameCache[self.SN]
            
            frameIndex = frame["index"]
                    
            L = frame.get('3D_Positions')
            D = frame.get('3D_Displacements')
            F = frame.get('3D_Forces')
            Fr = frame.get("3D_ResultantForce")
            Mr = frame.get("3D_ResultantMoment")
            data_dict = {
                "3D_Positions": L,
                "3D_Displacements": D,
                "3D_Forces": F,
                "3D_ResultantForce": Fr,
                "3D_ResultantMoment": Mr
            }
            self.frames_data[frameIndex] = data_dict

            # # 打印字典中各个数据的内容
            # print("\n-------------------3D_Positions----------------------------\n")
            # # print(data_dict["3D_Positions"][0:50, :])
            # print(self.frames_data[frameIndex]["3D_Positions"])
            # print("\n-------------------3D_Displacements------------------------\n")
            # print(self.frames_data[frameIndex]["3D_Displacements"])
            # print("\n-------------------3D_Forces-------------------------------\n")
            # print(self.frames_data[frameIndex]["3D_Forces"])
            # print("\n-------------------3D_ResultantForce-----------------------\n")
            # print(self.frames_data[frameIndex]["3D_ResultantForce"])
            # print("\n-------------------3D_ResultantMoment----------------------\n")
            # print(self.frames_data[frameIndex]["3D_ResultantMoment"])


            self._plotter.at(0).clear()
            self._plotter.at(0).add(self._box, self._axs)
            self._plotter.at(1).clear()
            self._plotter.at(1).add(self._box, self._axs)
            if not L is None:
                if self.updateFlag:
                    meshSize = mesh_table[getModelName(self.SN)]
                    self._GenConnect(*meshSize)
                mesh = vedo.Mesh([L, self._connect], alpha=0.9, c=[150,150,230])
                if self._enable_Mesh0:
                    self._plotter.at(0).add(mesh)
                if self._enable_Displacements and not D is None:
                    arrsD = vedo.Arrows(list(L), list(L+D*self._scaleD), s=2)
                    self._plotter.at(0).add(arrsD)
                if self._enable_Mesh1:
                    self._plotter.at(1).add(mesh)
                if self._enable_Forces and not F is None:
                    arrsF = vedo.Arrows(list(L), list(L+F*self._scaleF), s=2)
                    self._plotter.at(1).add(arrsF)
            
            refPoint = frame.get('3D_refPoints_P')

            if not refPoint is None:
                if self._refPoints_org is None:
                    self._refPoints_org = refPoint
                    
                refP = vedo.Points(refPoint, c=[0,0,0])
                refP0 = vedo.Points(self._refPoints_org, c=[255,0,0])
                self._plotter.at(0).add(refP, refP0)
            
            if not self._recvFirstFrame:
                self._recvFirstFrame = True
                self._plotter.reset_camera()

            self._plotter.at(0).render()
            self._plotter.at(1).render()
    
    def _GenConnect(self, nx, ny):
        self._connect = []
        for iy in range(ny-1):
            for ix in range(nx-1):
                idx = iy * nx + ix
                self._connect.append([idx, idx+1, idx+nx])
                self._connect.append([idx+nx+1, idx+nx, idx+1])
        
    def _ButtonFunc_Calibrate(self):
        if self.SN != '':
            self.Tac3DSensor.calibrate(self.SN)

    def _ButtonFunc_Switch(self):
        if self.SN in self.SN_list:
            # 获取self.SN在SN_list中索引
            idx = self.SN_list.index(self.SN)
            # 切换到下一个SN
            idx = (idx+1) % len(self.SN_list)
            self.SN = self.SN_list[idx]
            self.updateFlag = True
            self._sensor_SN.text('SN: ' + self.SN)
        
    def _ButtonFunc_Mesh0(self):
        self._button_mesh0.switch()
        self._enable_Mesh0 = not self._enable_Mesh0
        
    def _ButtonFunc_Displacements(self):
        self._button_displacements.switch()
        self._enable_Displacements = not self._enable_Displacements
        
    def _ButtonFunc_Mesh1(self):
        self._button_mesh1.switch()
        self._enable_Mesh1 = not self._enable_Mesh1
        
    def _ButtonFunc_Forces(self):
        self._button_force.switch()
        self._enable_Forces = not self._enable_Forces
    
if __name__ == '__main__':
    import sys
    if len(sys.argv) == 2:
        port = int(sys.argv[1])
    else:
        port = 9988

    displayer = Tac3D_Displayer(port)
    displayer.Run()
