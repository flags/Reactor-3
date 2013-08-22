from globals import *

import alife

from multiprocessing import Pool

def test(life, key=None):
	return (life, key)

def process(callback, life, **kwargs):
	return [life, callback(life, **kwargs)]

def fast_scan_surroundings(life_id):
	#for life in LIFE:
	alife.sight.scan_surroundings(LIFE[life_id], judge=False, get_chunks=True)
		
def scan_all_surroundings():
	pool = Pool(processes=4)
	pool.map(fast_scan_surroundings, LIFE.keys())