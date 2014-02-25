from globals import *

import libtcodpy as tcod
import graphics as gfx
import life as lfe

import historygen
import situations
import language
import profiles
import effects
import weather
import spawns
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
              'white t-shirt']
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
		logic.tick_all_objects()
		#except Exception as e:
		#logging.error('Crash: %s' % e)
		#SETTINGS['running'] = False
		#sys.exit(1)
		
		amount -= 1

def generate_world(source_map, dynamic_spawns='Sparse', wildlife_spawns='Sparse', simulate_ticks=1000, combat_test=False, save=True, thread=True):
	WORLD_INFO['inittime'] = time.time()
	WORLD_INFO['start_age'] = simulate_ticks
	WORLD_INFO['dynamic_spawns'] = dynamic_spawns
	WORLD_INFO['wildlife_spawns'] = wildlife_spawns
	WORLD_INFO['seed'] = time.time()
	WORLD_INFO['combat_test'] = combat_test
	WORLD_INFO['title'] = 'Operation %s' % language.generate_scheme_title().title()
	
	random.seed(WORLD_INFO['seed'])
	
	if WORLD_INFO['dynamic_spawns'] == 'Sparse':
		WORLD_INFO['dynamic_spawn_interval'] = [350, (1000, 1200)]
	elif WORLD_INFO['dynamic_spawns'] == 'Medium':
		WORLD_INFO['dynamic_spawn_interval'] = [350, (800, 999)]
	elif WORLD_INFO['dynamic_spawns'] == 'Heavy':
		WORLD_INFO['dynamic_spawn_interval'] = [350, (600, 799)]
	else:
		WORLD_INFO['dynamic_spawn_interval'] = [-1, (600, 799)]
	
	if WORLD_INFO['wildlife_spawns'] == 'Sparse':
		WORLD_INFO['wildlife_spawn_interval'] = [2500, (770, 990)]
	elif WORLD_INFO['wildlife_spawns'] == 'Medium':
		WORLD_INFO['wildlife_spawn_interval'] = [2500, (550, 700)]
	elif WORLD_INFO['wildlife_spawns'] == 'Heavy':
		WORLD_INFO['wildlife_spawn_interval'] = [2500, (250, 445)]
	else:
		WORLD_INFO['wildlife_spawn_interval'] = [-1, (250, 445)]

	weather.change_weather()
	create_region_spawns()
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
	
	_config_directory, _worlds_directory = profiles.has_reactor3()
	_version_file = os.path.join(_worlds_directory, WORLD_INFO['id'], 'version.txt')
	
	with open(_version_file, 'w') as version_file:
		version_file.write(VERSION)

	logging.debug('Saving items...')
	items.save_all_items()
	
	maps.save_map('world', base_dir=profiles.get_world_directory(WORLD_INFO['id']))
	
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
	for chunk_key in WORLD_INFO['chunk_map']:
		_chunk = maps.get_chunk(chunk_key)
		
		if not 'spawn_items' in _chunk['flags']:
			continue
		
		for item in _chunk['flags']['spawn_items']:
			if random.uniform(0, 1)<item['rarity']:
				continue
			
			for i in range(item['amount']):
				_rand_pos = random.choice(_chunk['ground'])[:]
				_rand_pos.append(2)
				items.create_item(item['item'], position=_rand_pos)
		
	return False

	for building in WORLD_INFO['reference_map']['buildings']:
		_chunk_key = random.choice(alife.references.get_reference(building))
		_chunk = maps.get_chunk(_chunk_key)
		
		if not _chunk['ground']:
			continue
		
		if random.randint(0, 100)>=65:
			for i in range(0, 1+random.randint(0, 3)):
				_rand_pos = random.choice(_chunk['ground'])
				items.create_item('.22 rifle', position=[_rand_pos[0], _rand_pos[1], 2])
				items.create_item('.22 LR magazine', position=[_rand_pos[0], _rand_pos[1], 2])
			
			for i in range(10):
				_rand_pos = random.choice(_chunk['ground'])
				items.create_item('.22 LR cartridge', position=[_rand_pos[0], _rand_pos[1], 2])
		elif random.randint(0, 100)>=40:
			_items = ['corn', 'soda']
			for i in range(0, 1+random.randint(0, 3)):
				_rand_pos = random.choice(_chunk['ground'])
				items.create_item(random.choice(_items), position=[_rand_pos[0], _rand_pos[1], 2])
		
		for i in range(0, 1+random.randint(0, 3)):
			_rand_pos = random.choice(_chunk['ground'])
			items.create_item(random.choice(RECRUIT_ITEMS), position=[_rand_pos[0], _rand_pos[1], 2])

