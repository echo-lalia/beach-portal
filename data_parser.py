import time
import network
import json
import requests
import ntptime

"""
This module is used for fetching and parsing data from the internet,
and for collecting other data from various API's
"""


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ _CONSTANTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# how long we can try connecting (in seconds)
_CONNECT_TIMEOUT_SECONDS = const(20) 


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ GLOBALS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



NIC = network.WLAN(network.STA_IF)

with open('config.json', 'r') as config_file:
    CONFIG = json.loads(
        config_file.read()
        )

TIMEZONE = None

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ WIFI FUNCTIONS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def connect_to_internet():
    """Turn on wifi and try connecting to each given credential."""
    
    # turn on wifi if it isn't already
    NIC.active(True)
    
    # cycle through each wifi cred from config
    for ssid, passwd in CONFIG['wifi_creds']:
        
        attemps = 0
        NIC.connect(ssid, passwd)
        
        # wait for connection, break when timout surpassed or connected.
        while not NIC.isconnected():
            if attemps > _CONNECT_TIMEOUT_SECONDS:
                print(f"Timeout when connecting to '{ssid}'")
                break
            else:
                attemps += 1
                time.sleep(1)
        
        # do not try more credentials if we are connected
        if NIC.isconnected():
            print(f"Successfully connected to '{ssid}'")
            return True
    
    return NIC.isconnected()


def stop_internet_connection():
    """Disconnect and turn off wifi."""
    NIC.disconnect()
    NIC.active(False)
    
    
# fetch internet data
def get_timezone_data():
    global TIMEZONE
    
    if TIMEZONE is None:
        coords = CONFIG["location_coords"]
        url = f"https://www.timeapi.io/api/TimeZone/coordinate?latitude={coords[0]}&longitude={coords[1]}"
        
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"get_time_data failed with this response: {response.status_code}")
            return False
    
    TIMEZONE = json.loads(response.content)
    print(response.content)
    return True
    
def set_time():
    try:
        ntptime.settime()
    except Exception as e:
        print(f"Couldn't sync NTP time: {e}")
    try:
        get_timezone_data()
    except Exception as e:
        print(f"Couldn't get timezone data: {e}")
    
def get_local_time():
    epoch = time.time()
    local_epoch = epoch + TIMEZONE["currentUtcOffset"]["seconds"]
    return time.localtime(local_epoch)

if __name__ == "__main__":
    print(CONFIG)
    connect_to_internet()
    
    set_time()
    print(get_local_time())
    
    stop_internet_connection()