from multiprocessing import Pool
from globals import *

import alife
import life as lfe

import time

def init():
	SETTINGS['smp'] = Pool(processes=4)

def test(life, key=None):
	return (life, key)

def process(callback, life, **kwargs):
	return [life, callback(life, **kwargs)]

def _fast_scan_return(ret):
	print 'ret', ret

def fast_scan_surroundings(center_chunk_key, chunk_size, vision):
	#alife.sight.scan_surroundings(life, judge=False, get_chunks=True)
	return alife.sight._scan_surroundings(center_chunk_key, chunk_size, vision)
		
def scan_all_surroundings():
	_results = []
	for life in LIFE.values():
		_results.append(SETTINGS['smp'].apply_async(fast_scan_surroundings,
			                                 args=(lfe.get_current_chunk_id(life),
			                                       WORLD_INFO['chunk_size'],
			                                       alife.sight.get_vision(life),),
		                                      callback=_fast_scan_return))
	
	while _results:
		_rem = []
		for result in _results:
			if result.ready():
				_rem.append(result)
		
		for r in _rem:
			_results.remove(r)
	
	
	