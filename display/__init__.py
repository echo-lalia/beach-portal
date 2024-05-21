from display import tft_config
from display.tft_config import color565
import framebuf, math

# debug helper; speed up rendering by using shortcuts
_FAST_RENDER = False

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
    def __init__(self, invert_y = True, invert_x = True):
        self.tft = tft_config.config()
        self.width = self.tft.width()
        self.height = self.tft.height()
        self.invert_y = invert_y
        self.invert_x = invert_x
        
        self.buf = bytearray(self.width * self.height * 2)
        
        self.fbuf = framebuf.FrameBuffer(
            self.buf,
            self.width, self.height,
            framebuf.RGB565
            )
        
    def get_pixel(self, x, y):
        """This method is needed because fbuf.pixel cant accept None for color."""
        clr = self.fbuf.pixel(y,x)
        if clr is None:
            return (0,0,0)
        return RGB565_to_HSV(swap_bytes(clr))
    
    def color_pick(self,x,y):
        """Like get_pixel, but take muliple samples for higher quality."""
        samples = []
        
        x -= 1
        y -= 1
        
        for i in range(9):
            ix = i % 3
            iy = i // 3
            sample = self.fbuf.pixel(y + iy, x + ix)
            if sample is not None:
                samples.append(swap_bytes(sample))
        
        red, green, blue = 0,0,0
        
        if len(samples) == 0:
            return (0,0,0)
        
        for sample in samples:
            r, g, b = separate_color565(sample)
            red += r
            green += g
            blue += b
        
        red //= len(samples)
        green //= len(samples)
        blue //= len(samples)
        
        return RGB565_to_HSV(combine_color565(red, green, blue))
        
    
    def pixel(self, x, y, color):
        self.fbuf.pixel(y, x, color)
        
    def mix_pixel(self, x, y, color, percent=100):
        bg = self.fbuf.pixel(y,x)
        if bg is None:
            return
        bg = swap_bytes(bg)
        color = self.mix_viper(bg, color, percent)
        self.fbuf.pixel(y, x, swap_bytes(color))
        
    def add_pixel(self, x, y, color, percent=100):
        bg = self.fbuf.pixel(y,x)
        if bg is None:
            return
        bg = swap_bytes(bg)
        color = self.add_viper(bg, color, percent)
        self.fbuf.pixel(y, x, swap_bytes(color))
        
    def overlay_pixel(self, x, y, color, percent=100):
        bg = self.fbuf.pixel(y,x)
        if bg is None:
            return
        bg = swap_bytes(bg)
        color = self.overlay_viper(bg, color, percent)
        self.fbuf.pixel(y, x, swap_bytes(color))
    
    def multiply_pixel(self, x, y, color, percent=100):
        bg = self.fbuf.pixel(y,x)
        if bg is None:
            return
        bg = swap_bytes(bg)
        color = self.multiply_viper(bg, color, percent)
        self.fbuf.pixel(y, x, swap_bytes(color))
    
    def hline(self, x, y, width, color):
        color = HSV(color)
        self.fbuf.vline(y,x,width, color)
    
    def fill(self, color):
        self.fbuf.fill(HSV(color))
    
    def ellipse(self, x, y, r1, r2, color, f=False):
        color = HSV(color)
        self.fbuf.ellipse(y,x,r2,r1,color, f)
    
    def rect(self, x, y, w, h, color, fill=False):
        color = HSV(color)
        self.fbuf.rect(y, x, h, w, color, fill)
    
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
        if _FAST_RENDER:
            self.hline(x, y, width, color)
            return
        
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
    
#     @staticmethod
#     def overlay_val_float(a,b):
#         if a < 0.5:
#             return 2 * a * b
#         else:
#             return 1 - (2 * (1 - a) * (1 - b))
            
