import time
import lightsensor
import display
import machine
from machine import Pin, freq, PWM, Timer
import data_parser

freq(240_000_000)

# debug tools:
_FORCE_MAX_LIGHT_ = True
_FAST_CLOCK = True
_SUPRESS_TIME_SYNC = True


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ _CONSTANTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

_BLIGHT_MAX = const(65535)
_WIDTH = const(272)
_HEIGHT = const(480)

_CENTER_X = const(_WIDTH//2)

# how often to reload data from internet
_RELOAD_DATA_SECONDS = const(60 * 60)

# sky size
_SKY_HEIGHT = const((_HEIGHT * 2) // 3)
_SKY_START_HEIGHT = const((_SKY_HEIGHT * 2) // 3)
_SKY_MID_HEIGHT = const(_SKY_HEIGHT-_SKY_START_HEIGHT)

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
    
    reading = SENSOR.read()
    
    BLIGHT.duty_u16(
        int(_BLIGHT_MAX * reading)
        )

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ debug ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def advance_clock():
    """Advance the system clock,
    used to rapdidly test different times
    """
    _ADVANCE_SECONDS = const(60 * 60)
    
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
    color = data_parser.CURRENT_COLORS['sun']
    
    altitude = data_parser.SUN_DATA['sun_position']['altitude']
    
    if altitude > 0:
        position_fac = data_parser.get_factor(0, altitude, 90)
        position = int(_SKY_HEIGHT - (_SKY_HEIGHT * position_fac))
    else:
        position_fac = data_parser.get_factor(0, -altitude, 90)
        position = int(_SKY_HEIGHT + (_SKY_HEIGHT * position_fac))
    
    DISPLAY.ellipse(_CENTER_X, position, 20, 20, color, f=True)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main! ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main_loop():
    
    # init timer to update backlight regularly
    BL_TIMER.init(period=10, mode=Timer.PERIODIC, callback=set_backlight_from_sensor)
    
    # collect data to start
    if not _SUPRESS_TIME_SYNC:
        data_parser.update_data_internet()
    # remember how long since we last updated
    last_internet_update = time.time()
    
    counter = 0
    while True:
        
        # when it has been more than _RELOAD_DATA_SECONDS, reload our data
        if time.time() - last_internet_update >= _RELOAD_DATA_SECONDS and not _SUPRESS_TIME_SYNC:
            print(time.time() - last_internet_update)
            data_parser.update_data_internet()
            last_internet_update = time.time()
            
        
        # update calculated data every cycle
        epoch = time.time()
        if _FAST_CLOCK:
            epoch += _ADVANCE_SECONDS * counter
        data_parser.update_data_calculate(date=epoch)
        
        
        
        # graphics:
        draw_sky()
        draw_sun()
        draw_beach()
        DISPLAY.show()
        
            
        localtime = time.localtime(epoch)
        print(f"Time: {(localtime[3]-7)%24}:{localtime[4]}")
        
        counter += 1
    
# for testing, catch exceptions to deinit timer/display
try:
    main_loop()
except KeyboardInterrupt as e:
    print(e)
    BL_TIMER.deinit()
    DISPLAY.tft.deinit()