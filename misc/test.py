import tft_config
from tft_config import color565
import time
import framebuf
from machine import Pin, freq, PWM

freq(160_000_000)



tft = tft_config.config()
BLIGHT = PWM(Pin(1, Pin.OUT))

fbuf = framebuf.FrameBuffer(
    bytearray(tft.width() * tft.height() * 2),
    tft.width(), tft.height(),
    framebuf.RGB565
    )

BLIGHT.freq(1000)
BLIGHT.duty_u16(500)

width = tft.width()
height = tft.height()
bubble_size = 50

max_width = width - bubble_size
max_height = height - bubble_size

bubble_x = 0
bubble_y = 0
moving_down = True
moving_right = True

def bounce_bubble():
    global bubble_x, bubble_y, moving_down, moving_right
    fbuf.fill(0)
    fbuf.rect(bubble_x, bubble_y, bubble_size, bubble_size, color565(255,0,0), True)
    bubble_y += 1 if moving_down else -1
    bubble_x += 1 if moving_right else -1
    
    if bubble_x <= 0:
        bubble_x = 0
        moving_right = True
    elif bubble_x >= max_width:
        bubble_x = max_width
        moving_right = False
        
    if bubble_y <= 0:
        bubble_y = 0
        moving_down = True

    elif bubble_y >= max_height:
        bubble_y = max_height
        moving_down = False
    
#     print(moving_right, moving_down)
#     print(bubble_x, bubble_y)
    tft.bitmap(0,0, width, height, fbuf)
    

try:
    while True:
        bounce_bubble()
        time.sleep_ms(10)
except:
    BLIGHT.duty_u16(0)
