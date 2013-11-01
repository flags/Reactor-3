from globals import *

import libtcodpy as tcod
import graphics as gfx
import life as lfe

import historygen
import profiles
import effects
import weather
import mapgen
import cache
import logic
import items
import tiles
import alife
import life
import maps

import threading
import logging
import numbers
import random
import time
import json
import sys

BASE_ITEMS = ['sneakers',
              'blue jeans',
              'white t-shirt',
              'leather backpack',
              'radio',
              'frag grenade',
              'molotov']
RECRUIT_ITEMS = ['glock', '9x19mm magazine', 'soda', 'corn']

for i in range(10):
	RECRUIT_ITEMS.append('9x19mm round')

class Runner(threading.Thread):
	def __init__(self, amount):
		self.amount = amount
		self.running = True
		
		threading.Thread.__init__(self)
	
	def run(self):
		simulate_life(self.amount)
		self.running = False


def draw_world_stats():
	if not 'last_time' in WORLD_INFO:
		WORLD_INFO['last_time'] = []
	
	WORLD_INFO['last_time'].append(WORLD_INFO['ticks']/(time.time()-WORLD_INFO['inittime']))
	
	if len(WORLD_INFO['last_time'])>5:
		WORLD_INFO['last_time'].pop(0)
	
	tcod.console_print(0, 0, 0, 'World Generation')
	tcod.console_print(0, 0, 2, 'Simulating world: %s (%.2f t/s)' % (WORLD_INFO['ticks'], (sum(WORLD_INFO['last_time'])/len(WORLD_INFO['last_time']))))
	tcod.console_print(0, 0, 3, 'Queued ALife actions: %s' % sum([len(alife['actions']) for alife in [LIFE[i] for i in LIFE]]))
	tcod.console_print(0, 0, 4, 'Total ALife memories: %s' % sum([len(alife['memory']) for alife in [LIFE[i] for i in LIFE]]))
	tcod.console_print(0, 0, 5, '%s %s' % (TICKER[int(WORLD_INFO['ticks'] % len(TICKER))], '=' * int((WORLD_INFO['ticks']/float(WORLD_INFO['start_age']))*10)))
	tcod.console_print(0, 0, 6, 'Time elapsed: %.2f' % (time.time()-WORLD_INFO['inittime']))
	tcod.console_flush()

def simulate_life(amount):
	while amount:
		#try:
		logic.tick_all_objects(WORLD_INFO['map'])
		#except Exception as e:
		#logging.error('Crash: %s' % e)
		#SETTINGS['running'] = False
		#sys.exit(1)
		
		amount -= 1

def generate_world(source_map, life_density='Sparse', wildlife_density='Sparse', simulate_ticks=1000, combat_test=False, save=True, thread=True):
	WORLD_INFO['inittime'] = time.time()
	WORLD_INFO['start_age'] = simulate_ticks
	WORLD_INFO['life_density'] = life_density
	WORLD_INFO['wildlife_density'] = wildlife_density
	WORLD_INFO['seed'] = time.time()
	WORLD_INFO['combat_test'] = combat_test
	
	random.seed(WORLD_INFO['seed'])
	
	if WORLD_INFO['life_density'] == 'Sparse':
		WORLD_INFO['life_spawn_interval'] = [0, (1000, 1200)]
	elif WORLD_INFO['life_density'] == 'Medium':
		WORLD_INFO['life_spawn_interval'] = [0, (800, 999)]
	elif WORLD_INFO['life_density'] == 'Heavy':
		WORLD_INFO['life_spawn_interval'] = [0, (600, 799)]
	else:
		WORLD_INFO['life_spawn_interval'] = [-1, (600, 799)]
	
	if WORLD_INFO['wildlife_density'] == 'Sparse':
		WORLD_INFO['wildlife_spawn_interval'] = [2500, (770, 990)]
	elif WORLD_INFO['wildlife_density'] == 'Medium':
		WORLD_INFO['wildlife_spawn_interval'] = [2500, (550, 700)]
	elif WORLD_INFO['wildlife_density'] == 'Heavy':
		WORLD_INFO['wildlife_spawn_interval'] = [2500, (250, 445)]
	else:
		WORLD_INFO['wildlife_spawn_interval'] = [-1, (250, 445)]

	weather.change_weather()
	print 'STARTING!',WORLD_INFO['weather']
	#create_region_spawns()
	randomize_item_spawns()
	
	alife.camps.create_all_camps()
	
	if thread:
		tcod.console_rect(0,0,0,WINDOW_SIZE[0],WINDOW_SIZE[1],True,flag=tcod.BKGND_DEFAULT)
		_r = Runner(simulate_ticks)
		_r.start()

		while _r.running:
			draw_world_stats()
			
			if not SETTINGS['running']:
				return False
	else:
		simulate_life(simulate_ticks)
	
	lfe.focus_on(create_player())
	WORLD_INFO['id'] = 0
	
	if save:
		WORLD_INFO['id'] = profiles.create_world()
		save_world()
	
	logging.info('World generation complete (took %.2fs)' % (time.time()-WORLD_INFO['inittime']))

