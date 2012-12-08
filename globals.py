from libtcodpy import *
import os

WINDOW_TITLE = 'Reactor 3 - Milestone 3-2'

#Constants
WINDOW_SIZE = (100,50)
MAP_SIZE = [500,500,5]
MAP_WINDOW_SIZE = (40,40)
ITEM_WINDOW_SIZE = (40,1)
CONSOLE_WINDOW_SIZE = (40,30)
MESSAGE_WINDOW_SIZE = (60,10)
RUNNING = True
CURSOR = [0,0]
CAMERA_POS = [0,0,2]
SUN_POS = [0,0,25]
SUN_BRIGHTNESS = [0]
FPS = 30
FPS_TERRAFORM = 100
UPS = 1
FONT = 'terminal12x12_gs_ro.png'
FONT_LAYOUT = FONT_LAYOUT_ASCII_INCOL
DARK_BUFFER = [[]]
LIGHT_BUFFER = [[]]
RGB_BACK_BUFFER = [[],[],[]]
RGB_FORE_BUFFER = [[],[],[]]
RGB_LIGHT_BUFFER = [[],[],[]]
LIGHTS = []
CHAR_BUFFER = [[]]
CONSOLE_HISTORY = []
CONSOLE_HISTORY_MAX_LINES = 29
MESSAGE_LOG = []
MESSAGE_LOG_MAX_LINES = 8
PLACING_TILE = None
RENDERER = RENDERER_GLSL
DATA_DIR = 'data'
LIFE_DIR = os.path.join(DATA_DIR,'life')
ITEM_DIR = os.path.join(DATA_DIR,'items')
DEFAULT_LIFE_ICON = '@'
DEFAULT_ITEM_ICON = 'i'
DEFAULT_ITEM_SIZE = '2x2'

#Life constants
LIFE_MAX_SPEED = 12

#Non-constants
SETTINGS = {'draw lights': True,
			'draw console': False,
			'draw z-levels above': True,
			'draw z-levels below': False}
KEYBOARD_STRING = ['']
SELECTED_TILES = []
LIFE_TYPES = {}
LIFE = []
ITEM_TYPES = {}
ITEMS = {}

#Consoles
MAP_WINDOW = None
ITEM_WINDOW = None
CONSOLE_WINDOW = None

#Menus
MENUS = []
ACTIVE_MENU = {'menu': -1,'index': 0}
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
		',': False,
		'\x1b':False,
		'\r':False,
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
