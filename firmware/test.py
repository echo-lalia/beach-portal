import tft_config
from tft_config import color565
import time
import framebuf
from machine import Pin, freq

freq(240_000_000)



tft = tft_config.config()
BLIGHT = Pin(1, Pin.OUT)

fbuf = framebuf.FrameBuffer(
    bytearray(tft.width() * tft.height() * 2),
    tft.width(), tft.height(),
    framebuf.RGB565
    )

BLIGHT.value(1)

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
    fbuf.rect(bubble_x, bubble_y, bubble_size, bubble_size, color565(100,100,255), True)
    bubble_x += 1 if moving_down else -1
    bubble_y += 1 if moving_right else -1
    
    if bubble_x <= 1:
        bubble_x = 1
        moving_right = True
    elif bubble_x >= max_width:
        bubble_x = max_width
        moving_right = False
        
    if bubble_y <= 1:
        bubble_y = 1
        moving_down = True
    elif bubble_y >= max_height:
        bubble_y = max_height
        moving_down = False
    
    print(bubble_x, bubble_y)
    tft.bitmap(0,0, width-1, height-1, fbuf)
    
# tft.fill(0)
# tft.fill_rect(50,50,50,50,color565(255,0,0))
# tft.fill_rect(100,100,50,50,color565(0,255,0))
# tft.fill_bubble_rect(120, 200, 40, 80, color565(0,0,255))


try:
    while True:
        bounce_bubble()
        time.sleep_ms(1)
except:
    BLIGHT.value(0)
