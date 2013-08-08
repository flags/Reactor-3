from globals import *

import libtcodpy as tcod
import life as lfe

import historygen
import profiles
import effects
import logic
import items
import tiles
import alife
import life
import maps

import threading
import logging
import random
import time
import json
import sys

BASE_ITEMS = ['sneakers',
              'blue jeans',
              'white t-shirt',
              'leather backpack',
              'radio']
RECRUIT_ITEMS = ['glock', '9x19mm magazine']

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
	tcod.console_print(0, 0, 0, 'World Generation')
	tcod.console_print(0, 0, 2, 'Simulating world: %s (%.2f t/s)' % (WORLD_INFO['ticks'], WORLD_INFO['ticks']/(time.time()-WORLD_INFO['inittime'])))
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

def generate_world(source_map, life_density='Sparse', wildlife_density='Sparse', simulate_ticks=1000, save=True, thread=True):
	WORLD_INFO['inittime'] = time.time()
	WORLD_INFO['start_age'] = simulate_ticks
	
	randomize_item_spawns()
	
	WORLD_INFO['life_density'] = life_density
	WORLD_INFO['wildlife_density'] = wildlife_density
	
	if WORLD_INFO['life_density'] == 'Sparse':
		WORLD_INFO['life_spawn_interval'] = [0, (770, 990)]
	elif WORLD_INFO['life_density'] == 'Medium':
		WORLD_INFO['life_spawn_interval'] = [0, (550, 700)]
	else:
		WORLD_INFO['life_spawn_interval'] = [0, (250, 445)]
	
	if WORLD_INFO['wildlife_density'] == 'Sparse':
		WORLD_INFO['wildlife_spawn_interval'] = [0, (770, 990)]
	elif WORLD_INFO['wildlife_density'] == 'Medium':
		WORLD_INFO['wildlife_spawn_interval'] = [0, (550, 700)]
	else:
		WORLD_INFO['wildlife_spawn_interval'] = [0, (250, 445)]
	
	if thread:
		tcod.console_rect(0,0,0,WINDOW_SIZE[0],WINDOW_SIZE[1],True,flag=tcod.BKGND_DEFAULT)
		_r = Runner(simulate_ticks)
		_r.start()

		while _r.running:
			draw_world_stats()
			
			if not SETTINGS['running']:
				return False
	else:
		print 'here'
		simulate_life(simulate_ticks)
	
	create_player(source_map)
	WORLD_INFO['id'] = 0
	
	if save:
		WORLD_INFO['id'] = profiles.create_world()
		save_world()
	
	logging.info('World generation complete (took %.2fs)' % (time.time()-WORLD_INFO['inittime']))

def load_world(world):
	WORLD_INFO['id'] = world
	maps.load_map('map', base_dir=profiles.get_world(world))

	logging.debug('Loading life from disk...')
	with open(os.path.join(profiles.get_world(WORLD_INFO['id']), 'life.dat'), 'r') as e:
		LIFE.update(json.loads(e.readline()))

	logging.debug('Loading items from disk...')
	with open(os.path.join(profiles.get_world(WORLD_INFO['id']), 'items.dat'), 'r') as e:
		ITEMS.update(json.loads(e.readline()))	
	
	SETTINGS['controlling'] = None
	SETTINGS['following'] = None
	for life in LIFE.values():
		if 'player' in life:
			SETTINGS['controlling'] = life['id']
			SETTINGS['following'] = life['id']
			break
	
	lfe.load_all_life()
	items.reload_all_items()
	
	logging.info('World loaded.')

def save_world():
	logging.debug('Offloading world...')
	maps.save_map('map', base_dir=profiles.get_world(WORLD_INFO['id']))
	
	logging.debug('Saving life...')
	_life = life.save_all_life()
	
	with open(os.path.join(profiles.get_world(WORLD_INFO['id']), 'life.dat'), 'w') as e:
		e.write(_life)
	
	logging.debug('Saving items...')
	items.save_all_items()
	
	with open(os.path.join(profiles.get_world(WORLD_INFO['id']), 'items.dat'), 'w') as e:
		e.write(json.dumps(ITEMS))
	
	items.reload_all_items()
	
	logging.info('World saved.')

