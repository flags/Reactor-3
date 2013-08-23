from multiprocessing import Pool, freeze_support
from globals import *

import alife
import life as lfe

import time

def init():
	SETTINGS['smp'] = Pool(processes=None)
	freeze_support()

def test(life, key=None):
	return (life, key)

def process(callback, life, **kwargs):
	return [life, callback(life, **kwargs)]

def _fast_scan_return(ret):
	alife.brain.flag(LIFE[ret[0]], 'nearby_chunks', value=ret[1])

def fast_scan_surroundings(life_id, center_chunk_key, chunk_size, vision):
	#alife.sight.scan_surroundings(life, judge=False, get_chunks=True)
	return [life_id, alife.sight._scan_surroundings(center_chunk_key, chunk_size, vision)]
		
def scan_all_surroundings():
	_workers = []
	
	for life in LIFE.values():
		_workers.append(SETTINGS['smp'].apply_async(fast_scan_surroundings,
			                                 args=(life['id'],
		                                            lfe.get_current_chunk_id(life),
			                                       WORLD_INFO['chunk_size'],
			                                       alife.sight.get_vision(life),),
		                                      callback=_fast_scan_return))
	
	while _workers:
		_rem = []
		for result in _workers:
			if result.ready():
				_rem.append(result)
		
		for r in _rem:
			_workers.remove(r)
	
	
	