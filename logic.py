from globals import *
from overwatch import situations, core

import libtcodpy as tcod
import graphics as gfx
import alife as alfe

import encounters
import artifacts
import worldgen
import effects
import bad_numbers
import weather
import timers
import dialog
import spawns
import melee
import locks
import cache
import menus
import items
import life
import smp

import logging
import random
import time

def can_tick(ignore_tickrate=False, ignore_pause=False):
	if SETTINGS['controlling'] and not EVENTS and not sum([abs(i) for i in LIFE[SETTINGS['controlling']]['velocity']]):
		if life.is_target_of(LIFE[SETTINGS['controlling']]):
			if not SETTINGS['paused']:
				gfx.message('An enemy appears.', style='important')
			
			SETTINGS['paused'] = True
			
		if not ignore_pause and SETTINGS['paused'] and not LIFE[SETTINGS['controlling']]['actions'] and not LIFE[SETTINGS['controlling']]['dead']:
			return False
	
	if not ignore_tickrate:
		if process_events():
			return False
	elif EVENTS and not ignore_pause:
		return False
	
	if SETTINGS['controlling'] and not ignore_pause and not sum([abs(i) for i in LIFE[SETTINGS['controlling']]['velocity']]):
		if MENUS:
			return False
		
		if LIFE[SETTINGS['controlling']]['targeting']:
			return False
	
		if life.has_dialog(LIFE[SETTINGS['controlling']]):
			return False
	
	if not ignore_tickrate: 
		if time.time()-WORLD_INFO['last_update_time']<1:
			if WORLD_INFO['tps']<30:
				WORLD_INFO['tps'] += 1
			else:
				return False
		else:
			WORLD_INFO['last_update_time'] = time.time()
			WORLD_INFO['tps'] = 0
	
	return True

def tick_all_objects(ignore_tickrate=False, ignore_pause=False):
	if not can_tick(ignore_tickrate=ignore_tickrate, ignore_pause=ignore_pause):
		return False
	
	if melee.process_fights():
		return False
	
	life.tick_all_life(setup=not SETTINGS['smp'] == None)
	effects.calculate_all_effects()
	tick_world()
	timers.tick()
	items.tick_all_items()
	life.tick_all_life()
	
	return True

def tick_world():
	WORLD_INFO['ticks'] += 1
	alfe.groups.get_group_relationships()
	
	if WORLD_INFO['real_time_of_day'] < WORLD_INFO['length_of_day']:
		WORLD_INFO['real_time_of_day'] += WORLD_INFO['time_scale']
	else:
		WORLD_INFO['real_time_of_day'] = 0
		WORLD_INFO['day'] += 1
		weather.change_weather()
	
	if WORLD_INFO['real_time_of_day']>=WORLD_INFO['length_of_day']-22.00 or WORLD_INFO['real_time_of_day']<=WORLD_INFO['length_of_day']*.15:
		if WORLD_INFO['time_of_day'] == 'day':
			gfx.message('Night falls.')
		
		WORLD_INFO['time_of_day'] = 'night'
	else:
		if WORLD_INFO['time_of_day'] == 'night':
			gfx.message('The sun rises.')
		
		WORLD_INFO['time_of_day'] = 'day'
	
	if WORLD_INFO['dynamic_spawn_interval'][0]>0:
		WORLD_INFO['dynamic_spawn_interval'][0] -= 1
	elif not WORLD_INFO['dynamic_spawn_interval'][0]:
		spawns.generate_life(random.choice(['loner', 'bandit']))
			
		WORLD_INFO['dynamic_spawn_interval'][0] = random.randint(WORLD_INFO['dynamic_spawn_interval'][1][0], WORLD_INFO['dynamic_spawn_interval'][1][1])
		
		logging.info('Reset life spawn clock: %s' % WORLD_INFO['dynamic_spawn_interval'][0])
	
	if WORLD_INFO['wildlife_spawn_interval'][0]>0:
		WORLD_INFO['wildlife_spawn_interval'][0] -= 1
	elif not WORLD_INFO['wildlife_spawn_interval'][0]:
		worldgen.generate_wildlife()
			
		WORLD_INFO['wildlife_spawn_interval'][0] = random.randint(WORLD_INFO['wildlife_spawn_interval'][1][0], WORLD_INFO['wildlife_spawn_interval'][1][1])
		
		logging.info('Reset wildlife spawn clock: %s' % WORLD_INFO['wildlife_spawn_interval'][0])
	
	situations.form_scheme()
	situations.execute_scheme()
	artifacts.tick_fields()
	alfe.factions.direct()
	core.evaluate_overwatch_mood()
	
	cache.scan_cache()
	
def is_night():
	if WORLD_INFO['time_of_day'] == 'night':
		return True
	
	return False

def time_until_midnight():
	if is_night():
		return 0
	
	return WORLD_INFO['length_of_day']-WORLD_INFO['real_time_of_day']

def draw_encounter():
	if not LIFE[SETTINGS['controlling']]['encounters']:
		return False
	
	encounters.draw_encounter(LIFE[SETTINGS['controlling']],
		LIFE[SETTINGS['controlling']]['encounters'][0])

def draw_event():
	_event = None
	
	for event in EVENTS:
		if not event['delay']:
			_event = event
			break
	
	if not _event:
		return False
	
	locks.unlock('camera_free')
	gfx.camera_track(_event['pos'])
	
	if len(event['text'])>=MAP_WINDOW_SIZE[0]-1:
		_lines = list(_event['text'].partition(','))
		
		if not len(_lines[1]):
			_lines = list(_event['text'].partition('.'))
		
		if len(_lines[1]):
			_lines.pop(1)
		else:
			lines = ['????']
		
	else:
		_lines = [_event['text']]
	
	for line in _lines:
		if len(line)>=MAP_WINDOW_SIZE[0]-1:
			_lines = ['The most annoying error.']
			break	
	
	_i = 0
	for line in _lines:
		_half = len(line)//2
		_x = bad_numbers.clip((MAP_WINDOW_SIZE[0]//2)-_half, 0, MAP_WINDOW_SIZE[0]-len(line)-1)
		
		gfx.blit_string(_x,
			10+_i,
			line,
		    'overlay')
		
		_i += 1
	
	return True

def show_event(text, time=45, delay=0, life=None, item=None, pos=None, priority=False):
	_event = {'text': text, 'time': time, 'delay': delay, 'life': life}
	
	if life:
		_event['pos'] = life['pos']
	elif item:
		_event['pos'] = item['pos']
	elif pos:
		_event['pos'] = pos
	
	if priority:
		EVENTS.insert(0, _event)
	else:
		EVENTS.append(_event)

def show_next_event():
	if not EVENTS:
		return False
	
	_event = None
	
	for event in EVENTS:
		if not event['delay']:
			_event = event
			break
	
	if not _event:
		return False
	
	EVENTS.remove(_event)
	gfx.refresh_view('map')
	
	if not EVENTS:
		life.focus_on(LIFE[SETTINGS['following']])
		locks.lock('camera_free', reason='No more events')
		
		return False
	
	return True

def process_events():
	if not EVENTS:
		return False
	
	_event = None
	for event in EVENTS:
		if not event['delay']:
			_event = event
			break
	
	if not _event:
		for event in EVENTS:
			if event['delay']:
				event['delay'] -= 1
	
	if not _event:
		return False
	
	if _event['time']>0:
		_event['time'] -= 0.1
		return True
	
	return show_next_event()

def matches(dict1, dict2):
	_break = False
	
	for key in dict2:
		if not key in dict1 or not dict1[key] == dict2[key]:
			return False
	
	return True
