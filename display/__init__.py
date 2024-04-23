from display import tft_config
from display.tft_config import color565
import framebuf

def swap_bytes(color):
    """
    this just flips the left and right byte in the 16 bit color.
    """
    return ((color & 255) << 8) + (color >> 8)

def mix(val2, val1, factor=0.5):
    """Mix two values to the weight of fac"""
    output = (val1 * factor) + (val2 * (1.0 - factor))
    return output

def clamp(val, minimum, maximum):
    if val < minimum:
        val = minimum
    elif val > maximum:
        val = maximum
    return val

def mix_angle_float(angle1, angle2, factor=0.5):
    """take two angles as floats (range 0.0 to 1.0) and average them to the weight of factor.
    Mainly for blending hue angles."""
    # Ensure hue values are in the range [0, 1)
    angle1 = angle1 % 1
    angle2 = angle2 % 1

    # Calculate the angular distance between hue1 and hue2
    angular_distance = (angle2 - angle1 + 0.5) % 1 - 0.5
    # Calculate the middle hue value
    blended = (angle1 + angular_distance * factor) % 1

    return blended


def separate_color565(color):
    """
    Separate a 16-bit 565 encoding into red, green, and blue components.
    """
    red = (color >> 11) & 0x1F
    green = (color >> 5) & 0x3F
    blue = color & 0x1F
    return red, green, blue


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


def rgb_to_hsv(r, g, b):
    '''
    Convert an RGB float to an HSV float.
    From: cpython/Lib/colorsys.py
    '''
    maxc = max(r, g, b)
    minc = min(r, g, b)
    rangec = (maxc-minc)
    v = maxc
    if minc == maxc:
        return 0.0, 0.0, v
    s = rangec / maxc
    rc = (maxc-r) / rangec
    gc = (maxc-g) / rangec
    bc = (maxc-b) / rangec
    if r == maxc:
        h = bc-gc
    elif g == maxc:
        h = 2.0+rc-bc
    else:
        h = 4.0+gc-rc
    h = (h/6.0) % 1.0
    return h, s, v


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


def mix_hsv(hsv1, hsv2, factor=0.5):
    """mix two HSV tuples to the weight of factor."""
    h1,s1,v1 = hsv1
    h2,s2,v2 = hsv2
    
    hue = mix_angle_float(h1, h2, factor=factor)
    sat = mix(s1, s2, factor=factor)
    val = mix(v1, v2, factor=factor)
    
    return hue, sat, val
    

def HSV(h,s=0,v=0):
    """Convert HSV vals into 565 value used by display."""
    if type(h) == tuple:
        h,s,v = h
    
    red, green, blue = hsv_to_rgb(h,s,v)
    
    red = int(red * 31)
    green = int(green * 63)
    blue = int(blue * 31)
    
    return swap_bytes(combine_color565(red, green, blue))

def dithered_HSV(h,s=0,v=0):
    """
    Convert HSV into RGB565 as a [3][3] tuple,
    where each r,g,b component is defined as:
    ('likely' component, 'unlikely' component, error/chance)
    
    for use with color dithering.
    """
    if type(h) == tuple:
        h,s,v = h
    
    red, green, blue = hsv_to_rgb(h,s,v)
    
    # exact values
    red = red * 31
    green = green * 63
    blue = blue * 31
    #print(red,green,blue)
    
    likely_red = int(round(red))
    likely_green = int(round(green))
    likely_blue = int(round(blue))
    
    # unlikely color is the exact color, but rounded the other way.
    unlikely_red = likely_red + 1 if likely_red < red else likely_red - 1
    unlikely_green = likely_green + 1 if likely_green < green else likely_green - 1
    unlikely_blue = likely_blue + 1 if likely_blue < green else likely_blue - 1
    
    # error is the distance between the likely color and the exact color
    red_error = abs(red - likely_red)
    green_error = abs(green - likely_green)
    blue_error = abs(blue - likely_blue)
    
    return (
        (clamp(likely_red, 0, 31), clamp(unlikely_red, 0, 31), red_error),
        (clamp(likely_green, 0, 63), clamp(unlikely_green, 0, 63), green_error),
        (clamp(likely_blue, 0, 31), clamp(unlikely_blue, 0, 31), blue_error),
        )

