from globals import *
from libtcodpy import *

import graphics

HEADER = ['Reactor 3',
	'- - -',
	'Return to Pripyat',
	'- - -',
	'']
HEADER.reverse()

MAIN_MENU_TEXT = ['s - Start  ',
	'o - Options',
	'q - Quit   ']

WORLD_INFO_TEXT = ['placeholder']

[MAIN_MENU_TEXT.insert(0, line) for line in HEADER]
[WORLD_INFO_TEXT.insert(0, line) for line in HEADER]

MENU = [MAIN_MENU_TEXT]

def draw_main_menu():
	console_rect(0,0,0,WINDOW_SIZE[0],WINDOW_SIZE[1],True,flag=BKGND_DEFAULT)
	
	_i = 0
	for line in MENU[0]:
		console_print(0, (WINDOW_SIZE[0]/2)-(len(line)/2), _i+1, line)
		_i += 1
	
	console_flush()
