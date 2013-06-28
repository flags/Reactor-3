from globals import *

import alife
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

def love_me():
	for target in SETTINGS['controlling']['know']:
		print target
		alife.brain.add_impression(LIFE[target], SETTINGS['controlling']['id'], 'debug', {'influence': 100})

def time(time):
	WORLD_INFO['time_of_day'] = time