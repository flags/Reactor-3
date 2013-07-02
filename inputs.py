from cStringIO import StringIO
from globals import *

from debug import *

import libtcodpy as tcod
import graphics as gfx

import scripting

import sys

def reset_input():
	for key in INPUT:
		INPUT[key] = False

def get_input():
	tcod.sys_check_for_event(tcod.EVENT_ANY, KEY, MOUSE)
	reset_input()
	get_keyboard_input()
	get_mouse_input()

def get_keyboard_input():
	global KEYBOARD_STRING
	
	if not KEY.vk:
		return False

	if KEY.c:
		_key = chr(KEY.c)
	else:
		if KEY.pressed:
			if KEY.vk == tcod.KEY_RIGHT:
				INPUT['right'] = True
			elif KEY.vk == tcod.KEY_LEFT:
				INPUT['left'] = True
			elif KEY.vk == tcod.KEY_DOWN:
				INPUT['down'] = True
			elif KEY.vk == tcod.KEY_UP:
				INPUT['up'] = True
		
		return True
	
	if SETTINGS['draw console']:
		if KEY.vk == tcod.KEY_ENTER and len(KEYBOARD_STRING[0]):
			#Taken from: http://stackoverflow.com/a/3906309
			old_stdout = sys.stdout
			redirected_output = sys.stdout = StringIO()
			exec(scripting.parse_console(KEYBOARD_STRING[0].rstrip()))
			sys.stdout = old_stdout
			
			gfx.log('>'+KEYBOARD_STRING[0].rstrip())
			gfx.log(' '+redirected_output.getvalue())
			
			KEYBOARD_STRING[0] = ''
			
		elif KEY.vk == tcod.KEY_BACKSPACE:
			KEYBOARD_STRING[0] = KEYBOARD_STRING[0][:len(KEYBOARD_STRING[0])-1]
	
	if not INPUT.has_key(_key):
		INPUT[_key] = False
	
	if not INPUT[_key] and KEY.pressed:
		if SETTINGS['draw console']:
			KEYBOARD_STRING[0] += _key
		
		INPUT[_key] = True
	else:
		#if INPUT[_key]:
		#	#TODO: A 'true' release...?
		#	pass
		
		INPUT[_key] = False

def get_mouse_input():
	#TODO: I can't get mouse input to work properly...
	pass
