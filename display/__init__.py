from display import tft_config
from display.tft_config import color565
import framebuf, math

def swap_bytes(color):
    """
    this just flips the left and right byte in the 16 bit color.
    """
    return ((color & 255) << 8) + (color >> 8)

def mix(val2, val1, factor=0.5):
    """Mix two values to the weight of fac"""
    output = (val1 * factor) + (val2 * (1.0 - factor))
    return output

def ease_in_out_sin(x):
    return -(math.cos(math.pi * x) - 1) / 2

def ease_out_cubic(x):
    return 1 - ((1 - x) ** 3)

def ease_in_cubic(x):
    return x * x * x

def ease_in_circ(x):
    return 1 - math.sqrt(1 - (x ** 2))

def ease_out_circ(x):
    return math.sqrt(1 - ((x - 1) ** 2))

def clamp(val, minimum, maximum):
    if val < minimum:
        val = minimum
    elif val > maximum:
        val = maximum
    return val

def ease_in_out_circ(x):
    if x < 0.5:
        return (1 - math.sqrt(1 - math.pow(2 * x, 2))) / 2
    else:
        return (math.sqrt(1 - math.pow(-2 * x + 2, 2)) + 1) / 2

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

def mix_hsv_in_rgb(hsv1, hsv2, factor=0.5):
    """Mix two HSV tuples to the weight of factor,
    Mix the colors in RGB color space.
    """
    r1,g1,b1 = hsv_to_rgb(*hsv1)
    r2,g2,b2 = hsv_to_rgb(*hsv2)
    
    red = mix(r1, r2, factor=factor)
    green = mix(g1, g2, factor=factor)
    blue = mix(b1, b2, factor=factor)
    
    return rgb_to_hsv(red, green, blue)
    
def add_hsv_in_rgb(hsv1, hsv2, factor=0.5):
    """Mix two HSV tuples by adding in RGB,
    factor controls weight of second color.
    """
    r1,g1,b1 = hsv_to_rgb(*hsv1)
    r2,g2,b2 = hsv_to_rgb(*hsv2)
    
    red = clamp(r1 + (r2 * factor), 0, 1)
    green = clamp(g1 + (g2 * factor), 0, 1)
    blue = clamp(b1 + (b2 * factor), 0, 1)
    
    return rgb_to_hsv(red, green, blue)

@micropython.native
def mix_hsv(hsv1, hsv2, factor=0.5):
    """mix two HSV tuples to the weight of factor."""
    h1,s1,v1 = hsv1
    h2,s2,v2 = hsv2
    
    hue = mix_angle_float(h1, h2, factor=factor)
    sat = mix(s1, s2, factor=factor)
    val = mix(v1, v2, factor=factor)
    
    return hue, sat, val
    
@micropython.native
def HSV(h,s=0,v=0):
    """Convert HSV vals into 565 value used by display."""
    if type(h) == tuple:
        h,s,v = h
    
    red, green, blue = hsv_to_rgb(h,s,v)
    
    red = int(red * 31)
    green = int(green * 63)
    blue = int(blue * 31)
    
    return swap_bytes(combine_color565(red, green, blue))

def RGB565_to_HSV(rgb):
    r,g,b = separate_color565(rgb)
    
    r /= 31
    g /= 63
    b /= 31
    
    return rgb_to_hsv(r,g,b)

