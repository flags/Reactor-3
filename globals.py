from libtcodpy import *
import os

WINDOW_TITLE = 'Reactor 3 - Milestone 5'

#Constants
WINDOW_SIZE = (100,50)
MAP_SIZE = [500,500,5]
MAP_WINDOW_SIZE = (40,40)
ITEM_WINDOW_SIZE = (40,1)
CONSOLE_WINDOW_SIZE = (40,30)
MESSAGE_WINDOW_SIZE = (100,10)
PREFAB_WINDOW_SIZE = (40,40)
X_CUTOUT_WINDOW_SIZE = (15,15)
Y_CUTOUT_WINDOW_SIZE = (15,15)
PREFAB_WINDOW_OFFSET = (MAP_WINDOW_SIZE[0]+26,1)
MAP_CURSOR = [0,0]
PREFAB_CURSOR = [0,0]
TICKER = ['\\', '|', '/', '-']
ENCOUNTER_ANIMATION_TIME = 30

#Map stuff
CHUNK_MAP = {}
WORLD_INFO = {'ticks': 0,
	'pause_ticks': 0,
	'in_combat': False}
REFERENCE_MAP = {'roads': [],
	'buildings': []}
CAMPS = {}

#Return values
STATE_CHANGE = 2
STATE_UNCHANGED = 3
RETURN_SKIP = 4

CAMERA_POS = [0,0,2]
PREFAB_CAMERA_POS = [0,0,0]
SUN_POS = [0,0,25]
SUN_BRIGHTNESS = [0]
FPS = 30
FPS_TERRAFORM = 100
UPS = 1
FONT = 'terminal12x12_gs_ro.png'
FONT_LAYOUT = FONT_LAYOUT_ASCII_INCOL
HEIGHT_MAP = [[]]
DARK_BUFFER = [[]]
LIGHT_BUFFER = [[]]
LOS_DARK_BUFFER = [[]]
LOS_LIGHT_BUFFER = [[]]
MAP_RGB_BACK_BUFFER = [[],[],[]]
MAP_RGB_FORE_BUFFER = [[],[],[]]
PREFAB_RGB_BACK_BUFFER = [[],[],[]]
PREFAB_RGB_FORE_BUFFER = [[],[],[]]
X_CUTOUT_RGB_FORE_BUFFER = [[],[],[]]
Y_CUTOUT_RGB_FORE_BUFFER = [[],[],[]]
X_CUTOUT_RGB_BACK_BUFFER = [[],[],[]]
Y_CUTOUT_RGB_BACK_BUFFER = [[],[],[]]
RGB_LIGHT_BUFFER = [[],[],[]]
LOS_BUFFER = [[]]
MAP_CHAR_BUFFER = [[]]
PREFAB_CHAR_BUFFER = [[]]
X_CUTOUT_CHAR_BUFFER = [[]]
Y_CUTOUT_CHAR_BUFFER = [[]]
LIGHTS = []
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
DEFAULT_ITEM_PREFIX = 'a'

#Versions
MAP_RENDER_VERSION = 4

#Graphics tweaks
FADE_TO_WHITE = [0]
BLEEDING_STRING_MAX_LENGTH = 25
BORDER_COLOR = Color(128,128,128)

#Life constants
LIFE_MAX_SPEED = 5
LIFE_BLEED_RATE = .05 #Lower is faster
DAMAGE_MOVE_PENALTY_MOD = .07
PASS_OUT_PAIN_MOD = 10
ENCOUNTER_TIME_LIMIT = 150
DEFAULT_CONTEXT_TIME = 25

#Non-constants
SETTINGS = {'running': True,
			'draw lights': True,
			'draw console': False,
			'draw z-levels above': True,
			'draw z-levels below': False,
			'progress bar max value': 25,
			'action queue size': 4,
			'world gravity': 0.3,
			'los': 40,
			'lifeid': 0,
			'heatmap': None,
			'controlling': None,
			'following': None,
			'state history size': 5,
			'chunk size': 5}
KEYBOARD_STRING = ['']
SELECTED_TILES = [[]]
TILES = {}
LIFE_TYPES = {}
LIFE = {}
ITEM_TYPES = {}
ITEMS = {}
BULLETS = []
EFFECTS = []
SPLATTERS = []
JOBS = {}

#Consoles
MAP_WINDOW = None
ITEM_WINDOW = None
CONSOLE_WINDOW = None

#Menus
MENUS = []
ACTIVE_MENU = {'menu': -1}
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
		'\t':False,
		'a':False,
		'b':False,
		'c':False,
		'C':False,
		'd':False,
		'e':False,
		'E':False,
		'f':False,
		'F':False,
		'g':False,
		'h':False,
		'H':False,
		'i':False,
		'j':False,
		'k':False,
		'l':False,
		'm':False,
		'n':False,
		'o':False,
		'O':False,
		'p':False,
		'q':False,
		'r':False,
		's':False,
		'S':False,
		't':False,
		'u':False,
		'v':False,
		'V':False,
		'w':False,
		'x':False,
		'y':False,
		'z':False,
		'Z':False,
		'1':False,
		'2':False,
		'3':False,
		'4':False,
		'5':False,
		'6':False,
		'7':False,
		'8':False,
		'9':False,
		'0':False}
		
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

#Message bank
MESSAGE_BANK = {'cancelpickupequipitem': 'You stop picking up the item.',
	'cancelpickupitem': 'You stop picking up the item.',
	'cancelequipitem': 'You stop putting on the item.'}
