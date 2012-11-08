"""Terraform - World editor for Reactor 3"""
from libtcodpy import *
from globals import *
from inputs import *
from tiles import *
import graphics as gfx
import random
import time
import maps

try:
	MAP = maps.load_map('map1.dat')
except IOError:
	MAP = maps.create_map()
	maps.save_map(MAP)

PLACING_TILE = WALL_TILE

gfx.init_libtcod()

def handle_input():
	global PLACING_TILE,RUNNING,SETTINGS
	
	#print DRAW_CONSOLE
	
	"""Parses input."""
	if gfx.window_is_closed() or INPUT['\x1b']:
		RUNNING = False

	if INPUT['up']:
		CURSOR[1] -= 1

		if CAMERA_POS[1]<MAP_WINDOW_SIZE[1]/2 and CAMERA_POS[1]>0:
			CAMERA_POS[1] -= 1

	if INPUT['down']:
		CURSOR[1] += 1

		if CURSOR[1]-CAMERA_POS[1]>=MAP_WINDOW_SIZE[1]/2:
			CAMERA_POS[1] += 1

	if INPUT['right']:
		CURSOR[0] += 1

		if CURSOR[0]-CAMERA_POS[0]>=MAP_WINDOW_SIZE[0]/2:
			CAMERA_POS[0]+=1

	if INPUT['left']:
		CURSOR[0] -= 1

		if CAMERA_POS[0]<CAMERA_POS[0]+MAP_WINDOW_SIZE[0]/2 and\
				CAMERA_POS[0]>0:
			CAMERA_POS[0] -= 1

	if INPUT[' ']:
		MAP[CURSOR[0]][CURSOR[1]][CAMERA_POS[2]] = \
				create_tile(PLACING_TILE)
	
	if INPUT['[']:
		if SETTINGS['draw console']:
			SETTINGS['draw console'] = False
		else:
			SETTINGS['draw console'] = True
	
	if INPUT['q']:
		_current_index = TILES.index(PLACING_TILE)-1
		
		if _current_index<0:
			_current_index = 0
		
		PLACING_TILE = TILES[_current_index]
			
	if INPUT['w']:
		_current_index = TILES.index(PLACING_TILE)+1
		
		if _current_index>=len(TILES):
			_current_index = len(TILES)-1
		
		PLACING_TILE = TILES[_current_index]

	if INPUT['1']:
		CAMERA_POS[2] = 1

	if INPUT['2']:
		CAMERA_POS[2] = 2

	if INPUT['3']:
		CAMERA_POS[2] = 3

	if INPUT['4']:
		CAMERA_POS[2] = 4

	if INPUT['5']:
		CAMERA_POS[2] = 5

	if INPUT['c']:
		MAP[CURSOR[0]][CURSOR[1]][CAMERA_POS[2]] = \
				create_tile(random.choice(GRASS_TILES))

	if INPUT['d']:
		MAP[CURSOR[0]][CURSOR[1]][CAMERA_POS[2]] = None
	
	if INPUT['a']:
		MAP[CURSOR[0]][CURSOR[1]][CAMERA_POS[2]] = \
				create_tile(random.choice(SAND_TILES))
	
	if INPUT['s']:
		MAP[CURSOR[0]][CURSOR[1]][CAMERA_POS[2]] = \
				create_tile(random.choice(DIRT_TILES))

def draw_cursor():
	"""Handles the drawing of the cursor."""
	if time.time()%1>=0.5:
		gfx.blit_char(CURSOR[0]-CAMERA_POS[0],
		              CURSOR[1]-CAMERA_POS[1],'X',white,black)
	else:
		gfx.blit_tile(CURSOR[0]-CAMERA_POS[0],
		              CURSOR[1]-CAMERA_POS[1],PLACING_TILE)

while RUNNING:
	get_input()
	handle_input()

	gfx.start_of_frame()
	maps.render_map(MAP)
	draw_cursor()
	gfx.draw_all_tiles()
	gfx.draw_bottom_ui()
	gfx.draw_selected_tile_in_item_window(TILES.index(PLACING_TILE))
	gfx.draw_console()
	gfx.end_of_frame()

maps.save_map(MAP)