@micropython.native
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
        (clamp(likely_red, 0, 31), clamp(unlikely_red, 0, 31), (red_error)),
        (clamp(likely_green, 0, 63), clamp(unlikely_green, 0, 63), (green_error)),
        (clamp(likely_blue, 0, 31), clamp(unlikely_blue, 0, 31), (blue_error)),
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
        clr = self.fbuf.pixel(y,x)
        if clr is None:
            return (0,0,0)
        return RGB565_to_HSV(swap_bytes(clr))
        
    def pixel(self, x, y, color):
        self.fbuf.pixel(y, x, color)
    
    def hline(self, x, y, width, color):
        color = HSV(color)
        self.fbuf.vline(y,x,width, color)
    
    def fill(self, color):
        self.fbuf.fill(HSV(color))
    
    def ellipse(self, x, y, r1, r2, color, f=False):
        color = HSV(color)
        self.fbuf.ellipse(y,x,r2,r1,color, f)
    
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
        r_offset = 1 if rm == 0 else (x + y + r1 * r2) % rm
        g_offset = 1 if gm == 0 else (x - y + g2 * b2) % gm
        b_offset = 1 if bm == 0 else (x + y - b1 * g1) % bm
        
        for i in range(width):
            
            r = r2 if r_offset == 0 else r1
            g = g2 if g_offset == 0 else g1
            b = b2 if b_offset == 0 else b1
            
            #rgb = swap_bytes(combine_color565(r, g, b))
            rgb = (r << 11) | (g << 5) | b
            rgb = ((rgb & 255) << 8) + (rgb >> 8)
            
            fbuf.pixel(y, x, rgb)
            
            x += 1
            
            if rm != 0:
                r_offset = (r_offset + 1) % rm
            if gm != 0:
                g_offset = (g_offset + 1) % gm
            if bm != 0:
                b_offset = (b_offset + 1) % bm
            
            
    @micropython.native
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
            r_mod = int(round(1 / r[2])) + 1
            
        if g[2] == 0:
            g_mod = 0
        else:
            g_mod = int(round(1 / g[2])) + 1
            
        if b[2] == 0:
            b_mod = 0
        else:
            b_mod = int(round(1 / b[2])) + 1
        
        self._dithered_hline(
            x, y,
            width,
            r[0], g[0], b[0],
            r[1], g[1], b[1],
            r_mod, g_mod, b_mod,
            )
        
        
        
        
    def show(self):
        self.tft.bitmap(0,0, self.width, self.height, self.fbuf)
        
    @micropython.native
    def hline_circle(self, x, y, size, colors):
        """Designed for glow circle,
        this function draws a circle with hlines,
        and each hline can have a specified color.
        """
        y -= size // 2 # center y
        for i in range(size):
            fac = ((i + 1) / (size))
            
            if fac < 0.5:
                fac = ease_out_circ((fac + fac))
            else:
                fac = 1 - ease_in_circ((fac - 0.5) * 2)
                
            width = int(size * fac)
            self.dithered_hline(x - (width // 2), y + i, width, colors[i])
            #self.hline(x - (width // 2), y + i, width, colors[i])

    @micropython.native
    def glow_circle(self, x, y, inner_radius, outer_radius, color, steps=10):
        size = outer_radius * 2 + 1
        steps = outer_radius - inner_radius
        
        #sample bg colors for transparency
        colors = []
        for i in range(size):
            # take multiple samples because of the dithering
            sample1 = self.get_pixel(x-1, y-outer_radius+i)
            sample2 = self.get_pixel(x+1, y-outer_radius+i)
            colors.append(mix_hsv(sample1, sample2))
            #color = add_hsv_in_rgb(color, RGB565_to_HSV(sample))
            #colors.append(sample1)
        
        for step in range(steps):
        
            fac = ease_in_circ((step+1) / steps)
            blended_colors = [add_hsv_in_rgb(clr, color, factor=fac) for clr in colors]
            
            self.hline_circle(x, y, size, blended_colors)
            
            # reduce size and trim unused colors for next step
            size = size - 2
            colors = colors[1:-1]
            
        
    @micropython.native
    def v_gradient(self, x, y, width, height, start_color, end_color, easing=None):
        fbuf = self.fbuf
        
        for i in range(height):
            
            fac = i / (height - 1)
            if easing:
                fac = easing(fac)
            
            
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
    
    DISPLAY.v_gradient(0,0, 272, 480, (0.69444, 0.71, 0.13), (0.113888, 0.87, 0.98))
    
    DISPLAY.glow_circle(100, 50, 20, 40, (0.1,0.4,1.0))
    
    DISPLAY.show()
    
    time.sleep(5)
    blight.value(0)