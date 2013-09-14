from globals import *

import pathfinding
import zones
import alife
import life

def suicide():
	life.kill(LIFE[SETTINGS['controlling']], 'suicide')

def kill(life_id):
	life.kill(LIFE[life_id], 'suicide')

def make_hungry(life_id):
	LIFE[life_id]['hunger'] = 500

def make_thirsty(life_id):
	LIFE[life_id]['thirst'] = 500

def simple_lights():
	SETTINGS['draw light'] = False

def love_me():
	for target in LIFE[SETTINGS['controlling']]['know']:
		alife.brain.add_impression(LIFE[target], LIFE[SETTINGS['controlling']]['id'], 'follow', {'influence': 100})

def time(time):
	WORLD_INFO['real_time_of_day'] = time

def timescale(scale):
	WORLD_INFO['time_scale'] = scale

def warp(x, y):
	LIFE[SETTINGS['controlling']]['pos'][0] = x
	LIFE[SETTINGS['controlling']]['pos'][1] = y
	
def d():
	_pos = LIFE[SETTINGS['controlling']]['pos']
	_next = [_pos[0], _pos[1]-10]
	#print pathfinding.dijkstra_path(LIFE[SETTINGS['controlling']], _pos, _next, life.can_walk_to(LIFE[SETTINGS['controlling']], _next))
	zones.dijkstra_map([], [zones.get_zone_at_coords(LIFE[SETTINGS['controlling']]['pos'])])

def toss():
	life.push(LIFE[SETTINGS['controlling']], 0, 2)