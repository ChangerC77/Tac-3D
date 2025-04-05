from dexhand_client import DexHandClient

if __name__ == "__main__":
    client = DexHandClient(ip="192.168.2.100", port=60031)
    client.start_server() # start the server
    
    client.acquire_hand() # acquire control and initialized the hand
    client.clear_hand_error()