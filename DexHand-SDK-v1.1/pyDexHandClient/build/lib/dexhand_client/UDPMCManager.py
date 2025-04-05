import ipaddress
import socket
import struct
import time
import threading


class UDP_MC_Manager:
    def __init__(self, callback=None, isSender=False, ip="", group="224.0.0.1", port=8083, frequency=1000):
        self.callback = callback

        self.isSender = isSender
        self.interval = 1.0 / frequency

        self.af_inet = None
        if group is not None and group != "" and ipaddress.ip_address(group) in ipaddress.ip_network("224.0.0.0/4"):
            self.group = group
        elif self.isSender:
            print("[UDP Manager] Invalid multicast group address, should be in 224.0.0.0/4")
            return
        else:
            self.group = ""

        self.ip = ip
        self.port = port
        self.addr = (self.group, self.port)
        self.running = False

    def start(self):
        self.af_inet = socket.AF_INET  # ipv4
        self.sockUDP = socket.socket(self.af_inet, socket.SOCK_DGRAM)

        if self.isSender:
            self.roleName = "Sender"
            self.sockUDP.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            self.sockUDP.bind((self.ip, 0))
        else:
            self.roleName = "Receiver"
            self.sockUDP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sockUDP.bind(("", self.port))
            self.sockUDP.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 212992)
            mreq = struct.pack("4s4s", socket.inet_aton(self.group), socket.inet_aton(self.get_interface_ip(self.ip)))
            self.sockUDP.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        print("[UDP Manager]", self.roleName, "at:", self.group, ":", self.port)

        self.running = True
        if not self.isSender and self.callback is not None:
            self.thread = threading.Thread(target=self.receive, args=())
            self.thread.setDaemon(True)
            self.thread.start()  # 打开收数据的线程

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

    def send(self, data):
        if self.isSender:
            self.sockUDP.sendto(data, self.addr)

    def close(self):
        self.running = False

    def get_interface_ip(self, ip):
        s = socket.socket(self.af_inet, socket.SOCK_DGRAM)
        s.connect((ip, 0))
        addr = s.getsockname()
        s.close()
        return addr[0]


def receiver_callback(recv_data, recv_addr):
    print(recv_data)
