from display import tft_config
from display.tft_config import color565
import framebuf



class Display:
    """
    This class is used to abstract the underlying methods of the display driver,
    and create simple methods for drawing complex objects.
    """
    def __init__(self):
        self.tft = tft_config.config()
        self.width = tft.width()
        self.height = tft.height()
        
        self.fbuf = framebuf.FrameBuffer(
            bytearray(self.width * self.height * 2),
            self.height, self.width,
            framebuf.RGB565
            )
