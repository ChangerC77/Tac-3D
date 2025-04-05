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
    client.calibrate_force_zero()
    client.contact(contact_speed=8, preload_force=2, quick_move_speed=15, quick_move_pos=10)
    client.grasp(goal_force=10.0, load_time=5.0)
    client.force_servo(goal_force=1.0)
    sleep(8)

    client.release_hand()
