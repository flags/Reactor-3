from libtcodpy import *
from globals import *

def reset_input():
	for key in INPUT:
		INPUT[key] = False

def get_input():
	sys_check_for_event(EVENT_KEY_PRESS|EVENT_MOUSE,KEY,MOUSE)
	reset_input()
	get_keyboard_input()
	get_mouse_input()

def get_keyboard_input():
	if KEY.vk == KEY_UP:
		INPUT['up'] = True

	if KEY.vk == KEY_DOWN:
		INPUT['down'] = True

	if KEY.vk == KEY_LEFT:
		INPUT['left'] = True

	if KEY.vk == KEY_RIGHT:
		INPUT['right'] = True

	if KEY.vk == KEY_SPACE:
		INPUT['space'] = True

	if KEY.vk == KEY_ESCAPE:
		INPUT['escape'] = True

def get_mouse_input():
	#TODO: I can't get mouse input to work properly...
	pass