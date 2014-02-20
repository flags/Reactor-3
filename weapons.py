from globals import *

import graphics as gfx
import life as lfe

import numbers
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
		return 1.0
	elif life['stance'] == 'crouching':
		return .70
	elif life['stance'] == 'crawling':
		return .25
	else:
		1.0

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
	_accuracy = 3*weapon['accuracy']
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
	
	_bullet_deviation = (1-weapon['accuracy'])+life['recoil']
	_deviation_mod = SETTINGS['aim_difficulty']*(1-((life['stats']['firearms']/10.0)*SETTINGS['firearms_skill_mod']))
	_direction_deviation = (_bullet_deviation*SETTINGS['aim_difficulty'])*_deviation_mod
	
	life['recoil'] = numbers.clip(life['recoil']+(weapon['recoil']*get_stance_recoil_mod(life)), 0.0, 1.0)
	
	_bullet_direction = numbers.direction_to(life['pos'], target)+(random.uniform(-_direction_deviation, _direction_deviation))
	
	alife.noise.create(life['pos'], 120, '%s fire' % weapon['name'], 'something discharge', target=life['id'])
	
	#TODO: Clean this up...
	_bullet = items.get_item_from_uid(_feed['rounds'].pop())
	_bullet['pos'] = life['pos'][:]
	_bullet['start_pos'] = life['pos'][:]
	_bullet['owner'] = None
	_bullet['shot_by'] = life['id']
	_bullet['aim_at_limb'] = limb
	
	items.add_to_chunk(_bullet)
	
	if gfx.position_is_in_frame(life['pos']) or 'player' in life:
		effects.create_light(life['pos'], tcod.yellow, 7, 1, fade=3.2)
		effects.create_light(_bullet['pos'], tcod.yellow, 7, .9, fade=.65, follow_item=_bullet['uid'])
		effects.create_smoke_cloud(life['pos'], 3, color=tcod.light_gray)
		effects.create_smoke(life['pos'], color=tcod.yellow)
	
	_bullet['accuracy'] = int(round(get_accuracy(life, weapon['uid'], limb=_aim_with_limb)))

	print 'ACCURACY', _bullet['accuracy']
	
	del _bullet['parent']
	items.move(_bullet, _bullet_direction, _bullet['max_speed'])
	_bullet['start_velocity'] = _bullet['velocity'][:]
	items.tick_item(_bullet)
	
	for _life in [LIFE[i] for i in LIFE]:
		if _life['pos'][0] == target[0] and _life['pos'][1] == target[1]:
			life['aim_at'] = _life['id']
			break
	
	if len(lfe.find_action(life, matches=[{'action': 'shoot'}])) == 1:
		life['firing'] = None
