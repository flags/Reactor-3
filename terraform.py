"""Terraform - World editor for Reactor 3"""
from libtcodpy import *
from inputs import *
from tiles import *
import graphics as gfx
import globals as var
import random
import time
import maps

try:
	var.MAP = maps.load_map('map1.dat')
except IOError:
	var.MAP = maps.create_map()
	maps.save_map(var.MAP)

var.CURSOR = [0, 0]
var.PLACING_TILE = WALL_TILE

gfx.init_libtcod()

def handle_input():
	"""Parses input."""
	if gfx.window_is_closed() or var.INPUT['escape']:
		var.RUNNING = False

	if var.INPUT['up']:
		var.CURSOR[1] -= 1

		if var.CAMERA_POS[1]<var.MAP_WINDOW_SIZE[1]/2 and var.CAMERA_POS[1]>0:
			var.CAMERA_POS[1] -= 1

	if var.INPUT['down']:
		var.CURSOR[1] += 1

		if var.CURSOR[1]-var.CAMERA_POS[1]>=var.MAP_WINDOW_SIZE[1]/2:
			var.CAMERA_POS[1] += 1

	if var.INPUT['right']:
		var.CURSOR[0] += 1

		if var.CURSOR[0]-var.CAMERA_POS[0]>=var.MAP_WINDOW_SIZE[0]/2:
			var.CAMERA_POS[0]+=1

	if var.INPUT['left']:
		var.CURSOR[0] -= 1

		if var.CAMERA_POS[0]<var.CAMERA_POS[0]+var.MAP_WINDOW_SIZE[0]/2 and\
				var.CAMERA_POS[0]>0:
			var.CAMERA_POS[0] -= 1

	if var.INPUT['space']:
		var.MAP[var.CURSOR[0]][var.CURSOR[1]][var.CAMERA_POS[2]] = \
				create_tile(var.PLACING_TILE)

	if INPUT['1']:
		var.CAMERA_POS[2] = 1

	if INPUT['2']:
		var.CAMERA_POS[2] = 2

	if INPUT['3']:
		var.CAMERA_POS[2] = 3

	if INPUT['4']:
		var.CAMERA_POS[2] = 4

	if INPUT['5']:
		var.CAMERA_POS[2] = 5

	if INPUT['c']:
		var.MAP[var.CURSOR[0]][var.CURSOR[1]][var.CAMERA_POS[2]] = \
				create_tile(random.choice(GRASS_TILES))

	if INPUT['d']:
		var.MAP[var.CURSOR[0]][var.CURSOR[1]][var.CAMERA_POS[2]] = None
	
	if INPUT['a']:
		var.MAP[var.CURSOR[0]][var.CURSOR[1]][var.CAMERA_POS[2]] = \
				create_tile(random.choice(SAND_TILES))
	
	if INPUT['s']:
		var.MAP[var.CURSOR[0]][var.CURSOR[1]][var.CAMERA_POS[2]] = \
				create_tile(random.choice(DIRT_TILES))

def draw_cursor():
	"""Handles the drawing of the cursor."""
	if time.time()%1>=0.5:
		gfx.blit_char(var.CURSOR[0]-var.CAMERA_POS[0],
		              var.CURSOR[1]-var.CAMERA_POS[1],'X',white,black)
	else:
		gfx.blit_tile(var.CURSOR[0]-var.CAMERA_POS[0],
		              var.CURSOR[1]-var.CAMERA_POS[1],var.PLACING_TILE)

def draw_bottom_ui():
	"""Controls the drawing of the UI under the map."""
	gfx.blit_string(0, var.MAP_WINDOW_SIZE[1],'X: %s Y: %s Z: %s' %
		(var.CURSOR[0],var.CURSOR[1],var.CAMERA_POS[2]))

	_fps_string = '%s fps' % str(sys_get_fps())
	gfx.blit_string(var.WINDOW_SIZE[0]-len(_fps_string), var.MAP_WINDOW_SIZE[1],
					_fps_string)

while var.RUNNING:
	get_input()
	handle_input()

	gfx.start_of_frame()
	maps.render_map(var.MAP)
	draw_cursor()
	draw_bottom_ui()
	gfx.end_of_frame()

maps.save_map(var.MAP)
