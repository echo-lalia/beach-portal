import tft_config
from tft_config import color565
import time
import framebuf
import lightsensor
from machine import Pin, freq, PWM



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ _CONSTANTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

_BLIGHT_MAX = const(65535)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ GLOBALS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

TFT = tft_config.config()
SENSOR = lightsensor.LightSensor()
BLIGHT = PWM(Pin(1, Pin.OUT))

WIDTH = TFT.width()
HEIGHT = TFT.height()

FBUF = framebuf.FrameBuffer(
    bytearray(WIDTH * HEIGHT * 2),
    WIDTH, HEIGHT,
    framebuf.RGB565
    )





# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ function defs ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def set_backlight_from_sensor():
    
    reading = SENSOR.read()
    
    BLIGHT.duty_u16(
        int(_BLIGHT_MAX * reading)
        )





# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main! ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main_loop():
    
    loop_counter = 0
    while True:
        set_backlight_from_sensor()
    
    
main_loop()