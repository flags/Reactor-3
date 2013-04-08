from globals import *
from libtcodpy import *

import graphics

MAIN_MENU_TEXT = ['Reactor 3',
	'- - -',
	'STRATEGIC ROGUELIKE ACTION',
	'- - -',
	'',
	's - Start',
	'g - Generate World',
	'q - Quit']

WORLD_INFO_TEXT = ['World Info',
	'placeholder']

MENU = [MAIN_MENU_TEXT]

def draw_main_menu():
	console_rect(0,0,0,WINDOW_SIZE[0],WINDOW_SIZE[1],True,flag=BKGND_DEFAULT)
	
	_i = 0
	for line in MENU[0]:
		console_print(0, (WINDOW_SIZE[0]/2)-(len(line)/2), _i+1, line)
		_i += 1
	
	console_flush()
