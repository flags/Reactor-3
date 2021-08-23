from globals import *

import weather

import zones
import alife
import items
import life

def suicide():
	life.kill(LIFE[SETTINGS['following']], 'suicide')

def kill(life_id):
	life.kill(LIFE[life_id], 'suicide')

def stop():
	LIFE[SETTINGS['following']]['path'] = []

def clean_slate():
	for alife in list(LIFE.values()):
		if alife['id'] == SETTINGS['controlling'] or alife['dead']:
			continue
		
		life.kill(alife, 'an act of treason')

def make_hungry(life_id):
	LIFE[life_id]['hunger'] = 500
	
def world_hunger():
	for l in list(LIFE.values()):
		l['hunger'] = 500

def make_thirsty(life_id):
	LIFE[life_id]['thirst'] = 500

def simple_lights():
	SETTINGS['draw light'] = False

def time(time):
	WORLD_INFO['real_time_of_day'] = time

def timescale(scale):
	WORLD_INFO['time_scale'] = scale

def warp(x, y):
	LIFE[SETTINGS['controlling']]['pos'][0] = x
	LIFE[SETTINGS['controlling']]['pos'][1] = y

def camps():
	alife.camps.debug_camps()

def food():
	items.create_item('corn', position=LIFE[SETTINGS['controlling']]['pos'])

def drink():
	items.create_item('soda', position=LIFE[SETTINGS['controlling']]['pos'])

def give(item):
	items.create_item(item, position=LIFE[SETTINGS['controlling']]['pos'])

def day():
	WORLD_INFO['real_time_of_day'] = 1500

def night():
	WORLD_INFO['real_time_of_day'] = 0

def toss():
	life.push(LIFE[SETTINGS['controlling']], 0, 2)

def soldier():
	LIFE[SETTINGS['following']]['stats']['firearms'] = 10

def weather():
	weather.change_weather()