def load_world(world):
	gfx.title('Loading...')
	
	WORLD_INFO['id'] = world
	maps.load_map('map', base_dir=profiles.get_world_directory(world))

	logging.debug('Loading life from disk...')
	with open(os.path.join(profiles.get_world_directory(WORLD_INFO['id']), 'life.dat'), 'r') as e:
		LIFE.update(json.loads(e.readline()))

	logging.debug('Loading items from disk...')
	with open(os.path.join(profiles.get_world_directory(WORLD_INFO['id']), 'items.dat'), 'r') as e:
		ITEMS.update(json.loads(e.readline()))
	
	logging.debug('Loading historic items...')
	#with open(os.path.join(profiles.get_world_directory(WORLD_INFO['id']), 'items_history.dat'), 'r') as e:
	#	ITEMS_HISTORY.update(json.loads(''.join(e.readlines())))
	
	maps.reset_lights()
	
	SETTINGS['controlling'] = None
	SETTINGS['following'] = None
	for life in LIFE.values():
		if life['dead']:
			continue
		
		if 'player' in life:
			SETTINGS['controlling'] = life['id']
			lfe.focus_on(life)
			break
	
	lfe.load_all_life()
	items.reload_all_items()
	
	#logging.debug('Rendering map slices...')
	#maps.render_map_slices()
	
	logging.info('World loaded.')

def save_world():
	gfx.title('Saving...')
	logging.debug('Offloading world...')

	logging.debug('Saving items...')
	items.save_all_items()	
	
	maps.save_map('map', base_dir=profiles.get_world_directory(WORLD_INFO['id']))
	
	logging.debug('Saving life...')
	_life = life.save_all_life()
	
	with open(os.path.join(profiles.get_world_directory(WORLD_INFO['id']), 'life.dat'), 'w') as e:
		e.write(_life)
	
	with open(os.path.join(profiles.get_world_directory(WORLD_INFO['id']), 'items.dat'), 'w') as e:
		e.write(json.dumps(ITEMS))
	
	#cache.commit_cache('items')
	#cache.save_cache('items')
	
	items.reload_all_items()
	
	logging.info('World saved.')

def cleanup():
	if not WORLD_INFO['id']:
		return False
	
	gfx.title('Saving cache...')
	cache.save_cache('items')

def reset_world():
	SETTINGS['following'] = None
	SETTINGS['controlling'] = None
	
	logging.debug('World reset.')

def randomize_item_spawns():
	for building in WORLD_INFO['reference_map']['buildings']:
		_chunk_key = random.choice(alife.references.get_reference(building))
		_chunk = maps.get_chunk(_chunk_key)
		
		if not _chunk['ground']:
			continue
		
		if random.randint(0, 100)>=80:
			for i in range(0, 1+random.randint(0, 3)):
				_rand_pos = random.choice(_chunk['ground'])
				items.create_item('.22 rifle', position=[_rand_pos[0], _rand_pos[1], 2])
				items.create_item('.22 LR magazine', position=[_rand_pos[0], _rand_pos[1], 2])
			
			for i in range(10):
				_rand_pos = random.choice(_chunk['ground'])
				items.create_item('.22 LR cartridge', position=[_rand_pos[0], _rand_pos[1], 2])
		elif random.randint(0, 100)>=70:
			_items = ['corn', 'soda']
			for i in range(0, 1+random.randint(0, 3)):
				_rand_pos = random.choice(_chunk['ground'])
				items.create_item(random.choice(_items), position=[_rand_pos[0], _rand_pos[1], 2])
		
		for i in range(0, 1+random.randint(0, 3)):
			_rand_pos = random.choice(_chunk['ground'])
			items.create_item(random.choice(RECRUIT_ITEMS), position=[_rand_pos[0], _rand_pos[1], 2])

def get_spawn_point_around(pos, area=5):
	_x = numbers.clip(pos[0]+random.randint(-area, area), 0, MAP_SIZE[0]-1)
	_y = numbers.clip(pos[1]+random.randint(-area, area), 0, MAP_SIZE[1]-1)
	
	return (_x, _y)

