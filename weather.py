from globals import *

import libtcodpy as tcod

import numbers

def change_weather():
	_weather = {}
	_weather['events'] = 7
	_weather['colors'] = []
	_weather['color_indexes'] = []
	_weather['light_types'] = ['night', 'sunrise', 'clear', 'clear', 'clear', 'sunset', 'night']
	
	_colors = []
	_indexes = []
	_i = 0
	for light_type in _weather['light_types']:
		_weather['color_indexes'].append((WORLD_INFO['length_of_day']/_weather['events'])*_i)
		_i += 1
		
		if light_type == 'night':
			#_weather['colors'].append((28, 0, 12))
			_weather['colors'].append((255, 165, 0))
		elif light_type == 'overcast':
			_weather['colors'].append((0, 12, 12))
		elif light_type == 'clear':
			_weather['colors'].append((0, 0, 0))
		elif light_type == 'sunrise':
			_weather['colors'].append((19, 86, 100))
		elif light_type == 'sunset':
			_weather['colors'].append((19, 50, 100))
	
	create_light_map(_weather)
	
	WORLD_INFO['weather'].update(_weather)

def get_lighting():
	#print WORLD_INFO['weather']['light_map'][WORLD_INFO['real_time_of_day']-1], WORLD_INFO['real_time_of_day']
	_time = numbers.clip(WORLD_INFO['real_time_of_day'], 0, len(WORLD_INFO['weather']['light_map'])-1)
	return WORLD_INFO['weather']['light_map'][_time]

def create_light_map(weather):
	weather['light_map'] = tcod.color_gen_map([tcod.Color(c[0], c[1], c[2]) for c in weather['colors']], weather['color_indexes'])