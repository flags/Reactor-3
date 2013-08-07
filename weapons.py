from globals import *

import graphics as gfx
import life as lfe

import numbers
import bullets
import alife
import items

import random

random.seed()

def get_feed(weapon):
	return weapon[weapon['feed']]

def get_fire_mode(weapon):
	"""Returns current fire mode for a weapon."""
	return weapon['firemodes'][weapon['firemode']]

def get_recoil(life):
	_guns = lfe.get_held_items(life,matches=[{'type': 'gun'}])
	
	if not _guns:
		return 0
	
	weapon = lfe.get_inventory_item(life, _guns[0])
	_recoil = weapon['recoil']
	
	if life['stance'] == 'standing':
		_recoil *= 1
	elif life['stance'] == 'crouching':
		_recoil *= .75
	elif life['stance'] == 'crawling':
		_recoil *= .50
	
	return _recoil

def get_max_accuracy(weapon):
	return weapon['accuracy'][0]*weapon['accuracy'][1]

def get_accuracy(life, weapon, limb=None):
	#_accuracy = weapon['accuracy']
	
	_accuracy = get_max_accuracy(weapon)
	_accuracy *= alife.stats.get_firearm_accuracy(life)
	
	if limb:
		_stability = lfe.get_limb_stability(life, limb)
		_accuracy *=  _stability
		
		if 'player' in life:
			if _stability <= 0:
				gfx.message('Your %s is useless.' % limb, style='damage')
				return 0
			elif _stability <= .25:
				gfx.message('Your %s is nearly useless!' % limb, style='damage')
				lfe.add_wound(life, limb, pain=2)
			elif _stability <= .55:
				gfx.message('You feel a sharp pain in your %s!' % limb, style='damage')
				lfe.add_wound(life, limb, pain=1)
			elif _stability <= .75:
				gfx.message('Your %s stings from the recoil.' % limb, style='damage')
	
	if life['stance'] == 'standing':
		_accuracy *= 0.7
	elif life['stance'] == 'crouching':
		_accuracy *= 0.9
	elif life['stance'] == 'crawling':
		_accuracy *= 1
	
	print 'Accuracy', _accuracy
	
	return _accuracy

def get_impact_accuracy(life, bullet):
	#_travel_time = WORLD_INFO['time']-bullet['time_shot']
	_travel_distance = numbers.distance(bullet['start_pos'], bullet['pos'])
	_bullet_sway = _travel_distance*bullet['scatter_rate']
	
	if _travel_distance <= 2:
		return 0
	
	#_accuracy = bullet['needed_accuracy']*alife.stats.get_firearm_accuracy(life)
	_accuracy = _bullet_sway
	
	return _accuracy

def fire(life, target, limb=None):
	#TODO: Don't breathe this!
	if 'player' in life:
		weapon = life['firing']
	else:
		_item = lfe.get_held_items(life,matches=[{'type': 'gun'}])
		
		if _item:
			_item = _item[0]
		else:
			return False
		
		if not _item:
			if 'player' in life:
				gfx.message('You aren\'t holding a weapon!')
			life['facing'] = (_fx,_fy)
			life['firing'] = None
			return False
		
		weapon = lfe.get_inventory_item(life, _item)
	
	if not weapon:
		return False
	
	_mode = get_fire_mode(weapon)
	if _mode == 'single':
		_bullets = 1
	elif _mode == '3burst':
		_bullets = 3
	
	_aim_with_limb = None
	for hand in life['hands']:
		if weapon['uid'] in lfe.get_limb(life, hand)['holding']:
			_aim_with_limb = hand
	
	_ooa = False
	for i in range(_bullets):
		_feed_uid = get_feed(weapon)
		
		if not _feed_uid:
			if 'player' in life:
				gfx.message('The weapon is unloaded.')
			
			_ooa = True
			continue
		
		_feed = items.get_item_from_uid(_feed_uid)
		
		if not _feed or (_feed and not _feed['rounds']):
			if 'player' in life:
				gfx.message('*Click*')
			
			_ooa = True
			continue
		
		direction = numbers.direction_to(life['pos'],target)+(random.uniform(-life['recoil'], life['recoil']))
		life['recoil'] += weapon['recoil']
		
		#TODO: Clean this up...
		_bullet = items.get_item_from_uid(_feed['rounds'].pop())
		_bullet['pos'] = life['pos'][:]
		_bullet['start_pos'] = life['pos'][:]
		_bullet['owner'] = life['id']
		_bullet['aim_at_limb'] = limb
		_bullet['time_shot'] = WORLD_INFO['ticks']
		_bullet['needed_accuracy'] = get_max_accuracy(weapon)
		_bullet['accuracy'] = int(round(get_accuracy(life, weapon, limb=_aim_with_limb)))
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
