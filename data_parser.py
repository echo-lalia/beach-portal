import time
import network
import json
import requests
import ntptime
import suncalc
import display
import math
from utils import *

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

WEATHER = { # using default values to reduce possible errors
    'precipitation': 0.0, 'rain': 0.0, 'wind_speed': 14.0, 'snow': 0.0, 'temperature': 10.0, 'visibility': 20000.0, 'cloud_cover': 40, 'precipitation_probability': 10
    }

# dict stores color values as 4 tuples of hsv(3 tuple) values.
# these colors ordered as: (sunrise color, noon color, sunset color, midnight color)
# and are mixed/stored in CURRENT_COLORS
COLORS = {
    'sky_top': ((0.625, 0.47, 0.73), (0.57, 1.0, 0.97), (0.69444, 0.71, 0.13), (0.9693, 0.4, 0.12)),
    'sky_mid': ((0.0, 0.16, 0.87), (0.55555, 0.8, 0.98), (0.908, 0.46, 0.5), (0.5638, 0.16, 0.08)),
    'sky_bottom': ((0.1027, 0.87, 1.0), (0.53611, 0.3, 1.0), (0.113888, 0.87, 0.98), (0.097, 0.52, 0.0)),
    
    'sun': ((0.06111, 1.0, 1.0), (0.15, 1.0, 1.0), (0.030555, 1.0, 0.98), (0.0177, 1.0, 0.65)),
    
    'cloud_top': ((0.16666, 0.56, 0.99), (0.41666, 0.001, 0.99), (0.81, 0.31, 0.13), (0.5638, 0.16, 0.08)),
    'cloud_bottom': ((0.05, 0.88, 0.27), (0.55555, 0.1, 0.85), (0.094, 0.69, 0.99), (0.5638, 0.16, 0.08)),
    
    'beach_top': ((0.10555, 0.7, 0.99), (0.15277, 0.15, 0.86), (0.51111, 0.28, 0.21), (0.09722, 0.53, 0.13)),
    'beach_bottom': ((0.09722, 0.53, 0.15), (0.14166, 0.6, 0.3), (0.53333, 0.17, 0.05), (0.09722, 0.53, 0.0)),
    
    'mountain': ((0.04444, 0.45, 0.20), (0.6277778, 0.71, 0.6), (0.9194, 0.45, 0.20), (0.56389, 0.54, 0.32)),
    
    'water_top': ((0.1, 0.79, 0.93), (0.60278, 0.92, 0.68), (0.1222, 0.94, 0.86), (0.61666, 0.67, 0.27)),
    'water': ((0.5583, 0.76, 0.49), (0.43611, 0.52, 0.84), (0.76111, 0.43, 0.50), (0.65278, 0.27, 0.46)),
    
    'water_edge_end': ((0.6888889, 0.21, 0.34), (0.51944, 0.19, 0.93), (0.6888889, 0.21, 0.34), (0.5333333, 0.86, 0.16)),
    'water_sand_overlay': ((0.08333334, 0.75, 0.84), (0.675, 1.0, 0.17), (0.08333334, 0.75, 0.84), (0.675, 1.0, 0.0)),
    
    'fog': ((0.08888, 0.55, 0.90), (0.6388, 0.02, 0.82), (0.025, 0.56, 0.74), (0.04722, 0.9, 0.19)),

    'boat_overlay': ((0.1055, 0.5, 0.75), (0.14722, 0.35, 1.0), (0.88055, 0.79, 0.38), (0.59722, 1.0, 0.5)),
    'seasonal_overlay': ((0.1055, 0.79, 1.0), (0.14722, 0.35, 1.0), (0.88055, 0.79, 0.38), (0.59722, 1.0, 0.5)),
    
    }

CURRENT_COLORS = {}

# based on sun height
OVERLAY_SUN_COLORS = (
# max down
(0.6472, 0.81, 0.15),
# slightly down
(0.5611, 0.27, 0.34),
# horizon
(0.8944, 0.25, 0.47),
# slightly up
(0.108, 0.3, 0.6),
# max up
(0.133, 0.55, 0.79),
)

CURRENT_OVERLAY = 0

FOG_OPACITY = 0

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
                log(f"Timeout when connecting to '{ssid}'")
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
            log(f"get_time_data failed with this response: {response.status_code}")
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
        log(f"fetch_from_tide_station failed with this response: {response.status_code}")
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
        log(f"Couldn't sync NTP time: {e}")
    try:
        get_timezone_data()
    except Exception as e:
        log(f"Couldn't get timezone data: {e}")


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

def ease_out_cubic(x):
    return 1 - ((1 - x) ** 3)

def ease_in_sine(x):
  return 1 - math.cos((x * math.pi) / 2)



