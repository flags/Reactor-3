from libtcodpy import *
from globals import *
from tiles import *
import numpy
import time
import life

def init_libtcod(terraform=False):
	global MAP_WINDOW, ITEM_WINDOW, CONSOLE_WINDOW, MESSAGE_WINDOW, PREFAB_WINDOW, X_CUTOUT_WINDOW, Y_CUTOUT_WINDOW
	console_init_root(WINDOW_SIZE[0],WINDOW_SIZE[1],WINDOW_TITLE,renderer=RENDERER)
	MAP_WINDOW = console_new(MAP_WINDOW_SIZE[0],MAP_WINDOW_SIZE[1])
	ITEM_WINDOW = console_new(ITEM_WINDOW_SIZE[0],ITEM_WINDOW_SIZE[1])
	CONSOLE_WINDOW = console_new(CONSOLE_WINDOW_SIZE[0],CONSOLE_WINDOW_SIZE[1])
	MESSAGE_WINDOW = console_new(MESSAGE_WINDOW_SIZE[0],MESSAGE_WINDOW_SIZE[1])
	
	if terraform:
		PREFAB_WINDOW = console_new(PREFAB_WINDOW_SIZE[0],PREFAB_WINDOW_SIZE[1])
		X_CUTOUT_WINDOW = console_new(X_CUTOUT_WINDOW_SIZE[0],X_CUTOUT_WINDOW_SIZE[1])
		Y_CUTOUT_WINDOW = console_new(Y_CUTOUT_WINDOW_SIZE[0],Y_CUTOUT_WINDOW_SIZE[1])
		
		PREFAB_CHAR_BUFFER[0] = numpy.zeros((PREFAB_WINDOW_SIZE[1], PREFAB_WINDOW_SIZE[0]))
		X_CUTOUT_CHAR_BUFFER[0] = numpy.zeros((X_CUTOUT_WINDOW_SIZE[1], X_CUTOUT_WINDOW_SIZE[0]))
		Y_CUTOUT_CHAR_BUFFER[0] = numpy.zeros((Y_CUTOUT_WINDOW_SIZE[1], Y_CUTOUT_WINDOW_SIZE[0]))
	
	console_set_custom_font(FONT,FONT_LAYOUT)
	console_set_keyboard_repeat(200, 0)
	sys_set_fps(FPS)

	for i in range(3):
		MAP_RGB_BACK_BUFFER[i] = numpy.zeros((MAP_WINDOW_SIZE[1], MAP_WINDOW_SIZE[0]))
		MAP_RGB_FORE_BUFFER[i] = numpy.zeros((MAP_WINDOW_SIZE[1], MAP_WINDOW_SIZE[0]))
		RGB_LIGHT_BUFFER[i] = numpy.zeros((MAP_WINDOW_SIZE[1], MAP_WINDOW_SIZE[0]))
		
		if terraform:
			PREFAB_RGB_BACK_BUFFER[i] = numpy.zeros((PREFAB_WINDOW_SIZE[1], PREFAB_WINDOW_SIZE[0]))
			PREFAB_RGB_FORE_BUFFER[i] = numpy.zeros((PREFAB_WINDOW_SIZE[1], PREFAB_WINDOW_SIZE[0]))
			X_CUTOUT_RGB_BACK_BUFFER[i] = numpy.zeros((X_CUTOUT_WINDOW_SIZE[1], X_CUTOUT_WINDOW_SIZE[0]))
			X_CUTOUT_RGB_FORE_BUFFER[i] = numpy.zeros((X_CUTOUT_WINDOW_SIZE[1], X_CUTOUT_WINDOW_SIZE[0]))
			Y_CUTOUT_RGB_BACK_BUFFER[i] = numpy.zeros((Y_CUTOUT_WINDOW_SIZE[1], Y_CUTOUT_WINDOW_SIZE[0]))
			Y_CUTOUT_RGB_FORE_BUFFER[i] = numpy.zeros((Y_CUTOUT_WINDOW_SIZE[1], Y_CUTOUT_WINDOW_SIZE[0]))
	
	LOS_BUFFER[0] = numpy.zeros((MAP_WINDOW_SIZE[1], MAP_WINDOW_SIZE[0]))
	MAP_CHAR_BUFFER[0] = numpy.zeros((MAP_WINDOW_SIZE[1], MAP_WINDOW_SIZE[0]))
	DARK_BUFFER[0] = numpy.zeros((MAP_WINDOW_SIZE[1], MAP_WINDOW_SIZE[0]))
	LIGHT_BUFFER[0] = numpy.zeros((MAP_WINDOW_SIZE[1], MAP_WINDOW_SIZE[0]))

