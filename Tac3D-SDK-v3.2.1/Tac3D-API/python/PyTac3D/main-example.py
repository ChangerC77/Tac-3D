import PyTac3D
import time


print('PyTac3D version is :', PyTac3D.PYTAC3D_VERSION)

# 传感器SN
# Serial Number of the Tac3D sensor
SN = ''

# 帧序号
# frame index
frameIndex = -1 


# 时间戳
# timestamp
sendTimestamp = 0.0
recvTimestamp = 0.0

# 用于存储三维形貌、三维变形场、三维分布力、三维合力、三维合力矩数据的矩阵
# Mat for storing point cloud, displacement field, distributed force, resultant force, and resultant moment
P, D, F, Fr, Mr = None, None, None, None, None


# 编写用于接收数据的回调函数
# "param"是初始化Sensor类时传入的自定义参数
# Write a callback function to receive data
# "param" is the custom parameter passed in when initializing the Sensor object
def Tac3DRecvCallback(frame, param):
    global SN, frameIndex, sendTimestamp, recvTimestamp, P, D, F
    
    print()

    # 显示自定义参数
    # print the custom parameter
    print(param)

    # 获得传感器SN码，可用于区分触觉信息来源于哪个触觉传感器
    # get the SN code, which can be used to distinguish which Tac3D sensor the tactile information comes from
    SN = frame['SN']
    print(SN)
    
    # 获得帧序号
    # get the frame index
    frameIndex = frame['index']
    print(frameIndex)
    
    # 获得时间戳
    # get the timestamp
    sendTimestamp = frame['sendTimestamp']
    recvTimestamp = frame['recvTimestamp']

    # 使用frame.get函数通过数据名称"3D_Positions"获得numpy.array类型的三维形貌数据
    # 矩阵的3列分别为x,y,z方向的分量
    # 矩阵的每行对应一个测量点
    # Use the frame.get function to obtain the 3D shape in the numpy.array type through the data name "3D_Positions"
    # The three columns of the matrix are the components in the x, y, and z directions, respectively
    # Each row of the matrix corresponds to a sensing point
    P = frame.get('3D_Positions')

    # 使用frame.get函数通过数据名称"3D_Displacements"获得numpy.array类型的三维变形场数据
    # 矩阵的3列分别为x,y,z方向的分量
    # 矩阵的每行对应一个测量点
    # Use the frame.get function to obtain the displacement field in the numpy.array type through the data name "3D_Displacements"
    # The three columns of the matrix are the components in the x, y, and z directions, respectively
    # Each row of the matrix corresponds to a sensing point
    D = frame.get('3D_Displacements')

    # 使用frame.get函数通过数据名称"3D_Forces"获得numpy.array类型的三维分布力数据
    # 矩阵的3列分别为x,y,z方向的分量
    # 矩阵的每行对应一个测量点
    # Use the frame.get function to obtain the distributed force in the numpy.array type through the data name "3D_Forces"
    # The three columns of the matrix are the components in the x, y, and z directions, respectively
    # Each row of the matrix corresponds to a sensing point
    F = frame.get('3D_Forces')

    # 使用frame.get函数通过数据名称"3D_ResultantForce"获得numpy.array类型的三维合力的数据指针
    # 矩阵的3列分别为x,y,z方向的分量
    # Use the frame.get function to obtain the resultant force in the numpy.array type through the data name "3D_ResultantForce"
    # The three columns of the matrix are the components in the x, y, and z directions, respectively
    Fr = frame.get('3D_ResultantForce')

    # 使用frame.get函数通过数据名称"3D_ResultantMoment"获得numpy.array类型的三维合力的数据指针
    # 矩阵的3列分别为x,y,z方向的分量
    # Use the frame.get function to obtain the resultant moment in the numpy.array type through the data name "3D_ResultantMoment"
    # The three columns of the matrix are the components in the x, y, and z directions, respectively
    Mr = frame.get('3D_ResultantMoment')

# Create a Sensor object, set the callback function to Tac3DRecvCallback, and set the UDP receive port to 9988
# The Tac3DRecvCallback function will be automatically called every time a data frame is received
tac3d = PyTac3D.Sensor(recvCallback=Tac3DRecvCallback, port=9988, maxQSize=5, callbackParam = 'test param')

# 等待Tac3D传感器启动并传来数据
# Wait for the Tac3D sensor to start and send data
tac3d.waitForFrame()

# 5s
time.sleep(5)

# 发送一次校准信号（应确保校准时传感器未与任何物体接触）
# Send a calibration signal to reset zero point (please ensure that the sensor is not in contact with any object during calibration)
tac3d.calibrate(SN)

#5s
time.sleep(5)

# PyTac3D提供获取frame的另一种方式：通过getFrame获取缓存队列中的frame
# 这种方式的使用更为灵活简便，但缓存队列的长度可能影响采集数据的实时性
# 缓存队列的最大长度通过maxQSize设置
# PyTac3D provides another way to get the frame：get the frame in the cache queue through the getFrame function
# This method is more flexible and convenient to use, but the length of the cache queue may affect the real-time performance.
# The maximum length of the cache queue is set by maxQSize
frame = tac3d.getFrame()
if not frame is None:
    print(frame['SN'])

#5s
time.sleep(5)