def set_overlay_colors():
    global OVERLAY_SUN_COLORS, CURRENT_OVERLAY, SUN_DATA, FOG_OPACITY
    
    # point where we switch from horizon/day colors, to day/noon colors
    _MID_FACTOR = const(0.3)
    
    # find factor based on sun height
    altitude = SUN_DATA['sun_position']['altitude']
    sun_up = altitude > 0
    
    if sun_up:
        fac = get_factor(0, altitude, 90)
        colors = OVERLAY_SUN_COLORS[2:]
    else:
        fac = get_factor(0, -altitude, 90)
        colors = tuple(reversed(OVERLAY_SUN_COLORS[:3]))
    
    if fac > _MID_FACTOR:
        #rescale mid_factor-1, to 0-1
        fac -= _MID_FACTOR
        fac *= 1 / (1 - _MID_FACTOR)
        CURRENT_OVERLAY = display.mix_hsv_in_rgb(colors[1], colors[2], factor=fac)
    else:
        # rescale 0-mid_factor, to 0-1
        fac *= 1 / _MID_FACTOR
        CURRENT_OVERLAY = display.mix_hsv_in_rgb(colors[0], colors[1], factor=fac)
    
    # add temperature data to overlay color
    hot_factor = ease_in_sine(
        get_factor(24, WEATHER['temperature'], 40)
        )
    CURRENT_OVERLAY = display.mix_hsv_in_rgb(CURRENT_OVERLAY, (0.03, 0.95, 0.63), factor=hot_factor)
    
    cold_factor = ease_in_sine(
        1.0 - get_factor(-30, WEATHER['temperature'], 0)
        )
    CURRENT_OVERLAY = display.mix_hsv_in_rgb(CURRENT_OVERLAY, (0.6, 0.55, 0.74), factor=cold_factor)
    
    
    # also set fog opacity based on weather
    visibility_fac = ease_in_circ(clamp(1 - (WEATHER['visibility'] / 10000)))
    FOG_OPACITY = int(visibility_fac * 90)
    
    

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
        log(f"Incorrect time order in 'set_colors_by_sun': last_midnight:{last_midnight}, sunrise:{sunrise}, noon:{noon}, sunset:{sunset}, next_midnight:{next_midnight}")
#     assert last_midnight <= sunrise <= noon <= sunset <= next_midnight
#     assert last_midnight <= now <= next_midnight
    
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

# def get_weather_data():
#     global WEATHER
#     lat, lon = CONFIG['location_coords']
#     key = CONFIG['weather_key']
#     url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={key}&units=metric"
#     
#     response = requests.get(url)
#     
#     if response.status_code != 200:
#         log(f"get_weather_data failed with this response: {response.status_code}")
#         return False
#     
#     WEATHER = json.loads(response.content)


def get_weather_data():
    global WEATHER
    lat, lon = CONFIG['location_coords']
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=apparent_temperature,precipitation,snowfall,cloud_cover,wind_speed_10m&hourly=precipitation_probability,visibility&timeformat=unixtime&forecast_days=1"
    
    response = requests.get(url)
    
    if response.status_code != 200:
        log(f"get_weather_data failed with this response: {response.status_code}")
        return False
    
    content = json.loads(response.content)
    current = content.get('current', {})
    hourly = content.get('hourly', {})
    
    WEATHER = {
        'temperature': current.get('apparent_temperature', 10),
        'cloud_cover': current.get('cloud_cover', 0),
        'wind_speed': current.get('wind_speed_10m', 0),
        'precipitation': current.get('precipitation', 0),
        'snow': current.get('snowfall', 0),
        }
    # find total rain amount by subtracting snowfall from precipitation
    # i'm doing this because I don't want to deal with other types of precipitation.
    WEATHER['rain'] = WEATHER['precipitation'] - WEATHER['snow']
    
    # now we need to process hourly weather into current weather
    # we will do this by comparing the given 'current time' to the hourly times to find our index.
    best_index = 0
    best_error = 31536000
    time_now = current['time']
    for index, timestamp in enumerate(hourly['time']):
        error = abs(time_now - timestamp)
        if error < best_error:
            best_error = error
            best_index = index
    
    WEATHER['visibility'] = hourly['visibility'][best_index]
    WEATHER['precipitation_probability'] = hourly['precipitation_probability'][best_index]
    

def update_data_calculate(date=None, full=True):
    find_sun_data(date=date, full=full)
    set_colors_by_sun(date=date)
    set_overlay_colors()
    
    
def update_data_internet():
    connect_to_internet()
    
    set_time()
    get_tide_data()
    get_weather_data()
    
    stop_internet_connection()




if __name__ == "__main__":
    lat, lng = CONFIG['location_coords']
    
    print(CONFIG)
    
    #connect_to_internet()
    #get_tide_data()
    #print(TIDE_LEVEL)
    #get_tide_data()
    #get_weather_data()
    
    update_data_internet()
    print(
f"""

Timezone:
{TIMEZONE}

Tide level:
{TIDE_LEVEL}

Sun data:
{SUN_DATA}

Weather:
{WEATHER}

""")
    
    #find_sun_data()
    #print(SUN_DATA)
    