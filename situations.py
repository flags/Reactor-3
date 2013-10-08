from globals import *

import graphics as gfx
import life as lfe

import effects
import alife
import items

import random

def create_heli_crash(kind):
	while 1:
		chunk_key = random.choice(WORLD_INFO['chunk_map'])
		
		_walkable = alife.chunks.get_walkable_areas(chunk_key)
		if not _walkable:
			continue
		
def drop_cache(item_names):
	while 1:
		_chunk_key = random.choice(WORLD_INFO['chunk_map'].keys())
		_chunk = alife.chunks.get_chunk(_chunk_key)
		
		if _chunk['type'] == 'other':
			break
	
	for item in item_names:
		_pos = random.choice(_chunk['ground'])
		_item = ITEMS[items.create_item(item, position=[_pos[0], _pos[1], 2])]
		
		for life in LIFE.values():
			lfe.memory(life, 'cache_drop', chunk_key=_chunk_key)
			#alife.survival.add_needed_item(life,
			#                               {'pos': _item['pos'][:]},
			#                               satisfy_if=alife.action.make_small_script(function='always'),
			#                               satisfy_callback=alife.action.make_small_script(function='consume'))
			#alife.brain.remember_item(life, _item)
	
	gfx.message('You see something parachuting to the ground.')
	print _chunk['pos']