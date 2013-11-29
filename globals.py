import libtcodpy as tcod
import os

VERSION = '0.6.5'
WINDOW_TITLE = 'Reactor 3 - %s' % VERSION
WINDOW_SIZE = (100, 60)
MAP_SIZE = [250, 250, 5]
MAP_WINDOW_SIZE = (WINDOW_SIZE[0]/2, WINDOW_SIZE[1]-10)
ITEM_WINDOW_SIZE = (40,1)
CONSOLE_WINDOW_SIZE = (40,30)
MESSAGE_WINDOW_SIZE = (100,10)
PREFAB_WINDOW_SIZE = [40,40]
X_CUTOUT_WINDOW_SIZE = (15,15)
Y_CUTOUT_WINDOW_SIZE = (15,15)
PREFAB_WINDOW_OFFSET = (MAP_WINDOW_SIZE[0]+26,1)
CURSOR_POS = [WINDOW_SIZE[0]/2, WINDOW_SIZE[1]/2, 2]
MAP_CURSOR = [0,0]
PREFAB_CURSOR = [0,0]
PREFABS = {}
TICKER = ['\\', '|', '/', '-']
ENCOUNTER_ANIMATION_TIME = 30
UPDATE_CAMP_RATE = 5

#Map stuff
WORLD_INFO = {'map': [],
	'id': None,
	'seed': 0,
	'time': 0,
	'real_time_of_day': 6000,
	'time_of_day': 'limbo',
	'time_scale': 1,
	'length_of_day': 6000,
	'day': 0,
	'ticks': 0,
	'sub_ticks': 0,
	'max_sub_ticks': 5,
	'tps': 0,
	'last_update_time': 0,
	'life_density': 'Sparse',
	'life_spawn_interval': [0, (0, 0)],
	'wildlife_spawn_interval': [0, (0, 0)],
	'world gravity': 0.3,
	'lifeid': 1,
	'itemid': 1,
	'groupid': 1,
	'campid': 1,
	'effectid': 1,
	'zoneid': 1,
	'memoryid': 1,
	'goalid': 1,
	'jobid': 1,
	'dialogid': 1,
	'dialogs': {},
	'chunk_map': {},
	'camps': {},
	'groups': {},
	'jobs': {},
	'references': {},
	'reference_map': {'roads': [], 'buildings': []},
	'slices': {},
	'chunk_size': 5,
	'lights': [],
	'timers': [],
	'weather': {}}

#Return values
STATE_CHANGE = 2
STATE_UNCHANGED = 3
RETURN_SKIP = 4

STATE_ICONS = {}

#States
TIER_COMBAT = 1
TIER_SURVIVAL = 2
TIER_EXPLORE = 3
TIER_IDLE = 4
TIER_WORK = 2.5
TIER_PASSIVE = 333
TIER_CONSTANT = 332
TIER_SUBMIT = 0.1

#Group stages
STAGE_FORMING = 1
STAGE_SETTLING = 2
STAGE_SETTLED = 3
STAGE_RAIDING = 4

CAMERA_POS = [0,0,2]
PREFAB_CAMERA_POS = [0,0,0]
SUN_POS = [0,0,25]
SUN_BRIGHTNESS = [100]
FPS = 1000
FPS_TERRAFORM = 100
LOW_FPS = 15
FONT = 'terminal8x8_gs_as_incol.png'
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
MAP_CHAR_BUFFER = [[], []]
PREFAB_CHAR_BUFFER = [[], []]
X_CUTOUT_CHAR_BUFFER = [[], []]
Y_CUTOUT_CHAR_BUFFER = [[], []]
REFRESH_POSITIONS = []
CONSOLE_HISTORY = []
CONSOLE_HISTORY_MAX_LINES = 29
MESSAGE_LOG = []
MESSAGE_LOG_MAX_LINES = 8
PLACING_TILE = None
RENDERER = tcod.RENDERER_SDL
DATA_DIR = 'data'
LIFE_DIR = os.path.join(DATA_DIR,'life')
ITEM_DIR = os.path.join(DATA_DIR,'items')
TEXT_DIR = os.path.join(DATA_DIR,'text')
PREFAB_DIR = os.path.join(DATA_DIR,'prefabs')
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
LIFE_THINK_RATE = 6
DAMAGE_MOVE_PENALTY_MOD = .07
PASS_OUT_PAIN_MOD = 10

#Non-constants
SETTINGS = {'running': True,
	'paused': False,
	'camera_track': [0, 0, 0],
	'last_camera_pos': [-1, -1, -1],
	'cursor speed': 3,
	'draw lights': True,
	'light mesh grid': None,
	'diffuse light': False,
	'debug host': '',
	'debug port': 3335,
	'draw console': False,
	'draw z-levels above': True,
	'draw z-levels below': False,
	'draw visible chunks': False,
	'draw life info': True,
	'draw message box': True,
	'draw effects': True,
	'print dijkstra maps': False,
	'progress bar max value': 25,
	'action queue size': 4,
	'los': 40,
	'controlling': None,
	'following': None,
	'state history size': 5,
	'fire burn rate': 0.04,
	'smp': None,
	'map_slices': [],
	'recording': False,
	'recording fps': 0,
	'recording fps temp': 0,
	'viewid': 1,
	'active_view': 0,
    'refresh_los': False}

FUNCTION_MAP = {}
KEYBOARD_STRING = ['']
SELECTED_TILES = [[]]
TILES = {}
TILE_STRUCT = {'flags': {}}
TILE_STRUCT_DEP = ['tiles']
LIFE_TYPES = {}
LIFE = {}
LIFE_MAP = []
ITEMS = {}
ITEMS_HISTORY = {}
ITEM_TYPES = {}
ITEM_MAP = []
CHUNK_MAP_CACHE = {}
BULLETS = []
EFFECTS = {}
EFFECT_MAP = []
SPLATTERS = []
SELECTED_TARGET = []
EVENTS = []
DIJKSTRA_CACHE = {}
ZONE_CACHE = {}
VIEWS = {}
VIEW_SCENE = {}
VIEW_SCENE_CACHE = set()
DIALOG_TOPICS = {}

#Consoles
ITEM_WINDOW = None
CONSOLE_WINDOW = None
MESSAGE_WINDOW = None

#Menus
MENUS = []
ACTIVE_MENU = {'menu': -1}
MENU_PADDING = (1,1)

#Controls
KEY = tcod.Key()
MOUSE = tcod.Mouse()
MOUSE_POS = [0, 0]
MOUSE_CALLBACKS = {'m1_click': None, 'm2_click': None, 'move': None}
INPUT = {'up':False,
		'down':False,
		'left':False,
		'right':False,
		' ':False,
		'.':False,
		'-':False,
		',': False,
		'?': False,
		'\x1b':False,
		'\r':False,
		'\t':False,
		'a':False,
		'A': False,
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
		'0':False,
		'm1': False,
		'm2': False}
		
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
