from globals import *

import threading
import logic
import items
import tiles
import life
import maps
import time

RECRUIT_ITEMS = ['sneakers']

class Runner(threading.Thread):
	def __init__(self, function, source_map, amount):
		self.function = function
		self.source_map = source_map
		self.amount = amount
		self.running = True
		
		threading.Thread.__init__(self)
	
	def run(self):
		self.function(self.source_map, amount=self.amount)
		self.running = False


def generate_world(source_map, life=1, simulate_ticks=1000):
	console_print(0, 0, 0, 'Generating initial life...')
	console_flush()
	
	generate_life(source_map, amount=life)
	
	_r = Runner(simulate_life, source_map, amount=simulate_ticks)
	_r.start()
	
	while _r.running:
		console_print(0, 0, 1, 'Simulating world: %s' % WORLD_INFO['ticks'])
		console_flush()
	
	create_player(source_map)

def generate_life(source_map, amount=1):
	for i in range(amount):
		alife = life.create_life('Human',name=['test', str(i)],map=source_map,position=[50,50-(i*10),2])
		
		for item in RECRUIT_ITEMS:
			life.add_item_to_inventory(alife, items.create_item(item))

def simulate_life(source_map, amount=1000):
	sys_set_fps(9999)

	for i in range(amount):
		logic.tick_all_objects(source_map)

	sys_set_fps(FPS)

def create_player(source_map):
	PLAYER = life.create_life('Human',
		name=['Tester','Toaster'],
		map=source_map,
		position=[25,40,2])
	PLAYER['player'] = True
	
	life.add_item_to_inventory(PLAYER, items.create_item('sneakers'))

	SETTINGS['controlling'] = PLAYER
	SETTINGS['following'] = PLAYER

def generate_structure_map(source_map):
	_buildings = []
	_all_walls = []
	
	#TODO: z-levels
	for x in range(MAP_SIZE[0]):
		for y in range(MAP_SIZE[1]):
			z = 2
			
			if not source_map[x][y][z] and not source_map[x][y][z+1]:
				continue
			
			if (x,y,z+1) in _all_walls:
				continue
			
			_walls = []
			_open_walls = [(x,y,z+1)]
			while _open_walls:
				_wall_x,_wall_y,_wall_z = _open_walls.pop(0)
				
				for x_mod in range(-1,2):
					for y_mod in range(-1,2):
						if (x_mod,y_mod) == (0,0):
							continue
						
						_x = _wall_x+x_mod
						_y = _wall_y+y_mod
						
						if (_x,_y,z+1) in _all_walls:
							continue
						
						if _x>=MAP_SIZE[0] or _y>=MAP_SIZE[1]:
							continue
						
						if not source_map[_x][_y][z+1]:
							continue
						
						_walls.append((_x,_y,z+1))
						_open_walls.append((_x,_y,z+1))
						#_all_walls.append((_x,_y,z+1))
			
			_all_walls.extend(_walls)
			_buildings.append(_walls)
	
	return _buildings
