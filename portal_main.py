import time
import lightsensor
import display
from machine import Pin, freq, PWM, Timer


# debug tools:
_FORCE_MAX_LIGHT_ = True


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ _CONSTANTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

_BLIGHT_MAX = const(65535)
_WIDTH = const(272)
_HEIGHT = const(480)

# sky size
_SKY_HEIGHT = const((_HEIGHT * 2) // 3)
_SKY_START_HEIGHT = const((_SKY_HEIGHT * 2) // 3)
_SKY_MID_HEIGHT = const(_SKY_HEIGHT-_SKY_START_HEIGHT)

_BEACH_HEIGHT = const(_HEIGHT - _SKY_HEIGHT)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ GLOBALS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


SENSOR = lightsensor.LightSensor()
BLIGHT = PWM(Pin(1, Pin.OUT))
DISPLAY = display.Display()


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





# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main! ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main_loop():
    
    
    BL_TIMER.init(period=10, mode=Timer.PERIODIC, callback=set_backlight_from_sensor)
    
    loop_counter = 0
    while True:
        start_time = time.ticks_ms()
        DISPLAY.v_gradient(0,0, _WIDTH, _SKY_START_HEIGHT, (0.39444,0.29,1.0), (0.9194445,0.28,0.60))
        DISPLAY.v_gradient(0,_SKY_START_HEIGHT, _WIDTH, _SKY_MID_HEIGHT, (0.9194445,0.28,0.60), (0.17222,0.87,0.97))
        
        DISPLAY.v_gradient(0, _SKY_HEIGHT, _WIDTH, _BEACH_HEIGHT, (0.0, 0.6, 0.8157), (0.9594723, 0.5, 0.14))
        time_diff = time.ticks_diff(time.ticks_ms(), start_time)
        
        DISPLAY.show()
        print(f"Drawing took {round(time_diff / 1000, 2)} seconds.")
        time.sleep(1)
        break
    
# for testing, catch exceptions to deinit timer/display
try:
    main_loop()
except Exception as e:
    print(e)
    BL_TIMER.deinit()
    DISPLAY.tft.deinit()