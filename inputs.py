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
	if KEY.c:
		print KEY.c,ord('c')

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

	if KEY.c == ord('c'):
		INPUT['c'] = True

	if KEY.c == ord('d'):
		INPUT['d'] = True

	if KEY.vk == KEY_1:
		INPUT['1'] = True

	if KEY.vk == KEY_2:
		INPUT['2'] = True

	if KEY.vk == KEY_3:
		INPUT['3'] = True

	if KEY.vk == KEY_4:
		INPUT['4'] = True

	if KEY.vk == KEY_5:
		INPUT['5'] = True

def get_mouse_input():
	#TODO: I can't get mouse input to work properly...
	pass