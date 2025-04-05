from dexhand_client import DexHandClient
from time import sleep


def recv_callback_hand(client: DexHandClient):
    if client.hand_info._frame_cnt % 20 == 0:  # 每20帧执行一次
        print(f"DexHand: now position = {client.hand_info.now_pos:.3f}")


if __name__ == "__main__":
    client = DexHandClient(
        ip="192.168.2.100",
        port=60031,
        recvCallback_hand=recv_callback_hand,
    )
    client.start_server()
    sleep(10)
