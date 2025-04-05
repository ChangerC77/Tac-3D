#ifndef _LIBTAC3D_HPP
#define _LIBTAC3D_HPP

#include <yaml-cpp/yaml.h>
#include <opencv2/opencv.hpp>
#include <queue>
#include <map>
#include <thread>
#include <unistd.h>


#define NETWORKRECEIVE_BUFFSIZE 1024000
#define NETWORKRECEIVE_UDPPACKETSIZE 1400  // 这个值必须和NETWORKTRANSPORT_UDPPACKETSIZE一致!!
#define NETWORKRECEIVE_RECVPOOLSIZE 10
#define NETWORKRECEIVE_RECVTIMEOUT 1.0
#define FRAME_BUFFERSIZE 10

#ifdef __WIN32__
#include <windows.h>
#define socklen_t int
#else
#include <arpa/inet.h>   //htonl  htons 所需的头文件
#endif

namespace Tac3D
{

class Timer
{
public:
    struct timeval startTime;
    struct timeval checkTime;
    struct timeval currentTime;

    double Start();
    double GetTime();
    double Check();
};

typedef struct
{
    int dataLength;
    char *data;
    socklen_t addr_len;
    sockaddr_in addr;
}SockUDPFrame_t;

class UDPSock
{
public:
//构造函数，初始化时创建套接字，异常处理。
    UDPSock(void);
    void Start(int port = 8083, bool isServer = false);
    void SetCallback(void (*callback)(SockUDPFrame_t *frame, void *param), void *param);
    //析构函数，关闭连接，清理缓冲区
    ~UDPSock();
    //发送数据
    bool Send(SockUDPFrame_t *frame);

    bool SetAddr(SockUDPFrame_t *frame, const char* ip, int port);

private:
    void ServSockBind(int port);
    //接受数据
    void Receive();
    int udp_sock;//套接字，由构造函数初始化
    sockaddr_in udp_addr;//socket地址，待绑定ip、端口、套接字类型
    bool running;
    void (*recvCallback)(SockUDPFrame_t *frame, void *param);
    void *recvCallbackParam;
};

struct NetworkReceiveBuffer
{
    int bufferIndex;
    bool isFree;
    double loaclTimestamp;
    uint32_t serialNum;

    uint16_t pktNum;
    uint16_t pktCnt;

    int headLen;
    int dataLen;
    char headBuffer[NETWORKRECEIVE_UDPPACKETSIZE];
    char dataBuffer[NETWORKRECEIVE_BUFFSIZE];
};

class Frame
{
private:
    std::map<std::string, void*> fieldCache;

public:
    uint32_t index = 0;
    std::string SN;
    double sendTimestamp;
    double recvTimestamp;
    
    void _addFrameField(std::string fieldName, void* ptr);

    template <typename T>
    T* get(std::string fieldName)
    {
        if (Frame::fieldCache.find(fieldName) != Frame::fieldCache.end())
        {
            return (T*)Frame::fieldCache[fieldName];
        }
        else
        {
            std::cout << "frame field not found : " << fieldName << " (get).";
            return NULL;
        }
    }

    void dumpField();
};


class Sensor
{
private:
    UDPSock UDP;
    int port;
    std::map<std::string, sockaddr_in> fromAddrMap;
    std::map<std::string, int> typeDict;
    Frame recvFrame;
    bool _isReady;
    void (*_recvCallback)(Frame &frame, void *param) = NULL;
    void *_callbackParam;
public:
    Timer timer;
    NetworkReceiveBuffer *bufferPool = NULL;
    NetworkReceiveBuffer* _GetFreeBuffer();
    NetworkReceiveBuffer* _GetBufferBySerialNum(uint32_t serialNum);
    void _process(NetworkReceiveBuffer &buffer, sockaddr_in &fromAddr);
    ~Sensor();
    Sensor(void (*recvCallback)(Frame &frame, void *param), int port, void* callbackParam = NULL);
    void calibrate(std::string SN);
    void quitSensor(std::string SN);
    void waitForFrame();
};

}

#endif

