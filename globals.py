from libtcodpy import *

WINDOW_TITLE = 'Reactor 3 - Milestone 2-2'
WINDOW_SIZE = (100,50)
MAP_SIZE = (100,100,5)
MAP_WINDOW = (40,40)
RUNNING = True
CAMERA_POS = [0,0,2]
FPS = 300
FONT = 'terminal12x12_gs_ro.png'
FONT_LAYOUT = FONT_LAYOUT_ASCII_INCOL
DARK_BUFFER = [[]]
LIGHT_BUFFER = [[]]
RGB_BACK_BUFFER = [[],[],[]]
RGB_FORE_BUFFER = [[],[],[]]
CHAR_BUFFER = [[]]
RENDERER = RENDERER_GLSL
DATA_DIR = 'data'
KEY = Key()
MOUSE = Mouse()
INPUT = {'up':False,
		'down':False,
		'left':False,
		'right':False,
		'space':False,
		'escape':False,
		'a':False,
		'c':False,
		'd':False,
		'1':False,
		'2':False,
		'3':False,
		'4':False,
		'5':False}
GREEN_ALT = Color(0,130,0)
GRASS_GREEN = Color(0, 150, 0)
GRASS_GREEN_DARK = Color(0, 140, 0)
SAND = Color(239,221,111)
BROWN_DARK = Color(123,74,18)
CLAY = Color(228,145,53)
