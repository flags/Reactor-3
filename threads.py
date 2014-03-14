from globals import MAP_SIZE, MAP_WINDOW_SIZE, WORLD_INFO, SETTINGS, LIFE

import graphics as gfx

import numbers
import maps

import threading
import logging
import time


class ChunkHandler(threading.Thread):
	def __init__(self, check_every=5):
		threading.Thread.__init__(self)
		
		self.last_checked = -check_every
		self.check_every = check_every
	
	def check_chunks(self):
		if WORLD_INFO['ticks']-self.last_checked<self.check_every:
			return False
		
		self.last_checked = WORLD_INFO['ticks']
		
		for life in [l for l in LIFE.values() if l['online']]:
			_x_min = numbers.clip(life['pos'][0]-MAP_WINDOW_SIZE[0], 0, MAP_SIZE[0]-1-MAP_WINDOW_SIZE[0])
			_y_min = numbers.clip(life['pos'][1]-MAP_WINDOW_SIZE[1], 0, MAP_SIZE[1]-1-MAP_WINDOW_SIZE[1])
			_x_max = numbers.clip(life['pos'][0]+MAP_WINDOW_SIZE[0], 0, MAP_SIZE[0]-1)
			_y_max = numbers.clip(life['pos'][1]+MAP_WINDOW_SIZE[1], 0, MAP_SIZE[1]-1)
			_refresh = False
			
			for y in range(_y_min, _y_max, WORLD_INFO['chunk_size']):
				for x in range(_x_min, _x_max, WORLD_INFO['chunk_size']):
					maps.load_cluster_at_position_if_needed((x, y))
					
					SETTINGS['loading'] = True
					
					if 'player' in life:
						_refresh = True
			
			if _refresh:
				gfx.refresh_view('map')
		
		SETTINGS['loading'] = False
	
	def run(self):
		while SETTINGS['running'] and not SETTINGS['kill threads']:
			self.check_chunks()
			time.sleep(1)
		
		logging.debug('ChunkHandler thread shutting down.')

def init():
	SETTINGS['chunk_handler'] = ChunkHandler()
	SETTINGS['chunk_handler'].start()
