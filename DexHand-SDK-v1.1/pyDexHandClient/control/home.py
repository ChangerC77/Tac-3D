from dexhand_client import DexHandClient

if __name__ == "__main__":
    client = DexHandClient(ip="192.168.2.100", port=60031)
    client.start_server() # start the server
    
    """ hand """
    client.acquire_hand() # acquire control and initialized the hand
    
    # 1. initialized gripper position
    # 通过使 DexHand 张开到最大位置，校准夹爪的位置零点 
    client.set_home()  # parameters: goal_speed (1.0 - 8.0 mm/s, default = 4 mm/s)