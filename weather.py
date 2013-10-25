from globals import *

import libtcodpy as tcod

def change_weather():
	_weather = {}
	_weather['events'] = 4
	_weather['colors'] = []
	_weather['color_indexes'] = []
	_weather['light_types'] = ['night', 'overcast', 'sunny']
	
	_colors = []
	_indexes = []
	_i = 0
	for light_type in _weather['light_types']:
		_weather['color_indexes'].append((WORLD_INFO['length_of_day']/_weather['events'])*_i)
		_i += 1
		
		if light_type == 'night':
			_weather['colors'].append((28, 0, 12))
		elif light_type == 'overcast':
			_weather['colors'].append((0, 125, 255))
		elif light_type == 'sunny':
			_weather['colors'].append((255, 165, 0))
	
	create_light_map(_weather)
	
	WORLD_INFO['weather'].update(_weather)

def get_lighting():
	print WORLD_INFO['weather']['light_map'][WORLD_INFO['real_time_of_day']-1]
	return WORLD_INFO['weather']['light_map'][WORLD_INFO['real_time_of_day']-1]

def create_light_map(weather):
	print weather.keys()
	weather['light_map'] = tcod.color_gen_map([tcod.Color(c[0], c[1], c[2]) for c in weather['colors']], weather['color_indexes'])