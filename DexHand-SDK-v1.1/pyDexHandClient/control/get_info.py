from dexhand_client import DexHandClient
from time import sleep

""" get the information about hand """

def recv_callback_hand(client: DexHandClient):
    if client.hand_info._frame_cnt % 20 == 0:  # 每20帧执行一次
        print(f"DexHand: now position = {client.hand_info.now_pos:.3f}")
        print(f"DexHand: goal position = {client.hand_info.goal_pos:.3f}")
        print(f"DexHand: now speed = {client.hand_info.now_speed:.3f}")
        print(f"DexHand: goal speed = {client.hand_info.goal_speed:.3f}")
        print(f"DexHand: now current = {client.hand_info.now_current:.3f}")
        print(f"DexHand: goal current = {client.hand_info.goal_current:.3f}")
        print(f"DexHand: now force = {client.hand_info.now_force}")
        print(f"DexHand: avg force = {client.hand_info.avg_force:.3f}")
        print(f"DexHand: goal force = {client.hand_info.goal_force:.3f}")
        print(f"DexHand: imu acc = {client.hand_info.imu_acc:}")
        print(f"DexHand: imu gyr = {client.hand_info.imu_gyr:}")
        print(f"DexHand: is_contact = {client.hand_info.imu_gyr:}")
        print(f"DexHand: error flag = {client.hand_info.error_flag:}")
        print(f"DexHand: now task = {client.hand_info.now_task:}")
        print(f"DexHand: recent task = {client.hand_info.recent_task:}")
        print(f"DexHand: recent task status = {client.hand_info.recent_task_status:}")
        print(f"DexHand: _frame_cnt = {client.hand_info._frame_cnt:}")
        

if __name__ == "__main__":
    client = DexHandClient(
        ip="192.168.2.100",
        port=60031,
        recvCallback_hand=recv_callback_hand,
    )
    client.start_server()
    sleep(1)