def get_spawn_point(randomize=False):
	if WORLD_INFO['reference_map']['roads'] and not randomize:
		_entry_road_keys = []
		for road in WORLD_INFO['reference_map']['roads']:
			for chunk_key in alife.references.get_reference(road):
				_pos = WORLD_INFO['chunk_map'][chunk_key]['pos']
				
				if len(mapgen.get_neighbors_of_type(WORLD_INFO, _pos, 'any')) <= 3:
					_entry_road_keys.append(chunk_key)
		
		if _entry_road_keys:
			
			_spawn_pos = random.choice(WORLD_INFO['chunk_map'][random.choice(_entry_road_keys)]['ground'])
			
			return [_spawn_pos[0], _spawn_pos[1], 2]

	_start_seed = random.randint(0, 3)
	
	if not _start_seed:
		_spawn = (random.randint(0, MAP_SIZE[0]-1), 0, 2)
	elif _start_seed == 1:
		_spawn = (MAP_SIZE[0]-1, random.randint(0, MAP_SIZE[1]-1), 2)
	elif _start_seed == 2:
		_spawn = (random.randint(0, MAP_SIZE[0]-1), MAP_SIZE[1]-1, 2)
	else:
		_spawn = (0, random.randint(0, MAP_SIZE[1]-1), 2)
	
	return _spawn

def generate_wildlife():
	_spawn = get_spawn_point(randomize=True)
	
	_p = life.create_life('dog',
          name=['Wild', 'Dog'],
          position=[_spawn[0], _spawn[1], 2])
	
	_group = alife.groups.create_group(_p)
	
	_children = []
	for i in range(2, 6):
		_spawn = get_spawn_point_around(_spawn)
		
		_c = life.create_life('dog',
	          name=['(Young) Wild', 'Dog'],
	          position=[_spawn[0], _spawn[1], 2])
		_c['icon'] = 'd'
		
		alife.groups.add_member(_group, _c['id'])
		
		alife.brain.meet_alife(_p, _c)
		alife.brain.meet_alife(_c, _p)
		
		alife.brain.flag_alife(_p, _c['id'], 'son')
		alife.brain.flag_alife(_c, _p['id'], 'father')
		
		_children.append(_c)
	
	for _c1 in _children:
		for _c2 in _children:
			if _c1['id'] == _c2['id']:
				continue
			
			alife.brain.meet_alife(_c1, _c2)
			alife.brain.meet_alife(_c2, _c1)
			
			alife.brain.flag_alife(_c1, _c2['id'], 'sibling')
			alife.brain.flag_alife(_c2, _c1['id'], 'sibling')
	
	#_spawn = get_spawn_point(randomize=True)
	
	#for i in range(4):
	#	_p = life.create_life('night_terror',
	#		position=[_spawn[0], _spawn[1], 2])

def generate_life():
	_spawn = get_spawn_point()
	
	if len(WORLD_INFO['groups'])>=2:
		_alife = life.create_life('human', map=WORLD_INFO['map'], position=[_spawn[0], _spawn[1], 2])
		#_alife['thirst'] = random.randint(_alife['thirst_max']/4, _alife['thirst_max']/3)
		
		if len(LIFE) == 1:
			logging.warning('No leaders. Creating one manually...')
			_alife['stats']['is_leader'] = True
		
		for item in BASE_ITEMS:
			life.add_item_to_inventory(_alife, items.create_item(item))
		
		return True
	
	_group_members = []
	
	for i in range(3):
		_alife = life.create_life('human', map=WORLD_INFO['map'], position=[_spawn[0], _spawn[1], 2])
		
		for item in BASE_ITEMS:
			life.add_item_to_inventory(_alife, items.create_item(item))
		
		if not _group_members:
			_alife['stats']['is_leader'] = True
			_group = alife.groups.create_group(_alife)
		
		_group_members.append(_alife)
	
	for m1 in _group_members:
		if m1['id'] == _group_members[0]['id']:
			continue
		
		alife.groups.add_member(_group, m1['id'])
	
	#for item in RECRUIT_ITEMS:
	#	life.add_item_to_inventory(alife, items.create_item(item))

def create_player():
	PLAYER = life.create_life('human',
		name=['Tester','Toaster'],
		position=get_spawn_point())
	PLAYER['stats'].update(historygen.create_background(life))
	PLAYER['player'] = True
	
	for item in BASE_ITEMS:
		life.add_item_to_inventory(PLAYER, items.create_item(item))
	
	life.add_item_to_inventory(PLAYER, items.create_item('mp5'))
	life.add_item_to_inventory(PLAYER, items.create_item('mp5 magazine'))
	
	for i in range(10):
		life.add_item_to_inventory(PLAYER, items.create_item('9x19mm round'))
	
	#for item in RECRUIT_ITEMS:
	#	life.add_item_to_inventory(PLAYER, items.create_item(item))

	SETTINGS['controlling'] = PLAYER['id']
	
	lfe.focus_on(LIFE[SETTINGS['controlling']])
	
	#_i = items.get_item_from_uid(items.create_item('burner', position=PLAYER['pos'][:]))
	#items.move(_i, 180, 3)
	
	return PLAYER
	
def create_region_spawns():
	#Step 1: Army Outpost
	for town_seed in WORLD_INFO['refs']['town_seeds']:
		
	for i in range(5):
		generate_wildlife()