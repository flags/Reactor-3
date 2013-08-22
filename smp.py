from multiprocessing import Pool
from globals import *

import alife
import life

import time

def init():
	SETTINGS['smp'] = Pool(processes=4)

def test(life, key=None):
	return (life, key)

def process(callback, life, **kwargs):
	return [life, callback(life, **kwargs)]

def fast_scan_surroundings(center_chunk_key, vision):
	#alife.sight.scan_surroundings(life, judge=False, get_chunks=True)
	alife.sight._scan_surroundings(center_chunk_key, 4, vision)
		
def scan_all_surroundings():
	_center_chunks = [life.get_current_chunk_id(l) for l in LIFE.values()]
	_chunk_size = [WORLD_INFO['chunk_size'] for l in range(len(LIFE))]
	_vision = [alife.sight.get_vision(l) for l in LIFE.values()]
	SETTINGS['smp'].map(fast_scan_surroundings, _center_chunks, _vision)
	SETTINGS['smp'].join()