def start_of_frame():
	console_fill_background(MAP_WINDOW,
	        numpy.subtract(numpy.add(numpy.subtract(MAP_RGB_BACK_BUFFER[0],RGB_LIGHT_BUFFER[0]),LIGHT_BUFFER[0]),DARK_BUFFER[0]).clip(0,255),
	        numpy.subtract(numpy.add(numpy.subtract(MAP_RGB_BACK_BUFFER[1],RGB_LIGHT_BUFFER[1]),LIGHT_BUFFER[0]),DARK_BUFFER[0]).clip(0,255),
	        numpy.subtract(numpy.add(numpy.subtract(MAP_RGB_BACK_BUFFER[2],RGB_LIGHT_BUFFER[2]),LIGHT_BUFFER[0]),DARK_BUFFER[0]).clip(0,255))
	console_fill_foreground(MAP_WINDOW,
	        numpy.subtract(numpy.add(numpy.subtract(MAP_RGB_FORE_BUFFER[0],RGB_LIGHT_BUFFER[0]),LIGHT_BUFFER[0]),DARK_BUFFER[0]).clip(0,255),
	        numpy.subtract(numpy.add(numpy.subtract(MAP_RGB_FORE_BUFFER[1],RGB_LIGHT_BUFFER[1]),LIGHT_BUFFER[0]),DARK_BUFFER[0]).clip(0,255),
	        numpy.subtract(numpy.add(numpy.subtract(MAP_RGB_FORE_BUFFER[2],RGB_LIGHT_BUFFER[2]),LIGHT_BUFFER[0]),DARK_BUFFER[0]).clip(0,255))
	console_fill_char(MAP_WINDOW,MAP_CHAR_BUFFER[0])

def start_of_frame_terraform():
	console_fill_background(PREFAB_WINDOW,PREFAB_RGB_BACK_BUFFER[0],PREFAB_RGB_BACK_BUFFER[1],PREFAB_RGB_BACK_BUFFER[2])
	console_fill_foreground(PREFAB_WINDOW,PREFAB_RGB_FORE_BUFFER[0],PREFAB_RGB_FORE_BUFFER[1],PREFAB_RGB_FORE_BUFFER[2])
	console_fill_char(PREFAB_WINDOW,PREFAB_CHAR_BUFFER[0])
	
	console_fill_background(X_CUTOUT_WINDOW,X_CUTOUT_RGB_BACK_BUFFER[0],X_CUTOUT_RGB_BACK_BUFFER[1],X_CUTOUT_RGB_BACK_BUFFER[2])
	console_fill_foreground(X_CUTOUT_WINDOW,X_CUTOUT_RGB_FORE_BUFFER[0],X_CUTOUT_RGB_FORE_BUFFER[1],X_CUTOUT_RGB_FORE_BUFFER[2])
	console_fill_char(X_CUTOUT_WINDOW,X_CUTOUT_CHAR_BUFFER[0])
	
	console_fill_background(Y_CUTOUT_WINDOW,Y_CUTOUT_RGB_BACK_BUFFER[0],Y_CUTOUT_RGB_BACK_BUFFER[1],Y_CUTOUT_RGB_BACK_BUFFER[2])
	console_fill_foreground(Y_CUTOUT_WINDOW,Y_CUTOUT_RGB_FORE_BUFFER[0],Y_CUTOUT_RGB_FORE_BUFFER[1],Y_CUTOUT_RGB_FORE_BUFFER[2])
	console_fill_char(Y_CUTOUT_WINDOW,Y_CUTOUT_CHAR_BUFFER[0])

