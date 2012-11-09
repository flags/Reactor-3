from libtcodpy import *

WINDOW_TITLE = 'Reactor 3 - Milestone 2-3'

#Constants
WINDOW_SIZE = (100,50)
MAP_SIZE = (100,100,5)
MAP_WINDOW_SIZE = (40,40)
ITEM_WINDOW_SIZE = (10,1)
CONSOLE_WINDOW_SIZE = (40,30)
RUNNING = True
CURSOR = [0,0]
CAMERA_POS = [0,0,2]
FPS = 300
FONT = 'terminal12x12_gs_ro.png'
FONT_LAYOUT = FONT_LAYOUT_ASCII_INCOL
DARK_BUFFER = [[]]
LIGHT_BUFFER = [[]]
RGB_BACK_BUFFER = [[],[],[]]
RGB_FORE_BUFFER = [[],[],[]]
CHAR_BUFFER = [[]]
CONSOLE_HISTORY = []
CONSOLE_HISTORY_MAX_LINES = 29
PLACING_TILE = None
RENDERER = RENDERER_GLSL
DATA_DIR = 'data'

#Non-constants
SETTINGS = {'draw console': False,
			'draw z-levels above': True,
			'draw z-levels below': False}
KEYBOARD_STRING = ['']

#Consoles
MAP_WINDOW = None
ITEM_WINDOW = None
CONSOLE_WINDOW = None

#Menus
MENUS = []
MENU_PADDING = (1,1)

#Controls
KEY = Key()
MOUSE = Mouse()
INPUT = {'up':False,
		'down':False,
		'left':False,
		'right':False,
		' ':False,
		'-':False,
		'\x1b':False,
		'a':False,
		'b':False,
		'c':False,
		'd':False,
		'e':False,
		'f':False,
		'g':False,
		'h':False,
		'i':False,
		'j':False,
		'k':False,
		'l':False,
		'm':False,
		'n':False,
		'o':False,
		'p':False,
		'q':False,
		'r':False,
		's':False,
		't':False,
		'u':False,
		'v':False,
		'w':False,
		'x':False,
		'y':False,
		'z':False,
		'1':False,
		'2':False,
		'3':False,
		'4':False,
		'5':False}
		
#Colors
GREEN_ALT = Color(0,130,0)
GRASS_GREEN = Color(0, 150, 0)
GRASS_GREEN_DARK = Color(0, 140, 0)
SAND = Color(239,221,111)
SAND_LIGHT = Color(245, 222, 179)
BROWN_DARK = Color(123,74,18)
BROWN_DARK_ALT = Color(123, 63, 0)
BROWN_DARK_ALT_2 = Color(139,71,38)
CLAY = Color(228,145,53)