#     @staticmethod
#     @micropython.native
#     def overlay_floats(clr1, clr2, multi=1):
#         r1,g1,b1 = separate_color565(clr1)
#         r2,g2,b2 = separate_color565(clr2)
#         
#         r1 /= 31; g1 /= 63; b1 /= 31
#         r2 /= 31; g2 /= 63; b2 /= 31
#         
#         red = (Display.overlay_val_float(r1, r2) * multi) + (r1 * (1-multi))
#         green = (Display.overlay_val_float(g1, g2) * multi) + (g1 * (1-multi))
#         blue = (Display.overlay_val_float(b1, b2) * multi) + (b1 * (1-multi))
#         
#         red *= 31
#         green *= 63
#         blue *= 31
#         
#         
#         return combine_color565(
#             int(red),
#             int(green),
#             int(blue))
#     
#     @staticmethod
#     @micropython.native
#     def _float_overlay_component(a,b,mul):
#         """Helper for the viper function, for the one part that can't use int math"""
#         return int((1 - (2 * (1 - (a/mul)) * (1 - (b/mul)))) * mul)


    @staticmethod
    @micropython.viper
    def mix_viper(clr1:int, clr2:int, percentage:int=100) -> int:
        """Fast viper function for mixing two colors."""
        # separate rgb565
        r1 = (clr1 >> 11) & 0x1F
        g1 = (clr1 >> 5) & 0x3F
        b1 = clr1 & 0x1F
        
        r2 = (clr2 >> 11) & 0x1F
        g2 = (clr2 >> 5) & 0x3F
        b2 = clr2 & 0x1F
        
        # apply percentages
        bg_percent = 100 - percentage
        
        red = (r2 * percentage + r1 * bg_percent) // 100
        green = (g2 * percentage + g1 * bg_percent) // 100
        blue = (b2 * percentage + b1 * bg_percent) // 100
        
        if red > 31:
            red = 31
        if green > 63:
            green = 63
        if blue > 31:
            blue = 31
        
        # combine color565
        return (red << 11) | (green << 5) | blue
    
    @staticmethod
    @micropython.viper
    def multiply_viper(clr1:int, clr2:int, percentage:int=100) -> int:
        """Fast viper function for adding two colors."""
        # separate rgb565
        r1 = (clr1 >> 11) & 0x1F
        g1 = (clr1 >> 5) & 0x3F
        b1 = clr1 & 0x1F
        
        r2 = (clr2 >> 11) & 0x1F
        g2 = (clr2 >> 5) & 0x3F
        b2 = clr2 & 0x1F
        
        # preform overlay math on each component pair
        # this would be better to read if it were separated to another function,
        # however it's faster if it's all inline
        red = (r1 * r2) // 31
        green = (g1 * g2) // 63
        blue = (b1 + b2) // 31
        
        # apply percentages
        bg_percent = 100 - percentage
        
        red = (red * percentage + r1 * bg_percent) // 100
        green = (green * percentage + g1 * bg_percent) // 100
        blue = (blue * percentage + b1 * bg_percent) // 100
        
        if red > 31:
            red = 31
        if green > 63:
            green = 63
        if blue > 31:
            blue = 31
        
        # combine color565
        return (red << 11) | (green << 5) | blue

    @staticmethod
    @micropython.viper
    def add_viper(clr1:int, clr2:int, percentage:int=100) -> int:
        """Fast viper function for adding two colors."""
        # separate rgb565
        r1 = (clr1 >> 11) & 0x1F
        g1 = (clr1 >> 5) & 0x3F
        b1 = clr1 & 0x1F
        
        r2 = (clr2 >> 11) & 0x1F
        g2 = (clr2 >> 5) & 0x3F
        b2 = clr2 & 0x1F
        
        # preform overlay math on each component pair
        # this would be better to read if it were separated to another function,
        # however it's faster if it's all inline
        red = r1 + r2
        green = g1 + g2
        blue = b1 + b2
        
        # apply percentages
        bg_percent = 100 - percentage
        
        red = (red * percentage + r1 * bg_percent) // 100
        green = (green * percentage + g1 * bg_percent) // 100
        blue = (blue * percentage + b1 * bg_percent) // 100
        
        if red > 31:
            red = 31
        if green > 63:
            green = 63
        if blue > 31:
            blue = 31
        
        # combine color565
        return (red << 11) | (green << 5) | blue

    @staticmethod
    @micropython.viper
    def overlay_viper(clr1:int, clr2:int, percentage:int=100) -> int:
        """Fast viper function for overlaying two colors."""
        # separate rgb565
        r1 = (clr1 >> 11) & 0x1F
        g1 = (clr1 >> 5) & 0x3F
        b1 = clr1 & 0x1F
        
        r2 = (clr2 >> 11) & 0x1F
        g2 = (clr2 >> 5) & 0x3F
        b2 = clr2 & 0x1F
        
        # preform overlay math on each component pair
        # this would be better to read if it were separated to another function,
        # however it's faster if it's all inline
        if r1 < (15):
            red = (2 * r1 * r2) // 31
        else:
            # invert colors
            # multiply
            red = (2 * (31 - r1) * (31 - r2)) // 31
            #uninvert output
            red = 31 - red
        
        if g1 < (31):
            green = (2 * g1 * g2) // 63
        else:
            # invert colors
            # multiply
            green = (2 * (63 - g1) * (63 - g2)) // 63
            #uninvert output
            green = 63 - green
        
        if b1 < (15):
            blue = (2 * b1 * b2) // 31
        else:
            # invert colors
            # multiply
            blue = (2 * (31 - b1) * (31 - b2)) // 31
            #uninvert output
            blue = 31 - blue
        
        # apply percentages
        bg_percent = 100 - percentage
        
        red = (red * percentage + r1 * bg_percent) // 100
        green = (green * percentage + g1 * bg_percent) // 100
        blue = (blue * percentage + b1 * bg_percent) // 100
        
        # combine color565
        return (red << 11) | (green << 5) | blue
    

    @micropython.viper
    def overlay_color(self, color:int, percentage:int, mix_color:int, mix_opacity:int):
        """Overlay (and normal mix) a given color over entire framebuffer."""
        _ALL_RGB_BYTES = const(65535 * 2)
        
        buf = self.buf
        buf_ptr = ptr16(self.buf)
        buf_len = int(len(buf)) // 2
        
        # abuse our 8mb psram, and just make room to store every possible color
        color_cache = bytearray(_ALL_RGB_BYTES)
        cache_ptr = ptr16(color_cache)
        
        # Iterate through every pixel
        for i in range(0, buf_len):
            source_clr = buf_ptr[i]
                
            # check if we have cached color (make the assumption that 0 is uncached)
            if cache_ptr[source_clr] != 0:
                buf_ptr[i] = cache_ptr[source_clr]
                
            # otherwise, calculate, and store result
            else:
                # un-swap bytes
                clr = ((source_clr & 255) << 8) + (source_clr >> 8)
                if mix_opacity != 0:
                    # add mix color
                    clr = int(self.mix_viper(clr, mix_color, mix_opacity))
                # get overlay color
                clr = int(self.overlay_viper(clr, color, percentage))
                
                # re-swap bytes
                clr = ((clr & 255) << 8) + (clr >> 8)
                
                # cache result
                cache_ptr[source_clr] = clr
                # display results
                buf_ptr[i] = clr

    
    @micropython.viper
    def _invert_buffer(self, buffer):
        """Invert our rgb565 framebuffer using set mirror values."""
        width = int(self.width)
        height = int(self.height)

        x_start = int(self.width) - 1 if self.invert_x else 0
        y_start = int(self.height) - 1 if self.invert_y else 0
        
        x_step = -1 if self.invert_x else 1
        y_step = -1 if self.invert_y else 1
        
        source_ptr = ptr16(self.buf)
        target = bytearray(width * height * 2)
        target_ptr = ptr16(target)
        
        for y in range(0, height):
            for x in range(0, width):
                target_x = x_start + (x * x_step)
                target_y = y_start + (y * y_step)
                
                target_idx = (target_y * width) + target_x
                source_idx = (y * width) + x
                
                target_ptr[target_idx] = source_ptr[source_idx]
        
        return target
        
    def show(self):
        if self.invert_x or self.invert_y:
            buf = self._invert_buffer(self.buf)
        else:
            buf = self.buf
        
        self.tft.bitmap(0,0, self.width, self.height, buf)
        
    @micropython.native
    def hline_circle(self, x, y, size, colors):
        """Designed for glow circle,
        this function draws a circle with hlines,
        and each hline can have a specified color.
        """
        if _FAST_RENDER:
            self.ellipse(x, y, size//2, size//2, colors[len(colors)//2], f=True)
            return
        
        y -= size // 2 # center y
        for i in range(size):
            fac = ((i + 1) / (size))
            
            if fac < 0.5:
                fac = ease_out_circ((fac + fac))
            else:
                fac = 1 - ease_in_circ((fac - 0.5) * 2)
                
            width = int(size * fac)
            self.dithered_hline(x - (width // 2), y + i, width, colors[i])


    @micropython.native
    def glow_circle(self, x, y, inner_radius, outer_radius, color, steps=10):
        if _FAST_RENDER:
            self.ellipse(x, y, inner_radius, inner_radius, color, f=True)
            return

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
    
    def blit_framebuf(self, fbuf, x, y, key=-1, palette=None):
        """
        Copy buffer to display framebuf at the given location.

        Args:
            buffer (bytes): Data to copy to display
            x (int): Top left corner x coordinate
            Y (int): Top left corner y coordinate
            width (int): Width
            height (int): Height
            key (int): color to be considered transparent
            palette (framebuf): the color pallete to use for the buffer
        """
        self.fbuf.blit(fbuf, x, y, key, palette)
    
    def blit_buffer(self, buffer, x, y, width, height, key=-1, palette=None):
        """
        Copy buffer to display framebuf at the given location.

        Args:
            buffer (bytes): Data to copy to display
            x (int): Top left corner x coordinate
            Y (int): Top left corner y coordinate
            width (int): Width
            height (int): Height
            key (int): color to be considered transparent
            palette (framebuf): the color pallete to use for the buffer
        """
        self.fbuf.blit(framebuf.FrameBuffer(buffer, width, height, framebuf.RGB565), x, y, key, palette)

    def bitmap_icons(self, bitmap_module, bitmap, color, x, y, invert_colors=False, index=0):
        """
        Draw a 2 color bitmap as a transparent icon on display,
        at the specified column and row, using given color and memoryview object.
        
        This function was particularly designed for use with MicroHydra Launcher,
        but could probably be useful elsewhere too.

        Args:
            (bitmap_module): The module containing the bitmap to draw
            bitmap: The actual bitmap buffer to draw
            color: the non-transparent color of the bitmap
            x (int): column to start drawing at
            y (int): row to start drawing at
            invert_colors (bool): flip transparent and non-tranparent parts of bitmap.
           
        """
        x, y, = y, x
        
        width = bitmap_module.WIDTH
        height = bitmap_module.HEIGHT
        to_col = x + width - 1
        to_row = y + height - 1
        

        bitmap_size = height * width
        buffer_len = bitmap_size * 2
        bpp = bitmap_module.BPP
        bs_bit = bpp * bitmap_size * index
        needs_swap = True
        buffer = bytearray(buffer_len)
        
        if needs_swap:
            color = swap_bytes(color)
            
        #prevent bg color from being invisible
        if color == 0:
            palette = (65535, color)
        else:
            palette = (0, color)
        
        for i in range(0, buffer_len, 2):
            color_index = 0
            for _ in range(bpp):
                color_index = (color_index << 1) | (
                    (bitmap[bs_bit >> 3] >> (7 - (bs_bit & 7))) & 1
                )
                bs_bit += 1

            color = palette[color_index]

            buffer[i] = color & 0xFF
            buffer[i + 1] = color >> 8

        
        self.blit_buffer(buffer,x,y,width,height,key=palette[0])
    
    
    def bitmap(self, bitmap, x, y, index=0, key=-1, palette=None):
        """
        Draw a bitmap on display at the specified column and row

        Args:
            bitmap (bitmap_module): The module containing the bitmap to draw
            x (int): column to start drawing at
            y (int): row to start drawing at
            index (int): Optional index of bitmap to draw from multiple bitmap
                module
            key (int): colors that match they key will be transparent.
        """
        x, y = y, x
        width = bitmap.WIDTH
        height = bitmap.HEIGHT
        to_col = x + width - 1
        to_row = y + height - 1

        bitmap_size = height * width
        buffer_len = bitmap_size * 2
        bpp = bitmap.BPP
        bs_bit = bpp * bitmap_size * index  # if index > 0 else 0
        if palette is None:
            palette = bitmap.PALETTE
        
        #swap colors if needed:
        palette = [swap_bytes(x) for x in palette]
        
        buffer = bytearray(buffer_len)

        for i in range(0, buffer_len, 2):
            color_index = 0
            for _ in range(bpp):
                color_index = (color_index << 1) | (
                    (bitmap.BITMAP[bs_bit >> 3] >> (7 - (bs_bit & 7))) & 1
                )
                bs_bit += 1

            color = palette[color_index]

            buffer[i] = color & 0xFF
            buffer[i + 1] = color >> 8
        
        self.blit_buffer(buffer,x,y,width,height,key=key)
        

    @micropython.viper
    def bitmap_transparent(self, module, fg_clr:int, x:int, y:int, key:int, opacity_percent:int, index:int, mix_func):
        """
        Draw a 2 color bitmap as a transparent icon on display,
        at the specified column and row, using given color and memoryview object.
        
        This function was particularly designed for use with MicroHydra Launcher,
        but could probably be useful elsewhere too.

        Args:
            (bitmap_module): The module containing the bitmap to draw
            bitmap: The actual bitmap buffer to draw
            color: the non-transparent color of the bitmap
            x (int): column to start drawing at
            y (int): row to start drawing at
            invert_colors (bool): flip transparent and non-tranparent parts of bitmap.
           
        """
        x, y, = y, x
        
        # not how this was intended to be used, but works with viper:
        bitmap = ptr8(module._bitmap)
        
        width = int(module.WIDTH)
        height = int(module.HEIGHT)
        to_col = x + width - 1
        to_row = y + height - 1
        
        bitmap_size = height * width
        buffer_len = bitmap_size * 2
        bpp = int(module.BPP)
        bs_bit = bpp * bitmap_size * index
        buffer = bytearray(buffer_len)
            
        
        for i in range(0, buffer_len, 2):
            color_index = 0
            for _ in range(bpp):
                color_index = (color_index << 1) | (
                    (bitmap[bs_bit >> 3] >> (7 - (bs_bit & 7))) & 1
                )
                bs_bit += 1
            
            if color_index == 0:
                color = key
            else:
                ix = (i // 2) % width
                iy = (i // 2) // width
                color = int(mix_func(
                            self.get_pixel_viper(iy + y, ix + x),
                            (fg_clr),
                            opacity_percent,
                            ))

            buffer[i + 1] = color & 0xFF
            buffer[i] = color >> 8

        
        self.blit_buffer(buffer,x,y,width,height,key=key)


    @micropython.viper
    def draw_image_fancy(self, module, color_list, x:int, y:int, key:int, opacity_percent:int):
        x, y, = y, x
        
        bitmap = module.BITMAP
        width = int(module.WIDTH)
        height = int(module.HEIGHT)
        to_col = x + width - 1
        to_row = y + height - 1

        bitmap_size = height * width
        buffer_len = bitmap_size * 2
        bpp = int(module.BPP)
        bs_bit = 0

        buffer = bytearray(buffer_len)
        
#         color = swap_bytes(color)
        
        colors = bytearray(width * 2)
        color_ptr = ptr16(colors)
        # process color_list into color array
        for i in range(width):
            color_ptr[i] = int(HSV(color_list[i]))
        
        
        for i in range(0, buffer_len, 2):
            color_index = 0
            for _ in range(bpp):
                color_index = (color_index << 1) | (
                    (int(bitmap[bs_bit >> 3]) >> (7 - (bs_bit & 7))) & 1
                )
                bs_bit += 1
            
            if color_index == 0:
                color = key
            else:
                ix = (i // 2) % width
                color = color_ptr[ix]
            #color = palette[color_index]

            buffer[i] = color & 0xFF
            buffer[i + 1] = color >> 8

        self.blit_buffer(buffer,x,y,width,height,key=key)
    
    @micropython.viper
    def get_pixel_viper(self, x:int, y:int) -> int:
        """Alternative to 'get_pixel' for viper use."""
        sample = self.fbuf.pixel(y,x)
        if not sample:
            return 0
        
        clr = int(sample)
        
        return ((clr & 255) << 8) + (clr >> 8)

    @micropython.viper
    def draw_image_fancy_trans(self, module, color_list, x:int, y:int, key:int, opacity_percent:int):
        """Just like 'draw_image_fancy, but it uses 3 clrs for varying opacity."""
        x, y, = y, x
        #testlist = []
        
        bitmap = module.BITMAP
        width = int(module.WIDTH)
        height = int(module.HEIGHT)
        to_col = x + width - 1
        to_row = y + height - 1

        bitmap_size = height * width
        buffer_len = bitmap_size * 2
        bpp = int(module.BPP)
        bs_bit = 0

        buffer = bytearray(buffer_len)
        
        colors = bytearray(width * 2)
        color_ptr = ptr16(colors)
        # process color_list into color array
        for i in range(width):
            color_ptr[i] = int(HSV(color_list[i]))
        
        
        for i in range(0, buffer_len, 2):
            color_index = 0
            for _ in range(bpp):
                color_index = (color_index << 1) | (
                    (int(bitmap[bs_bit >> 3]) >> (7 - (bs_bit & 7))) & 1
                )
                bs_bit += 1
            
            if color_index == 0:
                color = key
            else:
                opacity = opacity_percent // 2 if color_index == 1 else opacity_percent
                ix = (i // 2) % width
                iy = (i // 2) // width
                fg_clr = color_ptr[ix]
                color = int(
                    self.mix_viper(
                        self.get_pixel_viper(iy + y, ix + x),
                        ((fg_clr & 255) << 8) + (fg_clr >> 8),
                        opacity,
                    ))
                color = ((color & 255) << 8) + (color >> 8)
                #testlist.append(ix)
            #color = palette[color_index]

            buffer[i] = color & 0xFF
            buffer[i + 1] = color >> 8

        #print(min(testlist), max(testlist))
        self.blit_buffer(buffer,x,y,width,height,key=key)
                
                
        

if __name__ == "__main__":
    #import portal_main
    DISPLAY = Display()
#     DISPLAY.overlay_color(245)
#     import time
#     from machine import Pin
#     
#     blight = Pin(1, Pin.OUT)
#     blight.value(1)
#     DISPLAY = Display()
#     
#     DISPLAY.v_gradient(0,0, 272, 480, (0.69444, 0.71, 0.13), (0.113888, 0.87, 0.98))
#     
#     DISPLAY.glow_circle(100, 50, 20, 40, (0.1,0.4,1.0))
#     
#     DISPLAY.rect(50,0,50,50, (0,0,0), True)
#     
#     DISPLAY.show()
#     
#     time.sleep(5)
#     blight.value(0)