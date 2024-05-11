import time
import network
import json
import requests
import ntptime
import suncalc
import display
import math

"""
This module is used for fetching and parsing data from the internet,
and for collecting other data from various API's
"""


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ _CONSTANTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# how long we can try connecting (in seconds)
_CONNECT_TIMEOUT_SECONDS = const(20) 

SUNSET_POINT = -0.3

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ GLOBALS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



NIC = network.WLAN(network.STA_IF)

with open('config.json', 'r') as config_file:
    CONFIG = json.loads(
        config_file.read()
        )

TIMEZONE = None

SUN_DATA = {}
TIDE_LEVEL = 1.5 # random/arbitrary val to start

# dict stores color values as 4 tuples of hsv(3 tuple) values.
# these colors ordered as: (sunrise color, noon color, sunset color, midnight color)
# and are mixed/stored in CURRENT_COLORS
COLORS = {
    'sky_top': ((0.625, 0.47, 0.73), (0.53611, 0.13, 1.0), (0.69444, 0.71, 0.13), (0.9693, 0.4, 0.12)),
    'sky_mid': ((0.0, 0.16, 0.87), (0.55555, 0.5, 0.98), (0.908, 0.46, 0.5), (0.5638, 0.16, 0.08)),
    'sky_bottom': ((0.1027, 0.87, 1.0), (0.55555, 0.99, 0.97), (0.113888, 0.87, 0.98), (0.097, 0.52, 0.0)),
    
    'sun': ((0.06111, 1.0, 1.0), (0.15, 1.0, 1.0), (0.030555, 1.0, 0.98), (0.0177, 1.0, 0.65)),
    
    'beach_top': ((0.10555, 0.7, 0.99), (0.15277, 0.15, 0.86), (0.51111, 0.28, 0.21), (0.09722, 0.53, 0.13)),
    'beach_bottom': ((0.09722, 0.53, 0.15), (0.14166, 0.6, 0.3), (0.53333, 0.17, 0.05), (0.09722, 0.53, 0.0)),
    
    'water_top': ((0.1, 0.79, 0.93), (0.60278, 0.92, 0.68), (0.1222, 0.94, 0.86), (0.61666, 0.67, 0.27)),
    'water': ((0.5583, 0.76, 0.49), (0.43611, 0.52, 0.84), (0.76111, 0.43, 0.50), (0.65278, 0.27, 0.46)),
    }

CURRENT_COLORS = {}

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
    
    
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ TIME/TIMEZONE FUNCTIONS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def get_timezone_data(refresh=False):
    global TIMEZONE, CONFIG
    
    if TIMEZONE is None or refresh:
        coords = CONFIG["location_coords"]
        url = f"https://www.timeapi.io/api/TimeZone/coordinate?latitude={coords[0]}&longitude={coords[1]}"
        
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"get_time_data failed with this response: {response.status_code}")
            return False
        
        TIMEZONE = json.loads(response.content)
        
    return True

def get_date_str():
    """Return current time as a string based on ISO 8601"""
    year, month, mday, hour, minute, second, _, _ = time.localtime()
    
    datestr = f"{year:04d}-{month:02d}-{mday:02d}T{hour:02d}:{minute:02d}:{second:02d}Z"
    return datestr

def get_20_min_datestr():
    """Return start and end time for last 20 minute period."""
    _TWENTY_MINUTES = const(20 * 60)
    
    year, month, mday, hour, minute, second, _, _ = time.localtime(time.time())
    nowstr = f"{year:04d}-{month:02d}-{mday:02d}T{hour:02d}:{minute:02d}:{second:02d}Z"
    
    year, month, mday, hour, minute, second, _, _ = time.localtime(time.time() - _TWENTY_MINUTES)
    paststr = f"{year:04d}-{month:02d}-{mday:02d}T{hour:02d}:{minute:02d}:{second:02d}Z"
    
    return paststr, nowstr
    
def fetch_from_tide_station(station_id):
    """Fetch current tide height from Canada tide API service"""
    time1, time2 = get_20_min_datestr()
    
    url = f"https://api.iwls-sine.azure.cloud-nuage.dfo-mpo.gc.ca/api/v1/stations/{station_id}/data?time-series-code=wlo&from={time1}&to={time2}&resolution=FIVE_MINUTES"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"fetch_from_tide_station failed with this response: {response.status_code}")
        return False
    
    station_data = json.loads(response.content)
    
    output = []
    
    for item in station_data:
        output.append(station_data[0]["value"])
    
    return output
    
    
def get_tide_data():
    """Fetch current tide height from Canada tide API service"""
    # https://api.iwls-sine.azure.cloud-nuage.dfo-mpo.gc.ca/swagger-ui/index.html#/
    global CONFIG, TIDE_LEVEL
    
    # tide stations https://tides.gc.ca/en/stations
    stations = CONFIG["tide_stations"]
    
    all_data = []
    
    for station in stations:
        data = fetch_from_tide_station(station)
        if data:
            all_data += data
    
    if not all_data:
        return False # no data found
    
    TIDE_LEVEL = sum(all_data) / len(all_data)
    
    


def set_time():
    try:
        ntptime.settime()
    except Exception as e:
        print(f"Couldn't sync NTP time: {e}")
    try:
        get_timezone_data()
    except Exception as e:
        print(f"Couldn't get timezone data: {e}")
    
def to_local_time(utc_time):
    if type(utc_time) == tuple:
        utc_time = time.mktime(utc_time)
        
    local_epoch = utc_time + TIMEZONE["currentUtcOffset"]["seconds"]
    return time.localtime(local_epoch)
    