class Display:
    """
    This class is used to abstract the underlying methods of the display driver,
    and create simple methods for drawing complex objects.
    
    Uses HSV for all methods.
    
    Because display is landscape (and doesn't seem to work correctly otherwise?)
    all methods translate x/y coordinates accordingly.
    """
    def __init__(self):
        self.tft = tft_config.config()
        self.width = self.tft.width()
        self.height = self.tft.height()
        
        self.fbuf = framebuf.FrameBuffer(
            bytearray(self.width * self.height * 2),
            self.width, self.height,
            framebuf.RGB565
            )
    def get_pixel(self, x, y):
        """This method is needed because fbuf.pixel cant accept None for color."""
        return self.fbuf.pixel(y,x)
        
    def pixel(self, x, y, color):
        self.fbuf.pixel(y, x, color)
    
    @micropython.viper
    def _dithered_hline(
        self,
        x:int, y:int,
        width:int,
        r1:int, g1:int, b1:int,
        r2:int, g2:int, b2:int,
        rm:int, gm:int, bm:int,
        ):
        """
        fast(er) viper component of dithered hline, to speed rendering up.
        """
        # cache local vars for speed
        fbuf = self.fbuf
        
        # generate 'random' offsets for each component, to reduce color 
        r_offset = 1 if rm == 0 else (x + y + r1) % rm
        g_offset = 1 if gm == 0 else (x - y + g2) % gm
        b_offset = 1 if bm == 0 else (x + y - b1) % bm
        
        for i in range(width):
            
            r = r2 if r_offset == 0 else r1
            g = g2 if g_offset == 0 else g1
            b = b2 if b_offset == 0 else b1
            
            rgb = swap_bytes(combine_color565(r, g, b))
            fbuf.pixel(y, x, rgb)
            
            x += 1
            
            if rm != 0:
                r_offset = (r_offset + 1) % rm
            if gm != 0:
                g_offset = (g_offset + 1) % gm
            if bm != 0:
                b_offset = (b_offset + 1) % bm
            
            
            
    def dithered_hline(self, x, y, width, color):
        """Create an hline, but use dithering to represent exact colors."""
        fbuf = self.fbuf
        
        # get rgb components as (likely, unlikely, error)
        r,g,b = dithered_HSV(color)
        
        # find the modulo; how many time to repeat likely color, before doing unlikely color
        # avoid /0 error
        if r[2] == 0:
            r_mod = 0
        else:
            r_mod = int(round(1 / r[2]))
            
        if g[2] == 0:
            g_mod = 0
        else:
            g_mod = int(round(1 / g[2]))
            
        if b[2] == 0:
            b_mod = 0
        else:
            b_mod = int(round(1 / b[2]))
#         g_mod = int(round(1 / g[2]))
#         b_mod = int(round(1 / b[2]))
        
        self._dithered_hline(
            x, y,
            width,
            r[0], g[0], b[0],
            r[1], g[1], b[1],
            r_mod, g_mod, b_mod,
            )
        
        
        
        
    def show(self):
        self.tft.bitmap(0,0, self.width, self.height, self.fbuf)
        
    def v_gradient(self, x, y, width, height, start_color, end_color):
        fbuf = self.fbuf
        
        for i in range(height):
            
            fac = i / (height - 1)
            
            color = mix_hsv(start_color, end_color, factor=fac)
            
            #fbuf.vline(y+i, x, width, HSV(color))
            self.dithered_hline(x, y+i, width, color)
    
if __name__ == "__main__":
    #import portal_main
    import time
    from machine import Pin
    
    blight = Pin(1, Pin.OUT)
    blight.value(1)
    DISPLAY = Display()
    
    print(DISPLAY.dithered_hline( 10, 100, 100, (0.6083333,0.82,0.69)))
    DISPLAY.show()
    
    time.sleep(2)
    blight.value(0)