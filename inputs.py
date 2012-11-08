from libtcodpy import *
from globals import *

def reset_input():
	#for key in INPUT:
	#	INPUT[key] = False
	INPUT['left'] = False
	INPUT['right'] = False
	INPUT['up'] = False
	INPUT['down'] = False

def get_input():
	sys_check_for_event(EVENT_ANY,KEY,MOUSE)
	reset_input()
	get_keyboard_input()
	get_mouse_input()

def get_keyboard_input():
	if not KEY.vk:
		return False

	if KEY.c:
		_key = chr(KEY.c)
	else:
		#_key = chr(KEY.vk)
		if KEY.pressed:
			if KEY.vk == KEY_RIGHT:
				INPUT['right'] = True
			elif KEY.vk == KEY_LEFT:
				INPUT['left'] = True
			elif KEY.vk == KEY_DOWN:
				INPUT['down'] = True
			elif KEY.vk == KEY_UP:
				INPUT['up'] = True
		
		return True
	
	if not INPUT.has_key(_key):
		INPUT[_key] = False
	
	if not INPUT[_key] and KEY.pressed:
		INPUT[_key] = True
	else:
		if INPUT[_key]:
			#TODO: A 'true' release...?
			pass
		
		INPUT[_key] = False

def get_mouse_input():
	#TODO: I can't get mouse input to work properly...
	pass