def get_local_time():
    epoch = time.time()
    local_epoch = epoch + TIMEZONE["currentUtcOffset"]["seconds"]
    return time.localtime(local_epoch)




# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ TIME/TIMEZONE FUNCTIONS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def find_sun_data(date=None, full=True):
    global SUN_DATA
    _DAY_SECONDS = const(60 * 60 * 24)
#     _SUNSET_TIMES = (
#         (-0.833, 'sunrise', 'sunset'),
#         )
    _SUNSET_TIMES = (
        (SUNSET_POINT, 'sunrise', 'sunset'),
        )
    
    lat, lng = CONFIG['location_coords']
    
    
    # get sun times for now, tommorow, and yesterday
    if date is None:
        epoch = time.time()
    else:
        epoch = date
    #yesterday = epoch - _DAY_SECONDS
    #tommorow = epoch + _DAY_SECONDS
    
    
    SUN_DATA['sun_position'] = suncalc.get_position(lat=lat, lng=lng, degrees=True, date=epoch)
    
    if full:
        SUN_DATA['sun_times'] = suncalc.get_times(lat=lat, lng=lng, times=_SUNSET_TIMES, date=epoch)
        SUN_DATA['moon_position'] = suncalc.get_moon_position(lat=lat, lng=lng, degrees=True, date=epoch)
        SUN_DATA['moon_illumination'] = suncalc.get_moon_illumination(date=epoch)
#     
#     SUN_DATA = {
#         'sun_position':position,
#         'sun_times': times,
#     #    'sun_tommorow': tommorow,
#     #    'sun_yesterday': yesterday,
#         'moon_position': moon_position,
#         'moon_illumination': moon_illumination,
#         }


def get_factor(minimum, current, maximum) -> float:
    """Calculate where "current" falls between minimum/maximum,
    returns a float from 0.0 to 1.0
    """
    
    if current >= maximum:
        return 1.0
    if current <= minimum:
        return 0.0
    
    # rescale vals so that minimum = 0
    current = current - minimum
    maximum = maximum - minimum
    
    return current / maximum
    
def ease_in_circ(x):
    return 1 - math.sqrt(1 - (x ** 2))

def ease_out_circ(x):
    return math.sqrt(1 - ((x - 1) ** 2))
    

def set_colors_by_sun(date=None ):
    """Compare current time to sun times in SUN_DATA
    Use that info to select and set color data
    from COLORS to CURRENT_COLORS
    """
    global COLORS, CURRENT_COLORS, SUN_DATA
    
    sun_times = SUN_DATA['sun_times']
    if date is None:
        now = time.time()
    else:
        now = date
    
    last_midnight = time.mktime(sun_times['nadir'])
    sunrise       = time.mktime(sun_times['sunrise'])
    noon          = time.mktime(sun_times['solar_noon'])
    sunset        = time.mktime(sun_times['sunset'])
    next_midnight = last_midnight + _DAY_SECONDS
    
    # now MUST be within suntimes. adjust if not:
    while now < last_midnight:
        now += _DAY_SECONDS
    while now > next_midnight:
        now -= _DAY_SECONDS
    
#     set_yesterday = set_today - _DAY_SECONDS
#     rise_tommorow = rise_today + _DAY_SECONDS
    
    # for this to work, times MUST be in order
    if not (last_midnight <= sunrise <= noon <= sunset <= next_midnight):
        print(last_midnight, sunrise,noon, sunset, next_midnight)
    assert last_midnight <= sunrise <= noon <= sunset <= next_midnight
    assert last_midnight <= now <= next_midnight
    
    # clr_indices = 0, 1, 2, 3 for sunrise, noon, sunset, midnight
    # determine where "now" falls between the times above
    if last_midnight <= now <= sunrise:
        fac = get_factor(last_midnight, now, sunrise)
        fac = ease_in_circ(fac)
        clr_indices = (3, 0)
        
    elif sunrise <= now <= noon:
        fac = get_factor(sunrise, now, noon)
        fac = ease_out_circ(fac)
        clr_indices = (0, 1)
        
    elif noon <= now <= sunset:
        fac = get_factor(noon, now, sunset)
        fac = ease_in_circ(fac)
        clr_indices = (1, 2)
        
    else: # sunset <= now <= next_midnight:
        fac = get_factor(sunset, now, next_midnight)
        fac = ease_out_circ(fac)
        clr_indices = (2, 3)
#   
#     else: # midnight <= now <= rise_tommorow:
#         fac = get_factor(midnight, now, rise_tommorow)
#         clr_indices = (3, 0)
        
    # mix colors, set colors
    for key, vals in COLORS.items():
        clr1 = vals[clr_indices[0]]
        clr2 = vals[clr_indices[1]]
        CURRENT_COLORS[key] = display.mix_hsv_in_rgb(clr1, clr2, factor=fac)
    
    #print(now)
    #print(last_midnight, sunrise, noon, sunset, next_midnight)
    #print(f"fac: {fac}, clr_indices: {clr_indices}")

def update_data_calculate(date=None, full=True):
    find_sun_data(date=date, full=full)
    set_colors_by_sun(date=date)
    
    
def update_data_internet():
    connect_to_internet()
    
    set_time()
    get_tide_data()
    
    stop_internet_connection()




if __name__ == "__main__":
    lat, lng = CONFIG['location_coords']
    
    print(CONFIG)
    
    #connect_to_internet()
    #get_tide_data()
    #print(TIDE_LEVEL)
    #get_tide_data()
    #update_data_internet()
    
    #find_sun_data()
    #print(SUN_DATA)
    