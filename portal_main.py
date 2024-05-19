import time
import lightsensor
import display
import machine
from machine import Pin, freq, PWM, Timer
import data_parser
import math
import framebuf
from utils import *
import random
from images import mountain1, mountain2, mountain3, mountain4, title
from array import array
from images import cloud1, cloud2, cloud3, beachdebris

freq(240_000_000)

# debug tools:
_FORCE_MAX_LIGHT_ = False
_FAST_CLOCK = True
_SUPRESS_TIME_SYNC = True


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ _CONSTANTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

_BLIGHT_MAX = const(65535)
#_BLIGHT_MAX = const(10000)
_WIDTH = const(272)
_HEIGHT = const(480)

_CENTER_X = const(_WIDTH//2)

# how often to reload data from internet
_RELOAD_DATA_SECONDS = const(60 * 60)


SUNSET_POINT_DEGREES = math.degrees(data_parser.SUNSET_POINT)

# sky size
_SKY_HEIGHT = const((_HEIGHT * 2) // 3)
_SKY_START_HEIGHT = const((_SKY_HEIGHT * 2) // 3)
_SKY_MID_HEIGHT = const(_SKY_HEIGHT-_SKY_START_HEIGHT)

# when to stop drawing sun/ start drawing moon
_SKY_HEIGHT_MOON_START = const(_SKY_HEIGHT + 10)
_SKY_HEIGHT_SUN_STOP = const(_SKY_HEIGHT_MOON_START + 60)

_BEACH_HEIGHT = const(_HEIGHT - _SKY_HEIGHT)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ GLOBALS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


SENSOR = lightsensor.LightSensor()
BLIGHT = PWM(Pin(1, Pin.OUT))
DISPLAY = display.Display()

RTC = machine.RTC()

WIDTH = DISPLAY.width
HEIGHT = DISPLAY.height

# create backlight timer
BL_TIMER = Timer(3)

WATER_END = _SKY_HEIGHT + 32

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ function defs ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def timer_callback(t):
    set_backlight_from_sensor()

def set_backlight_from_sensor(t=None):
    if _FORCE_MAX_LIGHT_:
        BLIGHT.duty_u16(_BLIGHT_MAX)
        return
    
    BLIGHT.duty_u16(SENSOR.read())
    
def ease_in_sine(x):
  return 1 - math.cos((x * math.pi) / 2)
    
def ease_out_cubic(x):
    return 1 - ((1 - x) ** 3)

    
def ease_out_circ(x):
    return math.sqrt(1 - ((x - 1) ** 2))


def ease_in_out_circ(x):
    if x < 0.5:
        return (1 - math.sqrt(1 - math.pow(2 * x, 2))) / 2
    else:
        return (math.sqrt(1 - math.pow(-2 * x + 2, 2)) + 1) / 2


def ease_hold_center_circ(x):
    """Elasticly cling to 0.5"""
    if x < 0.5:
        return ease_out_circ(x * 2) / 2
    else:
        return 1 - (ease_out_circ((x - 0.5) * 2) / 2)


def ping_pong(value,maximum):
    odd_pong = (int(value / maximum) % 2 == 1)
    mod = value % maximum
    if odd_pong:
        return maximum - mod
    else:
        return mod


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ debug ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def advance_clock():
    """Advance the system clock,
    used to rapdidly test different times
    """
    _ADVANCE_SECONDS = const(60 * 30)
    
    epoch = time.time()
    epoch += _ADVANCE_SECONDS
    
    time_tuple = time.localtime(epoch)
    
    rtc_time_list = list(RTC.datetime())
    for i in range(5):
        rtc_time_list[i] = time_tuple[i]
    
    
    RTC.init(tuple(rtc_time_list))

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Graphics! ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def draw_title():
    _TITLE_X = const(22)
    _TITLE_Y = const(50)
    
    DISPLAY.fill((0.0, 0.0, 0.0))
    
    grad_colors = []
    for i in range(title.WIDTH):
        fac = i / title.WIDTH
        
        # mix mountain and bg gradient colors
        grad_colors.append(
            display.mix_hsv((0.122222, 0.76, 1.0), (0.086, 1.0, 0.8), factor=fac)
            )

    DISPLAY.draw_image_fancy(title, grad_colors, _TITLE_X, _TITLE_Y, 0, 100)
    DISPLAY.show()

def draw_sky():
    colors = data_parser.CURRENT_COLORS
    
    DISPLAY.v_gradient(0,0, _WIDTH, _SKY_START_HEIGHT, colors['sky_top'], colors['sky_mid'])
    DISPLAY.v_gradient(0,_SKY_START_HEIGHT, _WIDTH, _SKY_MID_HEIGHT, colors['sky_mid'], colors['sky_bottom'])


    
def draw_beach():
    colors = data_parser.CURRENT_COLORS
    DISPLAY.v_gradient(0, _SKY_HEIGHT, _WIDTH, _BEACH_HEIGHT, colors['beach_top'], colors['beach_bottom'])   


def draw_sun():
    _SUN_MIN_X = const(80)
    _SUN_MAX_X = const(_WIDTH - _SUN_MIN_X)
    _SUN_X_RANGE = const(_SUN_MAX_X - _SUN_MIN_X)
    
    color = data_parser.CURRENT_COLORS['sun']
    
    altitude = data_parser.SUN_DATA['sun_position']['altitude']
    # adjust so that sun is on horizon during sunset
    altitude -= SUNSET_POINT_DEGREES / 2
    
    # get/format aziumuth
    # -180 to +180:
    azimuth = data_parser.SUN_DATA['sun_position']['azimuth']
    # 0 to 360:
    azimuth %= 360
    # flatten so that 360 == 0 (and value is 0 to 180)
    azimuth = ping_pong(azimuth, 180)
    # 0.0 to 1.0
    azimuth /= 180
    # get x position based on azimuth
    azimuth = ease_in_out_circ(azimuth)
    #azimuth = ease_hold_center_circ(azimuth)
    sun_x = int(_SUN_X_RANGE * azimuth) + _SUN_MIN_X
    
    
    if altitude > 0:
        position_fac = data_parser.get_factor(0, altitude, 90)
        position = int(_SKY_HEIGHT - (_SKY_HEIGHT * position_fac))
    else:
        position_fac = data_parser.get_factor(0, -altitude, 90)
        position = int(_SKY_HEIGHT + (_SKY_HEIGHT * position_fac * 2))

    # draw moon only if sun out of view
    if position > _SKY_HEIGHT_MOON_START:
        draw_moon(position)
        
    if position < _SKY_HEIGHT_SUN_STOP:
        # main sun
        DISPLAY.glow_circle(sun_x, position, 20, 60, color)
        
        # white glow in center
        DISPLAY.glow_circle(sun_x, position, 10, 20, (0.13,1,1))
        
        
def draw_moon(sun_position):
    
    altitude = data_parser.SUN_DATA['moon_position']['altitude']
    
    azimuth = data_parser.SUN_DATA['moon_position']['azimuth']
    # 0 to 360:
    azimuth %= 360
    # flatten so that 360 == 0 (and value is 0 to 180)
    azimuth = ping_pong(azimuth, 180)
    # 0.0 to 1.0
    azimuth /= 180
    # get x position based on azimuth
    azimuth = ease_in_out_circ(azimuth)
    #azimuth = ease_hold_center_circ(azimuth)
    moon_x = int(_SUN_X_RANGE * azimuth) + _SUN_MIN_X
    
    
    height_factor = 1 - data_parser.get_factor(_SKY_HEIGHT_MOON_START, sun_position, _SKY_HEIGHT_SUN_STOP)
    
    if altitude > 0:
        position_fac = data_parser.get_factor(0, altitude, 90)
        position = int(_SKY_HEIGHT - (_SKY_HEIGHT * position_fac))
    else:
        position_fac = data_parser.get_factor(0, -altitude, 90)
        position = int(_SKY_HEIGHT + (_SKY_HEIGHT * position_fac * 2))
        
    # make moon pop up smoothly
    position += int(height_factor * _HEIGHT)
    
    
    fraction = data_parser.SUN_DATA['moon_illumination']['fraction']
    # dont draw moon if it's a 'new moon'
    if fraction > 0.05:
        # sample color behind moon (for shadow)
        bg_clr = DISPLAY.color_pick(moon_x, position)
        
        DISPLAY.glow_circle(moon_x, position, 18,24, (0.5, 0.5, 0.5))
        
        
        # if moon is not full, draw a shadow on it:
        if fraction < 0.95:
            
            DISPLAY.ellipse(
                moon_x - int(36 * fraction),
                position, 20,20,
                bg_clr, True)


@micropython.viper
def blend_color_fast(rgb1:int, rgb2:int) -> int:
    # assume first color is from fbuf, unswap it
    rgb1 = ((rgb1 & 255) << 8) + (rgb1 >> 8)
    
    # split color components
    red = (rgb1 >> 11) & 0x1F
    green = (rgb1 >> 5) & 0x3F
    blue = rgb1 & 0x1F
    
    # add second components
    red += (rgb2 >> 11) & 0x1F
    green += (rgb2 >> 5) & 0x3F
    blue += rgb2 & 0x1F
    
    # divide to get avg
    red //= 2
    green //= 2
    blue //= 2
    
    # recombine components and reswap
    rgb = (red << 11) | (green << 5) | blue
    rgb = ((rgb & 255) << 8) + (rgb >> 8)
    
    return rgb


@micropython.viper
def _mirror_water(x_start:int,y_start:int,width:int,height:int, buffer, colors):
    #buffer = bytearray(width * height * 2)
    buf_ptr = ptr16(buffer)
    
    for y in range(height):
        for x in range(width):
            target_y = y_start + y
            target_x = x_start + x
            
            
            #source_y = y_start - y - 1
            # add 'stretching' effect to reflection
            if y % 3 == 0:
                source_y = y_start - ((y * 12) // 13) - 1
            elif y % 3 == 1:
                source_y = y_start - ((y * 4) // 5) - 1
            else:
                source_y = y_start - y - 1
            
            # add ripples
            if not (y < 2 or y > height - 3):
                if x % 2 == 0:
                    source_y += (x + y) % 3
                else:
                    source_y -= (x + y) % 3

            
            target_idx = (target_y) + (target_x * _HEIGHT)
            source_idx = (source_y) + (target_x * _HEIGHT)

            
            buf_ptr[target_idx] = int(blend_color_fast(buf_ptr[source_idx], colors[y]))


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


@micropython.native
def HSV(h,s=0,v=0):
    """Convert HSV vals into 565 value used by display."""
    if type(h) == tuple:
        h,s,v = h
    
    red, green, blue = hsv_to_rgb(h,s,v)
    
    red = int(red * 31)
    green = int(green * 63)
    blue = int(blue * 31)
    
    return combine_color565(red, green, blue)


def draw_stars():
    _MAX_STARS = const(1000)
    colors = (65088, 63421, 65535, 64640, 61374, 65472, 42080, 58897, 61257, 65534, 63451, 65510)
    
    # number of stars are based on the altitude of sun.
    # This lets us see more stars the later it is.
    altitude = data_parser.SUN_DATA['sun_position']['altitude']
    # no point drawing if sun above horizon
    if altitude > 0:
        return
    
    # convert to floating point representation of num stars
    altitude = (altitude * -1) / 90
    
    num_stars = int(_MAX_STARS * altitude)
    for i in range(num_stars):
        # draw each star with a random position
        x = random.randint(0,_WIDTH)
        y = random.randint(0,_SKY_HEIGHT)
        clr = random.choice(colors)
        
        # fac representing individual star height
        fac = (1 - y / _SKY_HEIGHT) * random.randint(0,100)
        
        DISPLAY.add_pixel(x,y,clr,int(fac))
    
def avg_color565(color_list):
    red, green, blue = 0, 0, 0
    for color in color_list:
        r,g,b = separate_color565(color)
        red += r
        green += g
        blue += b
    red //= len(color_list)
    green //= len(color_list)
    blue //= len(color_list)
    return combine_color565(red, green, blue)

def avg_hsv(color_list):
    output_hsv = (0.0,0.0,0.0)
    for i, clr in enumerate(color_list):
        opacity = 1 / (i + 1)
        output_hsv = display.mix_hsv(output_hsv, clr, opacity)
    return output_hsv
    
def _water_edge_line(y_offsets, y, color, overlay=False, opacity=100):
    # draw each pixel in line
    if not overlay and opacity != 100:
        mix = True
    else:
        mix = False
    
    if overlay or mix: # regular pixel method expects swapped bytes
        clr = HSV(color)
    else:
        clr = display.HSV(color)
    
        
    
    
    for idx, offset in enumerate(y_offsets):
        if overlay:
            DISPLAY.overlay_pixel(idx, offset + y, clr, percent=opacity)
        elif mix:
            DISPLAY.mix_pixel(idx, offset + y, clr, percent=opacity)
        else:
            DISPLAY.pixel(idx, offset + y, clr)
    
    
def draw_water_edge(epoch, y):
    _EDGE_HEIGHT = const(14)
    time_offset = epoch % 314
    
    # generate list of y offsets for water edge
    y_offsets = []
    for i in range(_WIDTH):
        y_offsets.append(
            int(
                (math.sin((i + time_offset) / 60) - (math.pi / 2)) * 3
                )
            )
    
    # sample water edge to find blend color
    clrs = []
    clrs.append(DISPLAY.get_pixel(0, y-1))
    clrs.append(DISPLAY.get_pixel(_WIDTH // 3, y-1))
    clrs.append(DISPLAY.get_pixel((_WIDTH * 2) // 3, y-1))
    clrs.append(DISPLAY.get_pixel(_WIDTH - 1, y-1))
    water_color = avg_hsv(clrs)
    
    # clr, overlay, opacity
    line_list = []
    
    # add water edge ombre colors
    for i in range(_EDGE_HEIGHT):
        fac = i / (_EDGE_HEIGHT - 1)
        clr = display.mix_hsv_in_rgb(
            water_color,
            data_parser.CURRENT_COLORS['water_edge_end'],
            fac)
        line_list.append((clr, False, 100))
    # soften the final water edge (anti-alias)
    line_list.append((data_parser.CURRENT_COLORS['water_edge_end'], False, 33))
    
    # add water overlay to sand
    for i in range(20):
        fac = i / 19
        # reverse and make a slightly hard edge
        fac = ((1.0 - fac) * 0.3) + 0.1
        line_list.append((data_parser.CURRENT_COLORS['water_sand_overlay'], True, int(fac * 100)))
    
    # reverse the last couple of lines to make a harder looking edge
    line_list.append(line_list[-3])
    line_list.append(line_list[-2])
    
    # draw some leading lines to blend everything together
    for i in range(0,8):
        fac = 1 - (i / 7)
        opacity = int(fac * 100)
        _water_edge_line(y_offsets, y - i, water_color, opacity=opacity)

    # draw each line by def
    for idx, line in enumerate(line_list):
        clr, overlay, opacity = line
        _water_edge_line(y_offsets, y + idx, clr, overlay, opacity)
    
    
    # draw some random waves atop water
    # we need random to be changing every second, so we will simply reinit the module with seconds
    random.seed(time.time())
    for idx in range(random.randint(1,5)):
        h_fac = random.random()
        wave_y = y + _EDGE_HEIGHT - int(h_fac * 32)
        
        opacity = int(random.randint(1, 50) * (1 - h_fac))
        clr = data_parser.CURRENT_COLORS['water_edge_end']
        _water_edge_line(y_offsets, wave_y, clr, False, opacity)
    
    

def draw_water():
    _WATER_MINIMUM = const(32)
    _WATER_RANGE = const(_BEACH_HEIGHT - _WATER_MINIMUM)
    
    global WATER_END
    
    
    clr1 = data_parser.CURRENT_COLORS['water_top']
    clr2 = data_parser.CURRENT_COLORS['water']
    #clr = HSV(clr)
    
    # min/max data pulled from https://tides.gc.ca/en/stations/07707
    height = int(
            get_factor(
            -0.12,
            data_parser.TIDE_LEVEL,
            5.77,
            ) * _WATER_RANGE
        ) + _WATER_MINIMUM
    
    clrs = []
    for i in range(height):
        fac = i / (height-1)
        clrs.append(
            HSV(display.mix_hsv_in_rgb(clr1, clr2, fac))
            )

    _mirror_water(0, _SKY_HEIGHT, _WIDTH, height, DISPLAY.buf, clrs)
    
    WATER_END = _SKY_HEIGHT + height + _EDGE_HEIGHT
    
    draw_water_edge(time.time(), _SKY_HEIGHT + height)


def _draw_mountain(x, y_offset, mountain, opacity_start=0.5, opacity_end=1.0):
    # starting Y
    mountain_y = _SKY_HEIGHT - mountain.WIDTH
    # for calculating gradient colors; where is sky mid vs mountain y
    skymid_offset = mountain_y - _SKY_START_HEIGHT
    grad_colors = []
    #opacity = 0.8
    for i in range(mountain.WIDTH):
        fac = (i + skymid_offset) / (mountain.WIDTH + skymid_offset)
        
        # get more solid near bottom
        opacity_factor = mix(opacity_start, opacity_end, fac)
        
        # mix mountain and bg gradient colors
        grad_colors.append(
            display.mix_hsv_in_rgb(
            display.mix_hsv(data_parser.CURRENT_COLORS['sky_mid'], data_parser.CURRENT_COLORS['sky_bottom'], factor=fac),
            data_parser.CURRENT_COLORS['mountain'],
            factor=opacity_factor)
            )

    DISPLAY.draw_image_fancy(mountain, grad_colors, x, mountain_y + y_offset, 0, 100)
    
    
def draw_mountains(epoch):
    if _FAST_CLOCK:
        epoch = epoch // 50
    else:
        epoch = epoch // 800
    
    mountain_x_offset = ping_pong(epoch, _WIDTH)
    mountain_x_fac = mountain_x_offset / _WIDTH
    
    
    
    # mountain3 - back right
    mountain_y_offset = ping_pong(epoch // 10, 11)
    mountain_x = int(ease_out_cubic(mountain_x_fac) * mountain3.HEIGHT) + _WIDTH - mountain3.HEIGHT
    _draw_mountain(mountain_x, mountain_y_offset, mountain3, opacity_start=0.1, opacity_end=0.5)
    
    # mountain4 - back left
    mountain_y_offset = ping_pong(epoch // 12, 10)
    mountain_x = -int(ease_in_sine(mountain_x_fac) * mountain4.HEIGHT)
    _draw_mountain(mountain_x, mountain_y_offset, mountain4, opacity_start=0.15, opacity_end=0.6)
    
    # mountain1 - front right
    mountain_y_offset = ping_pong(epoch // 13, 13)
    mountain_x = int(ease_hold_center_circ(mountain_x_fac) * _WIDTH)
    _draw_mountain(mountain_x, mountain_y_offset, mountain1, opacity_start=0.5, opacity_end=0.8)
    
    # mountain2 - front left
    mountain_y_offset = ping_pong(epoch // 11, 12)
    mountain_x = int(ease_hold_center_circ(mountain_x_fac) * _WIDTH) - mountain2.HEIGHT
    _draw_mountain(mountain_x, mountain_y_offset, mountain2, opacity_start=0.75, opacity_end=0.95)

def _make_color_list(start_clr, end_clr, count):
    grad_colors = []
    for i in range(count):
        fac = i / (count - 1)
        
        # mix mountain and bg gradient colors
        grad_colors.append(
            display.mix_hsv(start_clr, end_clr, factor=fac)
            )
    return grad_colors

def draw_clouds(epoch):
    _MAX_CLOUDS = const(60)
    coverage = data_parser.WEATHER['cloud_cover'] / 100
    num_clouds = int(_MAX_CLOUDS * ease_in_sine(coverage))
    
    # re-init random with current half hour
    random.seed(epoch // 1800)
    
    for i in range(num_clouds):
        cloud = random.choice((cloud1, cloud2, cloud3))
        
        x = random.randint(0,_WIDTH) - (cloud.HEIGHT // 2)
        y = int(ease_in_sine(random.random()) * (_SKY_HEIGHT)) - cloud.WIDTH
        
        opacity = int(50 * coverage) + random.randint(1,50)
        
        clrs = _make_color_list(data_parser.CURRENT_COLORS['cloud_top'], data_parser.CURRENT_COLORS['cloud_bottom'], cloud.WIDTH)
        
        DISPLAY.draw_image_fancy_trans(cloud, clrs, x, y, 0, opacity)


def _desaturate_hsv(hsv, mult = 0.5):
    h,s,v = hsv
    s *= mult
    return h,s,v

def multiply_tuple(t1, t2, maximum=1.0):
    t1 = list(t1)
    for i, mult in enumerate(t2):
        t1[i] *= mult
        if t1[i] > maximum:
            t1[i] = maximum
    return tuple(t1)
        
def _draw_one_wind_line(x, y, length, y_speed, opacity):
    bg_clr = DISPLAY.color_pick(x,y)
    bg_clr = multiply_tuple(bg_clr, (1.0, 0.5, random.uniform(0.8,1.2)))
    for i in range(length):
        ix = x - (length // 2) + i
        iy = y + int(y_speed * i)
        DISPLAY.mix_pixel(ix, iy, HSV(bg_clr), opacity)
        
    
def draw_wind():
    _MAX_WIND = const(60)
    _MIN_WIND = const(10)
    
    wind = data_parser.WEATHER['wind_speed']
    if wind < _MIN_WIND:
        return


    fac = get_factor(_MIN_WIND, wind, _MAX_WIND)

    # reseed for random vals on every frame
    random.seed()
    y_speed = random.uniform(-0.25, 0.25)

    num_lines = int(ease_in_sine(fac) * 400)
    line_len = int(fac * 70) + 10
    opacity = int(fac * 50) + 30
    for i in range(num_lines):
        x = random.randint(0,_WIDTH)
        y = random.randint(0,_HEIGHT)
        _draw_one_wind_line(x, y, line_len, y_speed, opacity)


def _draw_one_rain_line(x, y, length, x_speed, opacity):
    clr = (random.uniform(0.6, 0.663), random.uniform(0.3,1.0), random.uniform(0.33, 0.66))
    
    for i in range(length):
        iy = y - (length // 2) + i
        ix = x + int(x_speed * i)
        
        DISPLAY.overlay_pixel(ix, iy, HSV(clr), opacity)
        #DISPLAY.mix_pixel(ix, iy, HSV(clr), opacity)
        

def draw_rain():
    _MAX_RAIN = const(30)
    _MIN_RAIN = const(0)
    
    rain = data_parser.WEATHER['rain']
    
    fac = get_factor(_MIN_RAIN, rain, _MAX_RAIN)

    # reseed for random vals on every frame
    random.seed()
    x_speed = random.uniform(-0.25, 0.25)

    num_lines = int(ease_in_sine(fac) * 400)
    line_len = int(fac * 80) + 10
    opacity = int(fac * 40) + 10
    for i in range(num_lines):
        x = random.randint(0,_WIDTH)
        y = random.randint(0,_HEIGHT)
        _draw_one_rain_line(x, y, line_len, x_speed, opacity)
        
        
def draw_sand(epoch):
    random.seed(epoch // 10800)
    _NUM_SAND_PARTICLES = const(100)
        
    for i in range(2000):
        x = random.randint(0,_WIDTH)
        y = random.randint(_SKY_HEIGHT, _HEIGHT)
        clr = (random.uniform(0.166, 0.666), random.uniform(0.04, 0.5), random.uniform(0.4, 0.6))
        DISPLAY.overlay_pixel(x, y, HSV(clr), 30)
    

def draw_beach_debris(epoch):
    
    # if water goes all the way (or past) the bottom of screen, no debris should be drawn
    if WATER_END >= _HEIGHT:
        return
    
    random.seed(epoch // 10800)
    
    num_debris = random.randint(3,10)
    for i in range(num_debris):
        x = random.randint(0,_WIDTH)
        y = random.randint(WATER_END, _HEIGHT)
        
        index = random.randint(0,15)
        
        bg_clr = DISPLAY.get_pixel(x, y)
        hue = random.uniform(0.04, 0.119)
        sat = random.uniform(0.0, 0.5)
        #val = clamp(bg_clr[2] + random.uniform(-0.5, 0.2))
        val = random.uniform(0.0, 0.6)
#         clr = display.mix_hsv_in_rgb(
#             bg_clr,
#             (hue, sat, val),
#             0.3,
#             )
        clr = DISPLAY.overlay_viper(
            HSV(bg_clr),
            HSV((hue, sat, val)),
            50
            )
        
        DISPLAY.bitmap_icons(
            beachdebris, beachdebris.BITMAP, clr, x - 8, y, index=index,
            )
    
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main! ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main_loop():
    
    # init timer to update backlight regularly
    BL_TIMER.init(period=20, mode=Timer.PERIODIC, callback=set_backlight_from_sensor)
    
    # collect data to start
    if not _SUPRESS_TIME_SYNC:
        data_parser.update_data_internet()
    data_parser.update_data_calculate()
    # remember how long since we last updated
    last_internet_update = time.time()
    
    counter = 0
    while True:
        # init random with current time in hours.
        # This lets the contents of the loop be different every hour, without changing every single frame
        random.seed(time.time() // 3600)
        
        
        # when it has been more than _RELOAD_DATA_SECONDS, reload our data
        if time.time() - last_internet_update >= _RELOAD_DATA_SECONDS and not _SUPRESS_TIME_SYNC:
            #print(time.time() - last_internet_update)
            data_parser.update_data_internet()
            last_internet_update = time.time()
        
        
        # update calculated data every cycle
        epoch = time.time()
        if _FAST_CLOCK:
            epoch += _ADVANCE_SECONDS * counter
        
        do_full_calc = (counter % 3 == 0)
        data_parser.update_data_calculate(date=epoch, full=do_full_calc)
        
        
        # graphics:
        draw_sky()
        draw_stars()
        draw_sun()
        draw_clouds(epoch)
        draw_beach()
        draw_sand(epoch)
        draw_mountains(epoch)
        draw_water()
        draw_wind()
        draw_rain()
        
        draw_beach_debris(epoch)
        
        # add overlay to display
        DISPLAY.overlay_color(HSV(data_parser.CURRENT_OVERLAY), 100, HSV(data_parser.CURRENT_COLORS['fog']), data_parser.FOG_OPACITY)
        
        DISPLAY.show()
        
        
        localtime = time.localtime(epoch)
        print(f"Time: {(localtime[3]-7)%24}:{localtime[4]}")
        print(f"Altitude: {data_parser.SUN_DATA['sun_position']['altitude']}, Azimuth: {data_parser.SUN_DATA['sun_position']['azimuth']}")
        counter += 1
        if counter > 1000:
            counter = 0


# for testing, catch exceptions to deinit timer/display
try:
    draw_title()
    main_loop()
except KeyboardInterrupt as e:
    print(e)
    BL_TIMER.deinit()
    DISPLAY.tft.deinit()