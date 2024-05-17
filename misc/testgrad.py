from data_parser import COLORS as colors
import display
from machine import Pin
from images import mountain1


_BLIGHT_MAX = const(65535)
_WIDTH = const(272)
_HEIGHT = const(480)

_CENTER_X = const(_WIDTH//2)
# sky size
_SKY_HEIGHT = const((_HEIGHT * 2) // 3)
_SKY_START_HEIGHT = const((_SKY_HEIGHT * 2) // 3)
_SKY_MID_HEIGHT = const(_SKY_HEIGHT-_SKY_START_HEIGHT)

_BEACH_HEIGHT = const(_HEIGHT - _SKY_HEIGHT)

_BAR_WIDTH = const(_WIDTH // 4)
_BAR_CENTER = const(_BAR_WIDTH // 2)

BLIGHT = Pin(1, Pin.OUT)
DISPLAY = display.Display()
BLIGHT.value(1)

for i in range(4):
    x = _BAR_WIDTH * i
    
    DISPLAY.v_gradient(x,0, _BAR_WIDTH, _SKY_START_HEIGHT, colors['sky_top'][i], colors['sky_mid'][i])
    DISPLAY.v_gradient(x,_SKY_START_HEIGHT, _BAR_WIDTH, _SKY_MID_HEIGHT, colors['sky_mid'][i], colors['sky_bottom'][i])

    # beach
    DISPLAY.v_gradient(x, _SKY_HEIGHT, _BAR_WIDTH, _BEACH_HEIGHT, colors['beach_top'][i], colors['beach_bottom'][i])   
    
    # sun
    position = 90
    
    DISPLAY.ellipse(x + _BAR_CENTER, position, 20, 20, colors['sun'][i], f=True)

mountain_height = _SKY_HEIGHT - mountain1.WIDTH
skymid_offset = mountain_height - _SKY_START_HEIGHT
grad_colors = []
# starting factor 
for i in range(mountain1.WIDTH):
    #fac = ((_SKY_HEIGHT - mountain1.WIDTH + i) - _SKY_MID_HEIGHT) / (_SKY_HEIGHT - _SKY_MID_HEIGHT)
    #print(fac)
    print(skymid_offset, mountain_height, _SKY_MID_HEIGHT)
    fac = (i + skymid_offset) / (mountain1.WIDTH + skymid_offset)
    grad_colors.append(display.mix_hsv(colors['sky_mid'][2], colors['sky_bottom'][2], factor=fac))

DISPLAY.draw_image_fancy(mountain1, grad_colors, 10, mountain_height, 0, 100)
DISPLAY.show()
