from globals import *

import threading
import logging
import logic
import items
import tiles
import life
import maps
import time

RECRUIT_ITEMS = ['sneakers', 'glock', '9x19mm magazine', '9x19mm round']

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


def draw_world_stats():	
	console_print(0, 0, 2, 'Simulating world: %s (%.2f t/s)' % (WORLD_INFO['ticks'], WORLD_INFO['ticks']/(time.time()-WORLD_INFO['inittime'])))
	console_print(0, 0, 3, 'Queued ALife actions: %s' % sum([len(alife['actions']) for alife in LIFE]))
	console_print(0, 0, 4, 'Total ALife memories: %s' % sum([len(alife['memory']) for alife in LIFE]))
	console_print(0, 0, 5, '%s %s' % (TICKER[int(WORLD_INFO['ticks'] % len(TICKER))], '=' * (WORLD_INFO['ticks']/50)))
	console_flush()

def generate_world(source_map, life=1, simulate_ticks=1000):
	console_print(0, 0, 0, 'World Generation')
	console_flush()
	
	WORLD_INFO['inittime'] = time.time()
	
	generate_life(source_map, amount=life)
	
	_r = Runner(simulate_life, source_map, amount=simulate_ticks)
	_r.start()
	
	while _r.running:
		draw_world_stats()
	
	create_player(source_map)
	logging.info('World generation complete (took %.2fs)' % (time.time()-WORLD_INFO['inittime']))

def generate_life(source_map, amount=1):
	for i in range(amount):
		alife = life.create_life('Human',name=['test', str(i)],map=source_map,position=[25,50-(i*10),2])
		
		for item in RECRUIT_ITEMS:
			life.add_item_to_inventory(alife, items.create_item(item))

def simulate_life(source_map, amount=1000):
	for i in range(amount):
		logic.tick_all_objects(source_map)

def create_player(source_map):
	PLAYER = life.create_life('Human',
		name=['Tester','Toaster'],
		map=source_map,
		position=[25,40,2])
	PLAYER['player'] = True
	
	life.add_item_to_inventory(PLAYER, items.create_item('sneakers'))

	SETTINGS['controlling'] = PLAYER
	SETTINGS['following'] = PLAYER
