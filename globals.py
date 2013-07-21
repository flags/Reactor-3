import libtcodpy as tcod
import os

WINDOW_TITLE = 'Reactor 3 - Milestone 5'

#Constants
WINDOW_SIZE = (100,60)
MAP_SIZE = [500,500,5]
MAP_WINDOW_SIZE = (50, 50)
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
CAMPS = {}
WORLD_INFO = {'map': [],
	'time': 0,
	'time_of_day': 6000,
	'time_scale': 1,
	'length_of_day': 6000,
	'day': 0,
	'ticks': 0,
	'tps': 0,
	'tps_time': 0,
	'pause_ticks': 0,
	'in_combat': False,
	'world gravity': 0.3,
	'lifeid': 1,
	'itemid': 1,
	'groupid': 1,
	'effectid': 1,
	'zoneid': 1,
	'memoryid': 1,
	'chunk_map': CHUNK_MAP,
	'reference_map': {'roads': [], 'buildings': []},
	'slices': {},
	'chunk_size': 5}

#Return values
STATE_CHANGE = 2
STATE_UNCHANGED = 3
RETURN_SKIP = 4

CAMERA_POS = [0,0,2]
PREFAB_CAMERA_POS = [0,0,0]
SUN_POS = [0,0,25]
SUN_BRIGHTNESS = [100]
FPS = 100
FPS_TERRAFORM = 100
LOW_FPS = 15
UPS = 1
TPS = 30
FONT = 'terminal12x12_gs_ro.png'
FONT_LAYOUT = tcod.FONT_LAYOUT_ASCII_INCOL
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
MAP_CHAR_BUFFER = [[], []]
PREFAB_CHAR_BUFFER = [[], []]
X_CUTOUT_CHAR_BUFFER = [[], []]
Y_CUTOUT_CHAR_BUFFER = [[], []]
LIGHTS = []
CONSOLE_HISTORY = []
CONSOLE_HISTORY_MAX_LINES = 29
MESSAGE_LOG = []
MESSAGE_LOG_MAX_LINES = 8
PLACING_TILE = None
RENDERER = tcod.RENDERER_GLSL
DATA_DIR = 'data'
LIFE_DIR = os.path.join(DATA_DIR,'life')
ITEM_DIR = os.path.join(DATA_DIR,'items')
TEXT_DIR = os.path.join(DATA_DIR,'text')
DEFAULT_LIFE_ICON = '@'
DEFAULT_ITEM_ICON = 'i'
DEFAULT_ITEM_SIZE = '2x2'
DEFAULT_ITEM_PREFIX = 'a'

#Versions
MAP_RENDER_VERSION = 6

#Graphics tweaks
FADE_TO_WHITE = [0]
BLEEDING_STRING_MAX_LENGTH = 25
BORDER_COLOR = tcod.Color(128,128,128)
MAX_MESSAGES_IN_DIALOG = 9

#Strings
TEXT_MAP = {}

#Life constants
LIFE_MAX_SPEED = 4
LIFE_BLEED_RATE = .4 #Higher is faster
DAMAGE_MOVE_PENALTY_MOD = .07
PASS_OUT_PAIN_MOD = 10
ENCOUNTER_TIME_LIMIT = 150
DEFAULT_CONTEXT_TIME = 25

GIST_MAP = {'how_are_you': 0,
	'ignore': 0,
	'ignore_rude': -1,
	'inquire_about': 0,
	'tell_about': 0,
	'inquire_response_positive': 1,
	'inquire_response_neutral': 0,
	'inquire_response_negative': -1,
	'inquire_response_knows_positive': 1,
	'inquire_response_knows_neutral': 0,
	'inquire_response_knows_negative': -1,
	'inquire_response_neutral': 0,
	'inquire_response_negative': -1,
	'last_seen_target_at': 0,
	'status_response_positive': 1,
	'status_response': 0,
	'status_response_neutral': 0,
	'status_response_neutral_question': 0,
	'irritated_neutral': 0,
	'irritated_negative': -1,
	'heard_of_camp': 0,
	'inquire_about_camp_founder': 0,
	'inquire_about_camp_population': 0,
	'talk_about_camp': 0,
	'never_heard_of_camp': 0,
	'tell_about_camp_founder': 0,
	'ignore_question': 0,
	'ignore_question_negative': -1,
	'inform_of_camp': 0,
	'end': 0,
	'nothing': 0}

QUESTIONS_ANSWERS = {'wants_founder_info': {'camp': '*', 'founder': '*'},
	'wants item': {'type': '*'}}

POSSIBLE_LIKES = {'status_response_neutral*': [1.0, 0.8],
	'how_are_you': [1.0, 0.7]}

#Non-constants
SETTINGS = {'running': True,
	'paused': False,
	'draw lights': True,
	'diffuse light': False,
	'debug host': '',
	'debug port': 3335,
	'draw console': False,
	'draw z-levels above': True,
	'draw z-levels below': False,
	'progress bar max value': 25,
	'action queue size': 4,
	'los': 40,
	'controlling': None,
	'following': None,
	'state history size': 5,
	'fire burn rate': 0.04}
KEYBOARD_STRING = ['']
SELECTED_TILES = [[]]
TILES = {}
LIFE_TYPES = {}
LIFE = {}
LIFE_MAP = []
ITEM_TYPES = {}
ITEMS = {}
BULLETS = []
EFFECTS = {}
EFFECT_MAP = []
SPLATTERS = []
JOBS = {}
SELECTED_TARGET = []
GROUPS = {}

#Consoles
MAP_WINDOW = None
ITEM_WINDOW = None
CONSOLE_WINDOW = None

#Menus
MENUS = []
ACTIVE_MENU = {'menu': -1}
MENU_PADDING = (1,1)

#Controls
KEY = tcod.Key()
MOUSE = tcod.Mouse()
INPUT = {'up':False,
		'down':False,
		'left':False,
		'right':False,
		' ':False,
		'-':False,
		',': False,
		'?': False,
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
		'P':False,
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
GREEN_ALT = tcod.Color(0,130,0)
GRASS_GREEN = tcod.Color(0, 150, 0)
GRASS_GREEN_DARK = tcod.Color(0, 140, 0)
SAND = tcod.Color(239,221,111)
SAND_LIGHT = tcod.Color(245, 222, 179)
BROWN_DARK = tcod.Color(123,74,18)
BROWN_DARK_ALT = tcod.Color(123, 63, 0)
BROWN_DARK_ALT_2 = tcod.Color(139,71,38)
CLAY = tcod.Color(228,145,53)

#Message bank
MESSAGE_BANK = {'cancelpickupequipitem': 'You stop picking up the item.',
	'cancelpickupitem': 'You stop picking up the item.',
	'cancelequipitem': 'You stop putting on the item.'}
