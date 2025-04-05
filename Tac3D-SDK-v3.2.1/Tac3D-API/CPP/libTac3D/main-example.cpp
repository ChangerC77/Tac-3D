#include "libTac3D.hpp" // 引用头文件


cv::Mat P, D, F, Fr, Mr; // 用于存储三维形貌、三维变形场、三维分布力、三维合力、三维合力矩数据的矩阵
int frameIndex;  // 帧序号
double sendTimestamp, recvTimestamp; // 时间戳
std::string SN;  // 传感器SN


void Tac3DRecvCallback(Tac3D::Frame &frame, void *param)
{
    cv::Mat *tempMat;
    float *testParam = (float*)param;  // 接收自定义参数
    SN = frame.SN;  // 获得传感器SN码，可用于区分触觉信息来源于哪个触觉传感器
    frameIndex = frame.index;  // 获得帧序号
    sendTimestamp = frame.sendTimestamp;  // 获得发送时间戳
    recvTimestamp = frame.recvTimestamp;  // 获得接收时间戳
    
    // 使用frame.get函数通过数据名称"3D_Positions"获得cv::Mat类型的三维形貌的数据指针
    tempMat = frame.get<cv::Mat>("3D_Positions");
    tempMat->copyTo(P); // 务必先将获得的数据拷贝到自己的变量中再使用（注意，OpenCV的Mat中数据段和矩阵头是分开存储的，因此需要使用copyTo同时复制矩阵的矩阵头和数据段，而不应当用=符号赋值）

    // 使用frame.get函数通过数据名称"3D_Displacements"获得cv::Mat类型的三维变形场的数据指针
    tempMat = frame.get<cv::Mat>("3D_Displacements");
    tempMat->copyTo(D); // 务必先将获得的数据拷贝到自己的变量中再使用

    // 使用frame.get函数通过数据名称"3D_Forces"获得cv::Mat类型的三维分布力的数据指针
    tempMat = frame.get<cv::Mat>("3D_Forces");
    tempMat->copyTo(F); // 务必先将获得的数据拷贝到自己的变量中再使用

    // 使用frame.get函数通过数据名称"3D_ResultantForce"获得cv::Mat类型的三维合力的数据指针
    tempMat = frame.get<cv::Mat>("3D_ResultantForce");
    tempMat->copyTo(Fr); // 务必先将获得的数据拷贝到自己的变量中再使用

    // 使用frame.get函数通过数据名称"3D_ResultantForce"获得cv::Mat类型的三维合力的数据指针
    tempMat = frame.get<cv::Mat>("3D_ResultantMoment");
    tempMat->copyTo(Mr); // 务必先将获得的数据拷贝到自己的变量中再使用
}


int main(int argc,char **argv)
{
    float testParam = 100.0;
    Tac3D::Sensor tac3d(Tac3DRecvCallback, 9988, &testParam); // 创建Sensor实例，设置回调函数为上面写好的Tac3DRecvCallback，设置UDP接收端口为9988
    tac3d.waitForFrame(); // 等待Tac3D-Desktop端启动传感器并建立连接

    usleep(1000*1000*5); // 5s
    tac3d.calibrate(SN); // 发送一次校准信号（应确保校准时传感器未与任何物体接触！否则会输出错误的数据！）

    usleep(1000*1000*5); // 5s
    // tac3d.quitSensor(SN); // 发送一次退出信号（不建议使用）
}
