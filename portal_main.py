import time
import lightsensor
import display
import machine
from machine import Pin, freq, PWM, Timer
import data_parser
import math
import framebuf
from utils import *
import random

freq(240_000_000)

# debug tools:
_FORCE_MAX_LIGHT_ = False
_FAST_CLOCK = True
_SUPRESS_TIME_SYNC = True


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ _CONSTANTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

_BLIGHT_MAX = const(65535)
#_BLIGHT_MAX = const(10000)
_WIDTH = const(272)
_HEIGHT = const(480)

_CENTER_X = const(_WIDTH//2)

# how often to reload data from internet
_RELOAD_DATA_SECONDS = const(60 * 60)


SUNSET_POINT_DEGREES = math.degrees(data_parser.SUNSET_POINT)

# sky size
_SKY_HEIGHT = const((_HEIGHT * 2) // 3)
_SKY_START_HEIGHT = const((_SKY_HEIGHT * 2) // 3)
_SKY_MID_HEIGHT = const(_SKY_HEIGHT-_SKY_START_HEIGHT)

# when to stop drawing sun/ start drawing moon
_SKY_HEIGHT_MOON_START = const(_SKY_HEIGHT + 10)
_SKY_HEIGHT_SUN_STOP = const(_SKY_HEIGHT_MOON_START + 60)

_BEACH_HEIGHT = const(_HEIGHT - _SKY_HEIGHT)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ GLOBALS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


SENSOR = lightsensor.LightSensor()
BLIGHT = PWM(Pin(1, Pin.OUT))
DISPLAY = display.Display()

RTC = machine.RTC()

WIDTH = DISPLAY.width
HEIGHT = DISPLAY.height

# create backlight timer
BL_TIMER = Timer(3)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ function defs ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def timer_callback(t):
    set_backlight_from_sensor()

def set_backlight_from_sensor(t=None):
    if _FORCE_MAX_LIGHT_:
        BLIGHT.duty_u16(_BLIGHT_MAX)
        return
    
    BLIGHT.duty_u16(SENSOR.read())
    
    
def ease_out_circ(x):
    return math.sqrt(1 - ((x - 1) ** 2))


def ease_in_out_circ(x):
    if x < 0.5:
        return (1 - math.sqrt(1 - math.pow(2 * x, 2))) / 2
    else:
        return (math.sqrt(1 - math.pow(-2 * x + 2, 2)) + 1) / 2


def ease_hold_center_circ(x):
    """Elasticly cling to 0.5"""
    if x < 0.5:
        return ease_out_circ(x * 2) / 2
    else:
        return 1 - (ease_out_circ((x - 0.5) * 2) / 2)


def ping_pong(value,maximum):
    odd_pong = (int(value / maximum) % 2 == 1)
    mod = value % maximum
    if odd_pong:
        return maximum - mod
    else:
        return mod


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ debug ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def advance_clock():
    """Advance the system clock,
    used to rapdidly test different times
    """
    _ADVANCE_SECONDS = const(60 * 30)
    
    epoch = time.time()
    epoch += _ADVANCE_SECONDS
    
    time_tuple = time.localtime(epoch)
    
    rtc_time_list = list(RTC.datetime())
    for i in range(5):
        rtc_time_list[i] = time_tuple[i]
    
    
    RTC.init(tuple(rtc_time_list))

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Graphics! ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def draw_sky():
    colors = data_parser.CURRENT_COLORS
    
    DISPLAY.v_gradient(0,0, _WIDTH, _SKY_START_HEIGHT, colors['sky_top'], colors['sky_mid'])
    DISPLAY.v_gradient(0,_SKY_START_HEIGHT, _WIDTH, _SKY_MID_HEIGHT, colors['sky_mid'], colors['sky_bottom'])


    
def draw_beach():
    colors = data_parser.CURRENT_COLORS
    DISPLAY.v_gradient(0, _SKY_HEIGHT, _WIDTH, _BEACH_HEIGHT, colors['beach_top'], colors['beach_bottom'])   


def draw_sun():
    _SUN_MIN_X = const(80)
    _SUN_MAX_X = const(_WIDTH - _SUN_MIN_X)
    _SUN_X_RANGE = const(_SUN_MAX_X - _SUN_MIN_X)
    
    color = data_parser.CURRENT_COLORS['sun']
    
    altitude = data_parser.SUN_DATA['sun_position']['altitude']
    # adjust so that sun is on horizon during sunset
    altitude -= SUNSET_POINT_DEGREES / 2
    
    # get/format aziumuth
    # -180 to +180:
    azimuth = data_parser.SUN_DATA['sun_position']['azimuth']
    # 0 to 360:
    azimuth %= 360
    # flatten so that 360 == 0 (and value is 0 to 180)
    azimuth = ping_pong(azimuth, 180)
    # 0.0 to 1.0
    azimuth /= 180
    # get x position based on azimuth
    azimuth = ease_in_out_circ(azimuth)
    #azimuth = ease_hold_center_circ(azimuth)
    sun_x = int(_SUN_X_RANGE * azimuth) + _SUN_MIN_X
    
    
    if altitude > 0:
        position_fac = data_parser.get_factor(0, altitude, 90)
        position = int(_SKY_HEIGHT - (_SKY_HEIGHT * position_fac))
    else:
        position_fac = data_parser.get_factor(0, -altitude, 90)
        position = int(_SKY_HEIGHT + (_SKY_HEIGHT * position_fac * 2))

    # draw moon only if sun out of view
    if position > _SKY_HEIGHT_MOON_START:
        draw_moon(position)
        
    if position < _SKY_HEIGHT_SUN_STOP:
        # main sun
        DISPLAY.glow_circle(sun_x, position, 20, 60, color)
        
        # white glow in center
        DISPLAY.glow_circle(sun_x, position, 10, 20, (0.13,1,1))
        
        
def draw_moon(sun_position):
    
    altitude = data_parser.SUN_DATA['moon_position']['altitude']
    
    azimuth = data_parser.SUN_DATA['moon_position']['azimuth']
    # 0 to 360:
    azimuth %= 360
    # flatten so that 360 == 0 (and value is 0 to 180)
    azimuth = ping_pong(azimuth, 180)
    # 0.0 to 1.0
    azimuth /= 180
    # get x position based on azimuth
    azimuth = ease_in_out_circ(azimuth)
    #azimuth = ease_hold_center_circ(azimuth)
    moon_x = int(_SUN_X_RANGE * azimuth) + _SUN_MIN_X
    
    
    height_factor = 1 - data_parser.get_factor(_SKY_HEIGHT_MOON_START, sun_position, _SKY_HEIGHT_SUN_STOP)
    
    if altitude > 0:
        position_fac = data_parser.get_factor(0, altitude, 90)
        position = int(_SKY_HEIGHT - (_SKY_HEIGHT * position_fac))
    else:
        position_fac = data_parser.get_factor(0, -altitude, 90)
        position = int(_SKY_HEIGHT + (_SKY_HEIGHT * position_fac * 2))
        
    # make moon pop up smoothly
    position += int(height_factor * _HEIGHT)
    
    
    fraction = data_parser.SUN_DATA['moon_illumination']['fraction']
    # dont draw moon if it's a 'new moon'
    if fraction > 0.05:
        # sample color behind moon (for shadow)
        bg_clr = DISPLAY.color_pick(moon_x, position)
        
        DISPLAY.glow_circle(moon_x, position, 18,24, (0.5, 0.5, 0.5))
        
        
        # if moon is not full, draw a shadow on it:
        if fraction < 0.95:
            
            DISPLAY.ellipse(
                moon_x - int(36 * fraction),
                position, 20,20,
                bg_clr, True)


@micropython.viper
def blend_color_fast(rgb1:int, rgb2:int) -> int:
    # assume first color is from fbuf, unswap it
    rgb1 = ((rgb1 & 255) << 8) + (rgb1 >> 8)
    
    # split color components
    red = (rgb1 >> 11) & 0x1F
    green = (rgb1 >> 5) & 0x3F
    blue = rgb1 & 0x1F
    
    # add second components
    red += (rgb2 >> 11) & 0x1F
    green += (rgb2 >> 5) & 0x3F
    blue += rgb2 & 0x1F
    
    # divide to get avg
    red //= 2
    green //= 2
    blue //= 2
    
    # recombine components and reswap
    rgb = (red << 11) | (green << 5) | blue
    rgb = ((rgb & 255) << 8) + (rgb >> 8)
    
    return rgb

@micropython.viper
def _mirror_water(x_start:int,y_start:int,width:int,height:int, buffer, colors):
    #buffer = bytearray(width * height * 2)
    buf_ptr = ptr16(buffer)
    
    for y in range(height):
        for x in range(width):
            target_y = y_start + y
            target_x = x_start + x
            
            
            #source_y = y_start - y - 1
            # add 'stretching' effect to reflection
            if y % 3 == 0:
                source_y = y_start - ((y * 12) // 13) - 1
            elif y % 3 == 1:
                source_y = y_start - ((y * 4) // 5) - 1
            else:
                source_y = y_start - y - 1
            
            # add ripples
            if not (y < 2 or y > height - 3):
                if x % 2 == 0:
                    source_y += (x + y) % 3
                else:
                    source_y -= (x + y) % 3

            
            target_idx = (target_y) + (target_x * _HEIGHT)
            source_idx = (source_y) + (target_x * _HEIGHT)

            
            buf_ptr[target_idx] = int(blend_color_fast(buf_ptr[source_idx], colors[y]))

def combine_color565(red, green, blue):
    """
    Combine red, green, and blue components into a 16-bit 565 encoding.
    """
    # Ensure color values are within the valid range
    red = max(0, min(red, 31))
    green = max(0, min(green, 63))
    blue = max(0, min(blue, 31))

    # Pack the color values into a 16-bit integer
    return (red << 11) | (green << 5) | blue

@micropython.native
def hsv_to_rgb(h, s, v):
    '''
    Convert an RGB float to an HSV float.
    From: cpython/Lib/colorsys.py
    '''
    if s == 0.0:
        return v, v, v
    i = int(h*6.0)
    f = (h*6.0) - i
    p = v*(1.0 - s)
    q = v*(1.0 - s*f)
    t = v*(1.0 - s*(1.0-f))
    i = i % 6
    if i == 0:
        return v, t, p
    if i == 1:
        return q, v, p
    if i == 2:
        return p, v, t
    if i == 3:
        return p, q, v
    if i == 4:
        return t, p, v
    if i == 5:
        return v, p, q
    # Cannot get here

@micropython.native
def HSV(h,s=0,v=0):
    """Convert HSV vals into 565 value used by display."""
    if type(h) == tuple:
        h,s,v = h
    
    red, green, blue = hsv_to_rgb(h,s,v)
    
    red = int(red * 31)
    green = int(green * 63)
    blue = int(blue * 31)
    
    return combine_color565(red, green, blue)

def draw_stars():
    _MAX_STARS = const(1000)
    colors = (65088, 63421, 65535, 64640, 61374, 65472, 42080, 58897, 61257, 65534, 63451, 65510)
    
    # number of stars are based on the altitude of sun.
    # This lets us see more stars the later it is.
    altitude = data_parser.SUN_DATA['sun_position']['altitude']
    # no point drawing if sun above horizon
    if altitude > 0:
        return
    
    # convert to floating point representation of num stars
    altitude = (altitude * -1) / 90
    
    num_stars = int(_MAX_STARS * altitude)
    for i in range(num_stars):
        # draw each star with a random position
        x = random.randint(0,_WIDTH)
        y = random.randint(0,_SKY_HEIGHT)
        clr = random.choice(colors)
        
        # fac representing individual star height
        fac = (1 - y / _SKY_HEIGHT) * random.randint(0,100)
        
        DISPLAY.add_pixel(x,y,clr,int(fac))
    
    

def draw_water():
    _WATER_MINIMUM = const(16)
    _WATER_RANGE = const(_BEACH_HEIGHT - _WATER_MINIMUM)
    
    
    clr1 = data_parser.CURRENT_COLORS['water_top']
    clr2 = data_parser.CURRENT_COLORS['water']
    #clr = HSV(clr)
    
    # min/max data pulled from https://tides.gc.ca/en/stations/07707
    height = int(
            get_factor(
            -0.12,
            data_parser.TIDE_LEVEL,
            5.77,
            ) * _WATER_RANGE
        ) + _WATER_MINIMUM
    
    clrs = []
    for i in range(height):
        fac = i / (height-1)
        clrs.append(
            HSV(display.mix_hsv_in_rgb(clr1, clr2, fac))
            )

    _mirror_water(0, _SKY_HEIGHT, _WIDTH, height, DISPLAY.buf, clrs)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main! ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main_loop():
    
    # init timer to update backlight regularly
    BL_TIMER.init(period=20, mode=Timer.PERIODIC, callback=set_backlight_from_sensor)
    
    # collect data to start
    if not _SUPRESS_TIME_SYNC:
        data_parser.update_data_internet()
    data_parser.update_data_calculate()
    # remember how long since we last updated
    last_internet_update = time.time()
    
    counter = 12
    while True:
        # init random with current time in hours.
        # This lets the contents of the loop be different every hour, without changing every single frame
        random.seed(time.time() // 3600)
        
        
        # when it has been more than _RELOAD_DATA_SECONDS, reload our data
        if time.time() - last_internet_update >= _RELOAD_DATA_SECONDS and not _SUPRESS_TIME_SYNC:
            #print(time.time() - last_internet_update)
            data_parser.update_data_internet()
            last_internet_update = time.time()
        
        
        # update calculated data every cycle
        epoch = time.time()
        if _FAST_CLOCK:
            epoch += _ADVANCE_SECONDS * counter
        
        do_full_calc = (counter % 3 == 0)
        data_parser.update_data_calculate(date=epoch, full=do_full_calc)
        
        
        # graphics:
        draw_sky()
        draw_stars()
        draw_sun()
        draw_beach()
        draw_water()
        
        # add overlay to display
        DISPLAY.overlay_color(HSV(data_parser.CURRENT_OVERLAY), 100)
        
        DISPLAY.show()
        
            
        localtime = time.localtime(epoch)
        print(f"Time: {(localtime[3]-7)%24}:{localtime[4]}")
        print(f"Altitude: {data_parser.SUN_DATA['sun_position']['altitude']}, Azimuth: {data_parser.SUN_DATA['sun_position']['azimuth']}")
        counter += 1
        if counter > 1000:
            counter = 0
    
# for testing, catch exceptions to deinit timer/display
try:
    main_loop()
except KeyboardInterrupt as e:
    print(e)
    BL_TIMER.deinit()
    DISPLAY.tft.deinit()