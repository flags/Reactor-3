
import libtcodpy as libtcod
import os

try:  #import NumPy
	from numpy import *
except ImportError:
	raise ImportError('----- NumPy must be installed. -----')


#size of the screen, in tiles
SCREEN_W = 80
SCREEN_H = 50
HALF_W = SCREEN_W / 2
HALF_H = SCREEN_H / 2


#initialize libtcod
libtcod.console_set_custom_font(os.path.join('arial10x10.png'),
	libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(SCREEN_W, SCREEN_H, 'libtcod sample', False)
 
 
#the coordinates of all tiles in the screen, as numpy arrays.
#NOTE: combining these with regular numbers will effectively transform all pixels
#based on their coordinates. they look like this with a 4x3 pixels screen:
#xg = [[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4]]
#yg = [[1, 1, 1, 1], [2, 2, 2, 2], [3, 3, 3, 3]]
(x, y) = meshgrid(range(SCREEN_W), range(SCREEN_H))

lights = []
lights.append({'x': 40,'y': 20,'brightness': 4.0}) #MUST BE FLOATS
lights.append({'x': 20,'y': 20,'brightness': 3.0})

while not libtcod.console_is_window_closed():
	key = libtcod.console_check_for_keypress()
	if key.vk == libtcod.KEY_ESCAPE: break
	
	_R = zeros((SCREEN_H,SCREEN_W))
	_G = zeros((SCREEN_H,SCREEN_W))
	_B = zeros((SCREEN_H,SCREEN_W))
	#_R = add(_R,255)
	#_G = add(_G,255)
	#_B = add(_B,255)
	render = zeros((SCREEN_H,SCREEN_W))
	
	for light in lights:
		if lights.index(light) == 0:
			light['x'] -= 0.01
		
		sqr_distance = (x - light['x'])**2 + (y - light['y'])**2
		
		brightness = light['brightness'] / sqr_distance
		brightness = clip(brightness * 255, 0, 255)
		
		render = add(brightness,render).clip(0,255)
	
		_R = add(brightness,_R).clip(0,255)
	#_G = add(brightness,_G).clip(0,255)
	#_B = add(brightness,_B).clip(0,255)
	
	libtcod.console_fill_background(0, _R, render, render)	
	print libtcod.sys_get_fps()
	libtcod.console_flush()

