from globals import *

import graphics as gfx
import life as lfe

import numbers
import bullets
import items

import random

random.seed()

def get_feed(weapon):
	return weapon[weapon['feed']]

def get_fire_mode(weapon):
	"""Returns current fire mode for a weapon."""
	return weapon['firemodes'][weapon['firemode']]

def get_recoil(life):
	weapon = lfe.get_inventory_item(life,lfe.get_held_items(life,matches=[{'type': 'gun'}])[0])
	_recoil = weapon['recoil']
	
	if life['stance'] == 'standing':
		_recoil *= 1
	elif life['stance'] == 'crouching':
		_recoil *= .75
	elif life['stance'] == 'crawling':
		_recoil *= .50
	
	return _recoil

def get_accuracy(life, weapon):
	_accuracy = weapon['accuracy']
	
	if life['stance'] == 'standing':
		_accuracy *= 1.5
	elif life['stance'] == 'crouching':
		_accuracy *= 1.2
	elif life['stance'] == 'crawling':
		_accuracy *= 1
	
	return _accuracy

def fire(life, target, limb=None):
	#TODO: Don't breathe this!
	if 'player' in life:
		weapon = life['firing']
	else:
		_item = lfe.get_held_items(life,matches=[{'type': 'gun'}])[0]
		
		if not _item:
			if 'player' in life:
				gfx.message('You aren\'t holding a weapon!')
			life['facing'] = (_fx,_fy)
			life['firing'] = None
			return False
		
		weapon = lfe.get_inventory_item(life, _item)
	
	_mode = get_fire_mode(weapon)
	if _mode == 'single':
		_bullets = 1
	elif _mode == '3burst':
		_bullets = 3
	
	_ooa = False
	for i in range(_bullets):
		_feed = get_feed(weapon)
		
		if not _feed or (_feed and not _feed['rounds']):
			if 'player' in life:
				gfx.message('*Click*')
			
			_ooa = True
			continue
		
		direction = numbers.direction_to(life['pos'],target)
		_accuracy = int(round(get_accuracy(life, weapon)))
		direction += random.randint(-_accuracy,_accuracy+1)
		
		#TODO: Clean this up...
		_bullet = _feed['rounds'].pop()
		_bullet['pos'] = life['pos'][:]
		_bullet['owner'] = life['id']
		_bullet['aim_at_limb'] = limb
		_bullet['accuracy'] = _accuracy
		del _bullet['parent']
		items.move(_bullet, direction, _bullet['max_speed'])
	
	if _ooa:
		if 'player' in life:
			gfx.message('You are out of ammo.')
	
	_fx = numbers.clip(life['facing'][0]-target[0],-1,1)
	_fy = numbers.clip(life['facing'][1]-target[1],-1,1)
	
	for _life in [LIFE[i] for i in LIFE]:
		if _life['pos'][0] == target[0] and _life['pos'][1] == target[1]:
			life['aim_at'] = _life['id']
			break
	
	life['facing'] = (_fx,_fy)
	life['firing'] = None