def get_spawn_point(randomize=False, zone_entry_point=False):
	if zone_entry_point:
		_pos = random.choice(WORLD_INFO['chunk_map'][WORLD_INFO['zone_entry_chunk_key']]['ground'])
		
		return [_pos[0], _pos[1], 2]
	
	if WORLD_INFO['reference_map']['roads'] and not randomize:
		_entry_road_keys = []
		for road in WORLD_INFO['reference_map']['roads']:
			for chunk_key in alife.references.get_reference(road):
				_pos = WORLD_INFO['chunk_map'][chunk_key]['pos']
				
				if len(mapgen.get_neighbors_of_type(WORLD_INFO, chunk_key, 'any')) <= 3:
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
	_spawn = get_spawn_point()
	_group_members = []
	
	for i in range(3):
		_alife = life.create_life('dog', map=WORLD_INFO['map'], position=[_spawn[0], _spawn[1], 2])
		
		if not _group_members:
			_alife['stats']['is_leader'] = True
			_group = alife.groups.create_group(_alife)
		
		_group_members.append(_alife)
	
	for m1 in _group_members:
		if m1['id'] == _group_members[0]['id']:
			continue
		
		alife.groups.discover_group(m1, _group)
		alife.groups.add_member(_group_members[0], _group, m1['id'])
		alife.groups.add_member(m1, _group, m1['id'])
		m1['group'] = _group
		alife.groups.set_leader(m1, _group, _group_members[0]['id'])
	
	for m1 in _group_members:
		for m2 in _group_members:
			if m1 == m2:
				continue
			
			alife.stats.establish_trust(m1, m2['id'])
	
	alife.speech.inform_of_group_members(_group_members[0], None, _group)

def create_player():
	PLAYER = life.create_life('human',
		name=['Tester','Toaster'],
		position=get_spawn_point(zone_entry_point=True))
	PLAYER['stats'].update(historygen.create_background(life))
	PLAYER['player'] = True
	
	for item in BASE_ITEMS:
		life.add_item_to_inventory(PLAYER, items.create_item(item))
	
	#life.add_item_to_inventory(PLAYER, items.create_item('glock'))
	#life.add_item_to_inventory(PLAYER, items.create_item('9x19mm magazine'))
	#life.add_item_to_inventory(PLAYER, items.create_item('electric lantern'))
	#life.add_item_to_inventory(PLAYER, items.create_item('aspirin'))
	
	#for i in range(17):
	#	life.add_item_to_inventory(PLAYER, items.create_item('9x19mm round'))

	SETTINGS['controlling'] = PLAYER['id']
	situations.create_intro_story()
	
	lfe.focus_on(LIFE[SETTINGS['controlling']])
	
	return PLAYER
	
def create_region_spawns():
	return False

	#Step 1: Army Outpost
	for outpost in WORLD_INFO['refs']['outposts']:
		generate_outpost(outpost)
	
	#return False

	_survival = True
	for town in WORLD_INFO['refs']['towns']:
		_spawn_chunk = random.choice(town)
		
		while maps.get_chunk(_spawn_chunk)['type'] == 'town':
			_spawn_chunk = random.choice(town)
	
		if _survival:
			_type = 'survival'
			_survival = False
		else:
			_type = 'crime'
	
		spawns.generate_group('bandit',
	                         amount=random.randint(4, 6),
	                         group_motive=_type,
	                         spawn_chunks=[_spawn_chunk])
	
	return False

	#Step 3: Rookie village
	_spawn_chunks = random.choice([t['rooms'] for t in WORLD_INFO['refs']['villages'][0]])
	_rookie_village_members = spawns.generate_group('loner',
	                                                amount=random.randint(7, 9),
	                                                group_motive='survival',
	                                                spawn_chunks=_spawn_chunks)
	
	for member in _rookie_village_members:
		alife.planner.remove_goal(member, 'discover')
	
	_dirt_road_start_chunk = maps.get_chunk(WORLD_INFO['refs']['dirt_road'][0])
	_dirt_road_end_chunk =  maps.get_chunk(WORLD_INFO['refs']['dirt_road'][len(WORLD_INFO['refs']['dirt_road'])-1])
	
	for x in range(0, MAP_SIZE[0], WORLD_INFO['chunk_size']):
		for y in range(_dirt_road_end_chunk['pos'][1], _dirt_road_start_chunk['pos'][1], WORLD_INFO['chunk_size']):
			if x < _dirt_road_end_chunk['pos'][0]-(10*WORLD_INFO['chunk_size']) or x > _dirt_road_end_chunk['pos'][0]+(10*WORLD_INFO['chunk_size']):
				continue
			
			if random.randint(0, 125):
				continue
			
			_spawn_chunk = '%s,%s' % (x, y)
	
			for _alife in spawns.generate_group('feral dog', amount=random.randint(4, 6), spawn_chunks=[_spawn_chunk]):
				life.memory(_alife, 'focus_on_chunk', chunk_key=_spawn_chunk)

def generate_outpost(outpost_chunks):
	spawns.generate_group('soldier', amount=5, group_motive='military', spawn_chunks=outpost_chunks)