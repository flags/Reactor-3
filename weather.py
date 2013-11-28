from globals import *

import libtcodpy as tcod

import numbers

def change_weather():
	_weather = {}
	_weather['events'] = 7
	_weather['colors'] = []
	_weather['color_indexes'] = []
	_weather['light_types'] = ['night', 'sunrise', 'clear', 'overcast', 'overcast', 'sunset', 'night']
	
	_colors = []
	_indexes = []
	_i = 0
	for light_type in _weather['light_types']:
		_weather['color_indexes'].append((WORLD_INFO['length_of_day']/_weather['events'])*_i)
		_i += 1
		
		if light_type == 'night':
			#_weather['colors'].append((28, 0, 12))
			_weather['colors'].append({'colors': (255, 165, 0), 'type': light_type})
		elif light_type == 'overcast':
			_weather['colors'].append({'colors': (60, 60, 60), 'type': light_type})
		elif light_type == 'clear':
			_weather['colors'].append({'colors': (0, 0, 0), 'type': light_type})
		elif light_type == 'sunrise':
			_weather['colors'].append({'colors': (19, 86, 100), 'type': light_type})
		elif light_type == 'sunset':
			_weather['colors'].append({'colors': (19, 50, 100), 'type': light_type})
	
	create_light_map(_weather)
	
	WORLD_INFO['weather'].update(_weather)

def get_lighting():
	#print WORLD_INFO['weather']['light_map'][WORLD_INFO['real_time_of_day']-1], WORLD_INFO['real_time_of_day']
	_time = numbers.clip(WORLD_INFO['real_time_of_day'], 0, len(WORLD_INFO['weather']['light_map'])-1)
	return WORLD_INFO['weather']['light_map'][_time]

def create_light_map(weather):
	weather['light_map'] = tcod.color_gen_map([tcod.Color(c['colors'][0], c['colors'][1], c['colors'][2]) for c in weather['colors']], weather['color_indexes'])