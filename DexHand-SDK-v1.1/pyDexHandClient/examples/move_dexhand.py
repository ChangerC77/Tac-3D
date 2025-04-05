from dexhand_client import DexHandClient
from time import sleep


def report_hand_info(client: DexHandClient):
    info = client.hand_info
    if info._frame_cnt % 10 == 0:
        print(
            f"Error:{info.error_flag}, nowforce: {info.avg_force:.3f}N nowpos: {info.now_pos:.3f}mm",
            end=" ",
        )
        if info.now_task in ["GOTO", "POSSERVO"]:
            print(f"goalpos : {info.goal_pos:.2f}")
        elif info.now_task in ["SETFORCE", "FORCESERVO"]:
            print(f"goalforce : {info.goal_force:.2f}")
        else:
            print()


if __name__ == "__main__":
    client = DexHandClient(
        ip="192.168.2.100",
        port=60031,
        recvCallback_hand=report_hand_info,
    )
    client.start_server()
    client.acquire_hand()

    client.set_home()
    client.pos_goto(goal_pos=30, max_speed=40, max_acc=20, max_f=3)
    client.pos_servo(goal_pos=10, max_f=3)
    sleep(2)

    client.release_hand()
