from libtcodpy import *
from inputs import *
from tiles import *
import graphics as gfx
import globals as var
import time
import maps

var.MAP = maps.load_map('map1.dat')
#var.MAP = maps.create_map()
#maps.save_map(var.MAP)
var.CURSOR = [0,0]

gfx.init_libtcod()

def handle_input():
	if gfx.window_is_closed() or var.INPUT['escape']:
		var.RUNNING = False

	if var.INPUT['up']:
		var.CURSOR[1]-=1

	if var.INPUT['down']:
		var.CURSOR[1]+=1

	if var.INPUT['right']:
		var.CURSOR[0]+=1

	if var.INPUT['left']:
		var.CURSOR[0]-=1

	if var.INPUT['space']:
		var.MAP[var.CURSOR[0]][var.CURSOR[1]][2] = create_tile(WALL_TILE)

def draw_cursor():
	if time.time()%1>=0.5:
		_fore = white
	else:
		_fore = None

	gfx.blit_char(var.CURSOR[0],var.CURSOR[1],'X',_fore,back_color=black)

while var.RUNNING:
	get_input()
	handle_input()

	gfx.start_of_frame()
	maps.render_map(var.MAP)
	draw_cursor()
	gfx.end_of_frame()

maps.save_map(var.MAP)