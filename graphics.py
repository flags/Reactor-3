from libtcodpy import *
from globals import *

def init_libtcod():
	console_init_root(WINDOW_SIZE[0],WINDOW_SIZE[1],WINDOW_TITLE,renderer=RENDERER)
	console_set_custom_font(FONT,FONT_LAYOUT)
	sys_set_fps(FPS)