def randomize_item_spawns():
	for building in WORLD_INFO['reference_map']['buildings']:
		_chunk_key = random.choice(building)
		_chunk = maps.get_chunk(_chunk_key)
		
		if not _chunk['ground']:
			continue
		
		_rand_pos = random.choice(_chunk['ground'])
		items.create_item(random.choice(RECRUIT_ITEMS), position=[_rand_pos[0], _rand_pos[1], 2])

def get_spawn_point():
	_start_seed = random.randint(0, 3)
	
	if not _start_seed:
		_spawn = (random.randint(0, MAP_SIZE[0]-1), 0)
	elif _start_seed == 1:
		_spawn = (MAP_SIZE[0]-1, random.randint(0, MAP_SIZE[1]-1))
	elif _start_seed == 2:
		_spawn = (random.randint(0, MAP_SIZE[0]-1), MAP_SIZE[1]-1)
	elif _start_seed == 3:
		_spawn = (0, random.randint(0, MAP_SIZE[1]-1))
	
	return _spawn

def generate_wildlife():
	for i in range(1, 3):
		_spawn = get_spawn_point()
		
		_p = life.create_life('dog',
			name=['Wild', 'Dog%s' % i],
			map=WORLD_INFO['map'],
			position=[_spawn[0], _spawn[1], 2])
		
		if random.randint(0, 3)>=2:
			_c = life.create_life('dog',
				name=['(Young) Wild', 'Dog%s' % i],
				map=WORLD_INFO['map'],
				position=[_spawn[0], _spawn[1], 2])
			_c['icon'] = 'd'
			
			alife.brain.meet_alife(_p, _c)
			alife.brain.meet_alife(_c, _p)
			
			alife.brain.flag_alife(_p, _c['id'], 'son')
			alife.brain.flag_alife(_c, _p['id'], 'father')

def generate_life(amount=1):
	_spawn = get_spawn_point()
	
	alife = life.create_life('human', map=WORLD_INFO['map'], position=[_spawn[0], _spawn[1], 2])
	
	for item in BASE_ITEMS:
		life.add_item_to_inventory(alife, items.create_item(item))
	
	for item in RECRUIT_ITEMS:
		if random.randint(0, 1):
			continue
		
		life.add_item_to_inventory(alife, items.create_item(item))

def create_player(source_map):
	PLAYER = life.create_life('human',
		name=['Tester','Toaster'],
		map=source_map,
		position=[10, 10, 2])
	PLAYER['stats'].update(historygen.create_background(life))
	PLAYER['player'] = True
	
	for item in BASE_ITEMS:
		life.add_item_to_inventory(PLAYER, items.create_item(item))
	
	life.add_item_to_inventory(PLAYER, items.create_item('.22 rifle'))
	life.add_item_to_inventory(PLAYER, items.create_item('.22 LR magazine'))
	
	for i in range(10):
		life.add_item_to_inventory(PLAYER, items.create_item('.22 LR cartridge'))
	
	#for item in RECRUIT_ITEMS:
	#	life.add_item_to_inventory(PLAYER, items.create_item(item))

	SETTINGS['controlling'] = PLAYER['id']
	SETTINGS['following'] = PLAYER['id']
	
	_i = items.get_item_from_uid(items.create_item('burner', position=PLAYER['pos'][:]))
	items.move(_i, 180, 3)
	
	#for x in range(-10, 11):
	#	for y in range(-10, 11):
	#		if random.randint(0, 10):
	#			continue
	#		effects.create_fire((PLAYER['pos'][0]+x, PLAYER['pos'][1]+y, PLAYER['pos'][2]), intensity=8)
