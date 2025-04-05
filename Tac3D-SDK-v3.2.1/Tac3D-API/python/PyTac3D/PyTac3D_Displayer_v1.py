from dexhand_client import DexHandClient
import PyTac3D
import ruamel.yaml
import vedo
import numpy as np

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


mesh_table = { 'A1': (20,20),
               'AD2': (20,20),
               'HDL1': (20,20),
               'DM1': (20,20),
               'DS1': (16,16),
               'DSt1': (16,16),
               'B1': (16,16),
               'UNKNOWN': (20,20),
               }

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
        self.Tac3D_name1 = "HDL1-0003"
        self.Tac3D_name2 = "HDL1-0004"
        self.tacinfo1 = Tac3D_info(self.Tac3D_name1)
        self.tacinfo2 = Tac3D_info(self.Tac3D_name2)
        self.tac_dict = {self.Tac3D_name1: self.tacinfo1, self.Tac3D_name2: self.tacinfo2}
        self.Tac3DSensor = PyTac3D.Sensor(recvCallback=self._recvCallback, port=port, maxQSize=5, callbackParam=self.tac_dict)
        self.SN = ''
        self.SN_list = []
        self.frameCacheLeft = {}
        self.frameCacheRight = {}
        self.updateFlag = True
        
        self._plotter = vedo.Plotter(N=4)
        
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

        # self._sensor_SN = vedo.Text2D('SN: None', s=1)
                
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
        tacinfo=param[SN]
        frameIndex = frame["index"] 
        tacinfo.frameIndex = frameIndex
        sendTimestamp = frame["sendTimestamp"]
        recvTimestamp = frame["recvTimestamp"]
        tacinfo.sendTimestamp = sendTimestamp
        tacinfo.recvTimestamp = recvTimestamp
        P = frame.get("3D_Positions")
        tacinfo.P = P
        D = frame.get("3D_Displacements")
        tacinfo.D = D
        F = frame.get("3D_Forces")
        tacinfo.F = F
        Fr = frame.get("3D_ResultantForce")
        tacinfo.Fr = Fr
        Mr = frame.get("3D_ResultantMoment")
        tacinfo.Mr = Mr
        if SN=="HDL1-0003":
           self.frameCacheLeft[recvTimestamp] = frame
        else :  
            self.frameCacheRight[recvTimestamp] = frame 
        self.SN=SN
        if not SN in self.SN_list:
            self.SN_list.append(SN)
            print('Sensor {} connected !'.format(SN))
    
    def Run(self):
        for i in range(4):
            self._plotter.at(i).add(self._box, self._axs)
            self._plotter.at(i).show()
        self._timerevt = self._plotter.add_callback('timer', self._ShowFrame)
        self._timer_id = self._plotter.timer_callback('create', dt=10)

        self._plotter.interactive().close()
        
    def _ShowFrame(self, event):
        # if self.SN != '':
                # 确保左右手数据可用
        if self.frameCacheLeft and self.frameCacheRight:
            latest_timestamp_left = max(self.frameCacheLeft.keys())
            frame_left = self.frameCacheLeft[latest_timestamp_left]

            latest_timestamp_right = max(self.frameCacheRight.keys())
            frame_right = self.frameCacheRight[latest_timestamp_right]

            # 提取左手数据
            L_left = frame_left.get('3D_Positions')
            D_left = frame_left.get('3D_Displacements')
            F_left = frame_left.get('3D_Forces')

            # 提取右手数据
            L_right = frame_right.get('3D_Positions')
            D_right = frame_right.get('3D_Displacements')
            F_right = frame_right.get('3D_Forces')
            
            print('----------------LEFT-----------------')
            print("\nP: ",L_left)
            print("\nD: ",D_left)
            print("\nF: ",F_left)
            print("\nTimeStamp: ",frame_left["recvTimestamp"])
            print('----------------RIGHT-----------------')
            print("\nP: ",L_right)
            print("\nD: ",D_right)
            print("\nF: ",F_right)
            print("\nTimeStamp: ",frame_right["recvTimestamp"])
            print("\nnext frame\n")


            for i in range(4):
                self._plotter.at(i).clear()
                self._plotter.at(i).add(self._box, self._axs)
            # self._plotter.at(i0).clear()
            # self._plotter.at(i0).add(self._box, self._axs)
            # self._plotter.at(i1).clear()
            # self._plotter.at(i1).add(self._box, self._axs)
            
            # 处理左手数据 (窗口 0, 2)
            if L_left is not None:
                meshSize = mesh_table[getModelName("HDL1-0003")]
                self._GenConnect(*meshSize)
                mesh_left = vedo.Mesh([L_left, self._connect], alpha=0.9, c=[150, 150, 230])
                if self._enable_Mesh0:
                    self._plotter.at(0).add(mesh_left)
                    self._plotter.at(1).add(mesh_left)

                if self._enable_Displacements and D_left is not None:
                    arrsD_left = vedo.Arrows(list(L_left), list(L_left + D_left * self._scaleD), s=2)
                    self._plotter.at(0).add(arrsD_left)
                    # self._plotter.at(1).add(arrsD_left)

                if self._enable_Forces and F_left is not None:
                    arrsF_left = vedo.Arrows(list(L_left), list(L_left + F_left * self._scaleF), s=2)
                    # self._plotter.at(0).add(arrsF_left)
                    self._plotter.at(1).add(arrsF_left)

            # 处理右手数据 (窗口 1, 3)
            if L_right is not None:
                meshSize = mesh_table[getModelName("HDL1-0004")]
                self._GenConnect(*meshSize)
                mesh_right = vedo.Mesh([L_right, self._connect], alpha=0.9, c=[230, 150, 150])
                if self._enable_Mesh1:
                    self._plotter.at(2).add(mesh_right)
                    self._plotter.at(3).add(mesh_right)

                if self._enable_Displacements and D_right is not None:
                    arrsD_right = vedo.Arrows(list(L_right), list(L_right + D_right * self._scaleD), s=2)
                    self._plotter.at(2).add(arrsD_right)
                    # self._plotter.at(3).add(arrsD_right)

                if self._enable_Forces and F_right is not None:
                    arrsF_right = vedo.Arrows(list(L_right), list(L_right + F_right * self._scaleF), s=2)
                    # self._plotter.at(2).add(arrsF_right)
                    self._plotter.at(3).add(arrsF_right)
            
            # if not L is None:
            #     if self.updateFlag:
            #         meshSize = mesh_table[getModelName(self.SN)]
            #         self._GenConnect(*meshSize)
            #     mesh = vedo.Mesh([L, self._connect], alpha=0.9, c=[150,150,230])
            #     if self._enable_Mesh0:
            #         # self._plotter.at(i0).add(mesh)
            #         self._plotter.at(0).add(mesh)
            #         self._plotter.at(2).add(mesh)

            #     if self._enable_Displacements and not D is None:
            #         arrsD = vedo.Arrows(list(L), list(L+D*self._scaleD), s=2)
            #         self._plotter.at(0).add(arrsD)
            #         self._plotter.at(2).add(arrsD)

            #         # self._plotter.at(i0).add(arrsD)
            #     if self._enable_Mesh1:
            #         self._plotter.at(1).add(mesh)
            #         self._plotter.at(3).add(mesh)

            #         # self._plotter.at(i1).add(mesh)
            #     if self._enable_Forces and not F is None:
            #         arrsF = vedo.Arrows(list(L), list(L+F*self._scaleF), s=2)
            #         self._plotter.at(3).add(arrsF)
            #         self._plotter.at(1).add(arrsF)
            #         # self._plotter.at(i1).add(arrsF)

            
            # refPoint = frame.get('3D_refPoints_P')

            # if not refPoint is None:
            #     if self._refPoints_org is None:
            #         self._refPoints_org = refPoint
                    
            #     refP = vedo.Points(refPoint, c=[0,0,0])
            #     refP0 = vedo.Points(self._refPoints_org, c=[255,0,0])
            #     self._plotter.at(0).add(refP, refP0)
            #     self._plotter.at(2).add(refP, refP0)
            #     # self._plotter.at(i0).add(refP, refP0)

            
            # if not self._recvFirstFrame:
            #     self._recvFirstFrame = True
            #     self._plotter.reset_camera()

            # self._plotter.at(i0).render()
            # self._plotter.at(i1).render()
            self._plotter.at(0).render()
            self._plotter.at(1).render()
            self._plotter.at(2).render()
            self._plotter.at(3).render()
    
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
            idx = self.SN_list.index(self.SN)
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
