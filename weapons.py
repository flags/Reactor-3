from globals import *

import graphics as gfx
import life as lfe

import numbers
import bullets
import effects
import alife
import items

import random

def get_weapon_to_fire(life):
	if 'player' in life:
		return life['firing']
		
	_item = lfe.get_held_items(life,matches=[{'type': 'gun'}])
		
	if _item:
		_item = _item[0]
	else:
		return False
	
	if not _item:
		if 'player' in life:
			gfx.message('You aren\'t holding a weapon!')
		
		life['firing'] = None
		return False
	
	return lfe.get_inventory_item(life, _item)

def get_feed(weapon):
	return weapon[weapon['feed']]

def get_fire_mode(weapon):
	"""Returns current fire mode for a weapon."""
	return weapon['firemodes'][weapon['firemode']]

def get_rounds_to_fire(weapon):
	_mode = get_fire_mode(weapon)
	
	if _mode == 'single':
		_bullets = 1
	elif _mode == '3burst':
		_bullets = 3
	else:
		logging.error('Unhandled firerate: %s. Handling...' % _mode)
		_bullets = 1
		
	return _bullets

def change_fire_mode(weapon, mode):
	weapon['firemode'] = mode

def get_stance_recoil_mod(life):
	if life['stance'] == 'standing':
		return 1
	elif life['stance'] == 'crouching':
		return .75
	elif life['stance'] == 'crawling':
		return .50

def get_recoil(life):
	_guns = lfe.get_held_items(life,matches=[{'type': 'gun'}])
	
	if not _guns:
		return 0
	
	weapon = lfe.get_inventory_item(life, _guns[0])
	_recoil = weapon['recoil']
	
	_recoil *= get_stance_recoil_mod(life)
	
	return _recoil

def get_accuracy(life, weapon_uid, limb=None):
	weapon = ITEMS[weapon_uid]
	_accuracy = weapon['accuracy']
	_accuracy *= alife.stats.get_firearm_accuracy(life)
	
	if limb:
		_stability = lfe.get_limb_stability(life, limb)
		_accuracy *= _stability
		
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
	
	return _accuracy

def get_bullet_scatter_to(life, position, bullet_uid):
	bullet = ITEMS[bullet_uid]
	
	_travel_distance = numbers.distance(bullet['pos'], position)
	
	if _travel_distance <= 2:
		return 0
	
	return _travel_distance*bullet['scatter_rate']

def fire(life, target, limb=None):
	#TODO: Don't breathe this!
	weapon = get_weapon_to_fire(life)
	
	if not weapon:
		return False
	
	_aim_with_limb = None
	for hand in life['hands']:
		if weapon['uid'] in lfe.get_limb(life, hand)['holding']:
			_aim_with_limb = hand
	
	_ooa = False
	_feed_uid = get_feed(weapon)
	
	if not _feed_uid:
		if 'player' in life:
			gfx.message('The weapon is unloaded.')
		
		_ooa = True
		return False
	
	_feed = items.get_item_from_uid(_feed_uid)
	
	if not _feed or (_feed and not _feed['rounds']):
		if 'player' in life:
			gfx.message('*Click* (You are out of ammo.)')
		
		_ooa = True
		return False
	
	direction = numbers.direction_to(life['pos'],target)+(random.uniform(-life['recoil'], life['recoil']))
	
	alife.noise.create(life['pos'], 120, '%s fire' % weapon['name'], 'something discharge')
	
	#TODO: Clean this up...
	_bullet = items.get_item_from_uid(_feed['rounds'].pop())
	_bullet['pos'] = life['pos'][:]
	_bullet['start_pos'] = life['pos'][:]
	_bullet['owner'] = None
	_bullet['shot_by'] = life['id']
	_bullet['aim_at_limb'] = limb
	
	life['recoil'] += _bullet['recoil']*(weapon['recoil']*get_stance_recoil_mod(life))
	
	items.add_to_chunk(_bullet)
	
	if gfx.position_is_in_frame(life['pos']):
		effects.create_light(life['pos'], tcod.yellow, 7, 1, fade=2.5)
		effects.create_light(_bullet['pos'], tcod.yellow, 7, 1, fade=0.65, follow_item=_bullet['uid'])
	
	_bullet['accuracy'] = int(round(get_accuracy(life, weapon['uid'], limb=_aim_with_limb)))
	del _bullet['parent']
	items.move(_bullet, direction, _bullet['max_speed'])
	_bullet['start_velocity'] = _bullet['velocity'][:]
	items.tick_item(_bullet['uid'])
	
	for _life in [LIFE[i] for i in LIFE]:
		if _life['pos'][0] == target[0] and _life['pos'][1] == target[1]:
			life['aim_at'] = _life['id']
			break
	
	if len(lfe.find_action(life, matches=[{'action': 'shoot'}])) == 1:
		life['firing'] = None
