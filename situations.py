from globals import *

import alife

import random

def create_heli_crash(kind):
	while 1:
		chunk_key = random.choice(CHUNK_MAP)
		
		_walkable = alife.chunks.get_walkable_areas(chunk_key)
		if not _walkable:
			continue
		
		s