def blit_tile(x,y,tile,char_buffer=MAP_CHAR_BUFFER,rgb_fore_buffer=MAP_RGB_FORE_BUFFER,rgb_back_buffer=MAP_RGB_BACK_BUFFER):
	_tile = get_tile(tile)

	blit_char(x,y,_tile['icon'],
		_tile['color'][0],
		_tile['color'][1],
		char_buffer=char_buffer,
		rgb_fore_buffer=rgb_fore_buffer,
		rgb_back_buffer=rgb_back_buffer)

def blit_char(x,y,char,fore_color=None,back_color=None,char_buffer=None,rgb_fore_buffer=None,rgb_back_buffer=None):
	if fore_color:
		rgb_fore_buffer[0][y,x] = fore_color.r
		rgb_fore_buffer[1][y,x] = fore_color.g
		rgb_fore_buffer[2][y,x] = fore_color.b

	if back_color:
		rgb_back_buffer[0][y,x] = back_color.r
		rgb_back_buffer[1][y,x] = back_color.g
		rgb_back_buffer[2][y,x] = back_color.b

	char_buffer[0][y,x] = ord(char)

def blit_string(x,y,text):
	console_print(0,x,y,text)

def darken_tile(x,y,amt):
	DARK_BUFFER[0][y,x] = amt

def lighten_tile(x,y,amt):
	LIGHT_BUFFER[0][y,x] = amt

def draw_cursor(cursor,camera,tile,char_buffer=MAP_CHAR_BUFFER,rgb_fore_buffer=MAP_RGB_FORE_BUFFER,rgb_back_buffer=MAP_RGB_BACK_BUFFER):
	if time.time()%1>=0.5:
		blit_char(cursor[0]-camera[0],
			cursor[1]-camera[1],
			'X',
			white,
			black,
			char_buffer=char_buffer,
			rgb_fore_buffer=rgb_fore_buffer,
			rgb_back_buffer=rgb_back_buffer)
	else:
		blit_tile(cursor[0]-camera[0],
			cursor[1]-camera[1],
			tile,
			char_buffer=char_buffer,
			rgb_fore_buffer=rgb_fore_buffer,
			rgb_back_buffer=rgb_back_buffer)

def draw_bottom_ui_terraform():
	"""Controls the drawing of the UI under the map."""
	blit_string(0,MAP_WINDOW_SIZE[1]+1,'X: %s Y: %s Z: %s' %
		(MAP_CURSOR[0],MAP_CURSOR[1],CAMERA_POS[2]))

	_fps_string = '%s fps' % str(sys_get_fps())
	blit_string(WINDOW_SIZE[0]-len(_fps_string), MAP_WINDOW_SIZE[1]+1,_fps_string)

def draw_bottom_ui():	
	console_set_default_foreground(MESSAGE_WINDOW,Color(128,128,128))
	console_print_frame(MESSAGE_WINDOW,0,0,MESSAGE_WINDOW_SIZE[0],MESSAGE_WINDOW_SIZE[1])
	console_set_default_foreground(MESSAGE_WINDOW,white)
	console_print(MESSAGE_WINDOW,1,0,'Messages')
	
	_y_mod = 1
	
	for msg in MESSAGE_LOG[max(0, min(len(MESSAGE_LOG)-MESSAGE_LOG_MAX_LINES, MESSAGE_LOG_MAX_LINES)):]:
		console_print(MESSAGE_WINDOW,1,_y_mod,msg)
		_y_mod += 1

def draw_selected_tile_in_item_window(pos):
	if time.time()%1>=0.5:
		console_print(ITEM_WINDOW,pos,0,chr(15))

def draw_all_tiles():
	for tile in TILES:
		console_set_char_foreground(ITEM_WINDOW, TILES.keys().index(tile), 0, TILES[tile]['color'][0])
		console_set_char_background(ITEM_WINDOW, TILES.keys().index(tile), 0, TILES[tile]['color'][1])
		console_set_char(ITEM_WINDOW, TILES.keys().index(tile), 0, TILES[tile]['icon'])

