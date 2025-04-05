from dexhand_client import DexHandClient
import time

if __name__ == "__main__":
    client = DexHandClient(ip="192.168.2.100", port=60031)
    client.start_server() # start the server
    
    """ hand """
    client.acquire_hand() # acquire control and initialized the hand
    
    # 1. initialized gripper position
    # 通过使 DexHand 张开到最大位置，校准夹爪的位置零点 
    # client.set_home()  # parameters: goal_speed (1.0 - 8.0 mm/s, default = 4 mm/s)
    # time.sleep(3)
    # 2. initialized force 
    # client.calibrate_force_zero() # acquire_hand() will use it automatically
    
    # 3. force control
    client.pos_goto(goal_pos=10.0,max_speed=16.0,max_acc=30.0,max_f=1.0) # with maximum speed and force to move
    time.sleep(5)
    client.pos_goto(goal_pos=48.0,max_speed=16.0,max_acc=30.0,max_f=1.0) # with maximum speed and force to move
    print("pos_goto has finished.")
    time.sleep(3)
    
    # 4. 允许用户在 DexHand尚未到达指定位置时更改目标位置
    # client.pos_servo(goal_pos=20.0,max_f=1.0)
    # print("pos_servo has finished.")
    # time.sleep(1)
    
    client.release_hand() # realsease to control hand 