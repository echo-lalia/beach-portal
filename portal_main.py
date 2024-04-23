import time
import lightsensor
import display
from machine import Pin, freq, PWM


# debug tools:
_FORCE_MAX_LIGHT_ = True


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ _CONSTANTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

_BLIGHT_MAX = const(65535)
_WIDTH = const(272)
_HEIGHT = const(480)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ GLOBALS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


SENSOR = lightsensor.LightSensor()
BLIGHT = PWM(Pin(1, Pin.OUT))
DISPLAY = display.Display()


WIDTH = DISPLAY.width
HEIGHT = DISPLAY.height


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ function defs ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def set_backlight_from_sensor():
    if _FORCE_MAX_LIGHT_:
        BLIGHT.duty_u16(_BLIGHT_MAX)
        return
    
    reading = SENSOR.read()
    
    BLIGHT.duty_u16(
        int(_BLIGHT_MAX * reading)
        )





# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main! ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main_loop():
    
    loop_counter = 0
    while True:
        set_backlight_from_sensor()
        DISPLAY.v_gradient(0,0, _WIDTH, _HEIGHT, (0.06388889,0.96,1.0), (0.6083333,0.82,0.69))
        
        DISPLAY.show()
        print('done!')
        time.sleep(1)
        break
main_loop()