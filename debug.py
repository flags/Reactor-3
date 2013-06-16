from globals import *

import life

def suicide():
	life.kill(SETTINGS['controlling'], 'suicide')

def kill(life_id):
	life.kill(LIFE[life_id], 'suicide')

def make_hungry(life_id):
	LIFE[life_id]['hunger'] = 500

def make_thirsty(life_id):
	LIFE[life_id]['hunger'] = 500

def simple_lights():
	SETTINGS['draw light'] = False

def time(time):
	WORLD_INFO['time_of_day'] = time