from globals import *

import libtcodpy as tcod
import graphics as gfx

import numbers
import alife
import maps

import random


def change_weather():
	_weather = {}
	_weather['events'] = 6
	_weather['colors'] = []
	_weather['color_indexes'] = []
	_weather['light_types'] = ['dark_night',
	                           'sunrise',
	                           'overcast_thunderstorm',
	                           'overcast_thunderstorm',
	                           'overcast_rain',
	                           'overcast',
	                           'dark_night_rain']
	
	_colors = []
	_indexes = []
	_i = 0
	for light_type in _weather['light_types']:
		_weather['color_indexes'].append((WORLD_INFO['length_of_day']/_weather['events'])*_i)
		_i += 1
		
		if 'dark_night' in light_type:
			_event = {'name': 'Dark', 'colors': (255, 165, 25), 'type': light_type}
		elif 'night' in light_type:
			_event = {'name': 'Clear', 'colors': (255, 165, 0), 'type': light_type}
		elif light_type == 'overcast':
			_event = {'name': 'Overcast', 'colors': (60, 60, 60), 'type': light_type}
		elif light_type == 'overcast_rain':
			_event = {'name': 'Overcast (Rain)', 'colors': (60, 60, 60), 'type': light_type}
		elif light_type == 'overcast_thunderstorm':
			_event = {'name': 'Overcast (Thunderstorm)', 'colors': (60, 60, 60), 'type': light_type}
		elif light_type == 'clear':
			_event = {'name': 'Clear', 'colors': (0, 0, 0), 'type': light_type}
		elif light_type == 'sunrise':
			_event = {'name': 'Clear', 'colors': (19, 86, 100), 'type': light_type}
		elif 'sunset' in light_type:
			_event = {'name': 'Clear', 'colors': (19, 50, 100), 'type': light_type}
		
		_event['effects'] = []
		if 'thunderstorm' in light_type:
			_event['effects'].extend(['raining', 'lightning'])
		
		if 'rain' in light_type:
			_event['effects'].append('raining')
		
		_weather['colors'].append(_event)
	
	create_light_map(_weather)
	
	WORLD_INFO['weather'].update(_weather)

def get_lighting():
	_time = numbers.clip(WORLD_INFO['real_time_of_day'], 0, len(WORLD_INFO['weather']['light_map'])-1)
	return WORLD_INFO['weather']['light_map'][_time]

def create_light_map(weather):
	weather['light_map'] = tcod.color_gen_map([tcod.Color(c['colors'][0], c['colors'][1], c['colors'][2]) for c in weather['colors']], weather['color_indexes'])

def get_weather_status():
	_current_weather = WORLD_INFO['real_time_of_day']/(WORLD_INFO['length_of_day']/len(WORLD_INFO['weather']['colors']))
	_current_weather = numbers.clip(_current_weather, 0, len(WORLD_INFO['weather']['colors'])-1)
	
	return WORLD_INFO['weather']['colors'][_current_weather]['name']

def generate_effects(size):
	_current_weather = WORLD_INFO['real_time_of_day']/(WORLD_INFO['length_of_day']/len(WORLD_INFO['weather']['colors']))
	_current_weather = numbers.clip(_current_weather, 0, len(WORLD_INFO['weather']['colors'])-1)
	
	if 'raining' in WORLD_INFO['weather']['colors'][_current_weather]['effects']:
		rain(size)
	
	if 'lightning' in WORLD_INFO['weather']['colors'][_current_weather]['effects'] and not random.randint(0, 200):
		RGB_LIGHT_BUFFER[0] *= 0
		RGB_LIGHT_BUFFER[1] *= 0
		RGB_LIGHT_BUFFER[2] *= 0

def rain(size):
	_running_time = WORLD_INFO['real_time_of_day'] - WORLD_INFO['real_time_of_day']/(WORLD_INFO['length_of_day']/len(WORLD_INFO['weather']['colors']))*(WORLD_INFO['length_of_day']/len(WORLD_INFO['weather']['colors']))
	
	_rate = .009
	
	for i in range(0, int(round(_running_time*_rate))):
		_x = random.randint(0, size[0]-1)
		_y = random.randint(0, size[1]-1)
		_skip = False
		
		for z in range(LIFE[SETTINGS['controlling']]['pos'][2]+1, MAP_SIZE[2]):
			if maps.is_solid((CAMERA_POS[0]+_x, CAMERA_POS[1]+_y, z)):
				_skip = True
				break
		
		if _skip:
			continue
		
		if not alife.sight.is_in_fov(LIFE[SETTINGS['controlling']], (CAMERA_POS[0]+_x, CAMERA_POS[1]+_y)):
			continue
		
		REFRESH_POSITIONS.append((_x, _y))
		
		gfx.tint_tile(_x, _y, tcod.blue, random.uniform(0.1, 0.6))
	