def draw_console():
	if not SETTINGS['draw console']:
		return False
	
	console_rect(CONSOLE_WINDOW,0,0,CONSOLE_WINDOW_SIZE[0],CONSOLE_WINDOW_SIZE[1],True,flag=BKGND_DEFAULT)
	
	_i = 0
	for line in CONSOLE_HISTORY[len(CONSOLE_HISTORY)-CONSOLE_HISTORY_MAX_LINES:]:
		_xoffset = 0
		
		if CONSOLE_HISTORY.index(line) % 2:
			console_set_default_foreground(CONSOLE_WINDOW,Color(185,185,185))
		else:
			console_set_default_foreground(CONSOLE_WINDOW,white)
		
		while len(line):
			console_print(CONSOLE_WINDOW,_xoffset,_i,line[:CONSOLE_WINDOW_SIZE[0]])
			line = line[CONSOLE_WINDOW_SIZE[0]:]
			_xoffset += 1
			_i += 1
			
	console_print(CONSOLE_WINDOW,0,CONSOLE_WINDOW_SIZE[1]-1,'#'+KEYBOARD_STRING[0])

def log(text):
	CONSOLE_HISTORY.append(text)

def message(text):
	MESSAGE_LOG.append(text)

def end_of_frame_terraform(editing_prefab=False):
	console_blit(ITEM_WINDOW,0,0,ITEM_WINDOW_SIZE[0],ITEM_WINDOW_SIZE[1],0,0,MAP_WINDOW_SIZE[1])
	console_blit(PREFAB_WINDOW,
		0,
		0,
		PREFAB_WINDOW_SIZE[0],
		PREFAB_WINDOW_SIZE[1],
		0,
		PREFAB_WINDOW_OFFSET[0],
		PREFAB_WINDOW_OFFSET[1])
	console_blit(X_CUTOUT_WINDOW,
		0,
		0,
		X_CUTOUT_WINDOW_SIZE[0],
		X_CUTOUT_WINDOW_SIZE[1],
		0,
		PREFAB_WINDOW_OFFSET[0],
		11)
	console_blit(Y_CUTOUT_WINDOW,
		0,
		0,
		Y_CUTOUT_WINDOW_SIZE[0],
		Y_CUTOUT_WINDOW_SIZE[1],
		0,
		PREFAB_WINDOW_OFFSET[0],
		22)
	
	if editing_prefab:
		console_set_default_foreground(0,white)
	else:
		console_set_default_foreground(0,Color(185,185,185))
	
	#TODO: Figure these out using math
	console_print(0,PREFAB_WINDOW_OFFSET[0],0,'Prefab Editor')
	console_print(0,PREFAB_WINDOW_OFFSET[0],11,'West -X Cutout- East')
	console_print(0,PREFAB_WINDOW_OFFSET[0],22,'North -Y Cutout- South')

def end_of_frame_reactor3():
	console_blit(MESSAGE_WINDOW,0,0,MESSAGE_WINDOW_SIZE[0],MESSAGE_WINDOW_SIZE[1],0,0,MAP_WINDOW_SIZE[1])

def end_of_frame():
	console_blit(MAP_WINDOW,0,0,MAP_WINDOW_SIZE[0],MAP_WINDOW_SIZE[1],0,0,0)
	
	for menu in MENUS:
		console_blit(menu['settings']['console'],0,0,
			menu['settings']['size'][0],
			menu['settings']['size'][1],0,
			menu['settings']['position'][0],
			menu['settings']['position'][1],1,0.5)
	
	if SETTINGS['draw console']:
		console_blit(CONSOLE_WINDOW,0,0,CONSOLE_WINDOW_SIZE[0],CONSOLE_WINDOW_SIZE[1],0,0,0,1,0.5)
	
	console_flush()

def window_is_closed():
	return console_is_window_closed()
