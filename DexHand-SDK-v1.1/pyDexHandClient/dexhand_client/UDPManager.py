import socket
import threading
import time


class UDP_Manager:
    def __init__(self, callback, isServer=False, ip="", port=8083, frequency=1000, inet=4):
        self.callback = callback

        self.isServer = isServer
        self.interval = 1.0 / frequency

        # self.available_addr = socket.getaddrinfo(socket.gethostname(), port)
        # self.hostname = socket.getfqdn(socket.gethostname())
        self.inet = inet
        self.af_inet = None
        self.ip = ip
        self.localIp = None
        self.port = port
        self.addr = (self.ip, self.port)
        self.running = False

        # self.serialNum = 0
        # self.recvPools = {} #{'IP:PORT': [{serialNum:[data..., recvNum, packetNum, timestamp]}]}

    def start(self):
        if self.inet == 4:
            self.af_inet = socket.AF_INET  # ipv4
            self.localIp = "127.0.0.1"
        elif self.inet == 6:
            self.af_inet = socket.AF_INET6  # ipv6
            self.localIp = "::1"
        self.sockUDP = socket.socket(self.af_inet, socket.SOCK_DGRAM)

        if self.isServer:
            self.roleName = "Server"
        else:
            self.port = 0
            self.roleName = "Client"

        self.sockUDP.bind((self.ip, self.port))
        self.sockUDP.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 212992)
        self.addr = self.sockUDP.getsockname()
        self.ip = self.addr[0]
        self.port = self.addr[1]
        print("[UDP Manager]", self.roleName, "at:", self.ip, ":", self.port)

        self.running = True
        self.thread = threading.Thread(target=self.receive, args=())
        self.thread.setDaemon(True)
        self.thread.start()  # 打开收数据的线程

    # def ListAddr(self):
    #     for item in self.available_addr:
    #         if item[0] == self.af_inet:
    #             print(item[4])

    def receive(self):
        while self.running:
            time.sleep(self.interval)
            while self.running:
                try:
                    recvData, recvAddr = self.sockUDP.recvfrom(65535)  # 等待接受数据
                except:
                    break
                if not recvData:
                    break
                self.callback(recvData, recvAddr)

    def send(self, data, addr):
        self.sockUDP.sendto(data, addr)

    def close(self):
        self.running = False


def client_receive(recv_data, recv_addr):
    print(recv_data)
