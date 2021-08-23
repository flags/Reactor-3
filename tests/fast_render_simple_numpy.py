#The majority of this code is not mine.
#It was originally used to demonstrate
#fast rendering in libtcod using Numpy.
#I adapted it to do the lighting for
#Reactor 3.

#Original source:
#http://doryen.eptalys.net/forum/index.php?topic=467.0

import libtcodpy as libtcod
import os

try:
	from numpy import *
except ImportError:
	raise ImportError('----- NumPy must be installed. -----')

SCREEN_W = 80
SCREEN_H = 50
HALF_W = SCREEN_W // 2
HALF_H = SCREEN_H // 2

libtcod.console_set_custom_font(os.path.join('arial10x10.png'),
	libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(SCREEN_W, SCREEN_H, 'libtcod sample', False)

(x, y) = meshgrid(list(range(SCREEN_W)), list(range(SCREEN_H)))

lights = []
lights.append({'x': 40,'y': 20,'brightness': 4.0})
lights.append({'x': 20,'y': 20,'brightness': 3.0})

while not libtcod.console_is_window_closed():
	key = libtcod.console_check_for_keypress()
	if key.vk == libtcod.KEY_ESCAPE: break
	
	_R = zeros((SCREEN_H,SCREEN_W))
	_R = add(_R,255)
	_G = zeros((SCREEN_H,SCREEN_W))
	_G = add(_G,255)
	_B = zeros((SCREEN_H,SCREEN_W))
	_B = add(_B,255)
	_RB = zeros((SCREEN_H,SCREEN_W))
	_GB = zeros((SCREEN_H,SCREEN_W))
	_BB = zeros((SCREEN_H,SCREEN_W))
	_RB = add(_RB,255)
	_GB = add(_GB,255)
	_BB = add(_BB,255)
	render = zeros((SCREEN_H,SCREEN_W))
	
	for light in lights:
		if lights.index(light) == 0:
			light['x'] -= 0.01
		
		sqr_distance = (x - light['x'])**2 + (y - light['y'])**2
		
		brightness = light['brightness'] / sqr_distance
		brightness = clip(brightness * 255, 0, 255)
	
		_RB = subtract(_RB,brightness).clip(0,255)
		_GB = subtract(_GB,brightness).clip(0,255)
		_BB = subtract(_BB,brightness).clip(0,255)
	
	_R = subtract(_R,_RB).clip(0,255)
	_G = subtract(_G,_GB).clip(0,255)
	_B = subtract(_B,_BB).clip(0,255)
	
	libtcod.console_fill_background(0, _R, _G, _B)
	libtcod.console_fill_foreground(0, _R, _G, _B)
	print(libtcod.sys_get_fps())
	libtcod.console_flush()

