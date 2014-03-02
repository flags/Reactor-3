from globals import WORLD_INFO, SETTINGS, LIFE, ITEMS

import life as lfe

import numbers
import alife

import logging


def get_player_situation():
	if not SETTINGS['controlling']:
		return False
	
	_life = LIFE[SETTINGS['controlling']]
	
	_situation = {}
	_situation['armed'] = alife.combat.has_potentially_usable_weapon(_life)
	_situation['friends'] = len([l for l in _life['know'].values() if l['alignment'] in ['trust', 'feign_trust']])
	_situation['group'] = _life['group']
	_situation['online_alife'] = [l for l in LIFE.values() if l['online'] and not l['dead'] and not l['id'] == _life['id']]
	_situation['trusted_online_alife'] = [l for l in _situation['online_alife'] if alife.judgement.can_trust(_life, l['id'])]
	_situation['has_radio'] = len(lfe.get_all_inventory_items(_life, matches=[{'type': 'radio'}]))>0
	_situation['weapons'] = alife.combat.get_weapons(_life)
	_situation['equipped_gear'] = lfe.get_all_equipped_items(_life)
	
	return _situation

def get_group_leader_with_motive(group_motive, online=False):
	for life in LIFE.values():
		if not (life['online'] or not online) or not life['group'] or not alife.groups.is_leader(life, life['group'], life['id']) or SETTINGS['controlling'] == life['id']:
			continue
		
		if alife.groups.get_motive(life, life['group']) == group_motive:
			return life['id']
	
	return None

def handle_tracked_alife():
	for ai in [LIFE[i] for i in WORLD_INFO['overwatch']['tracked_alife']]:
		if ai['online']:
			continue
		
		WORLD_INFO['overwatch']['tracked_alife'].remove(ai['id'])
		
		logging.debug('[Overwatch]: Stopped tracking agent: %s' % ' '.join(ai['name']))

def get_overwatch_hardship(no_mod=False):
	_stats = WORLD_INFO['overwatch']
	_situation = get_player_situation()
	
	if not _situation:
		return 0
	
	if no_mod:
		_mod = 1
	else:
		if len(_situation['online_alife']) == len(_situation['trusted_online_alife']):
			_mod = _stats['last_updated']/float(WORLD_INFO['ticks'])
		else:
			_mod = numbers.clip((_stats['last_updated']*1.5)/float(WORLD_INFO['ticks']), 0, 1.0)
			
			#TODO: Decay
			#_stats['loss_experienced'] *= _dec
			#_stats['danger_experienced'] *= _dec
			#_stats['injury'] *= _dec
			#_stats['human_encounters'] *= _dec
	
	_hardship = _stats['loss_experienced']
	_hardship += _stats['danger_experienced']
	_hardship += _stats['injury']
	_hardship += _stats['human_encounters']*4
	_hardship *= _mod
	
	return _hardship

def get_overwatch_success():
	_stats = WORLD_INFO['overwatch']
	_situation = get_player_situation()
	
	if not _situation:
		return 0
	
	#TODO: Check ammo
	_success = len(_situation['weapons'])
	_success += len(_situation['equipped_gear'])
	
	return _success

def evaluate_overwatch_mood():
	_stats = WORLD_INFO['overwatch']
	_hardship = get_overwatch_hardship()
	
	#print _hardship, _mod, _stats['rest_level'], (_stats['last_updated']/float(WORLD_INFO['ticks']))
	
	_success = get_overwatch_success()
	
	#if _stats['mood'] == 'rest':
	#	if _mod > _stats['rest_level']:
	#		return False
	#	
	#	_stats['mood'] = random.choice(['rest', 'hurt'])
	#elif _stats['mood'] == 'hurt':
	if _hardship-_success >= 3.5:
		_stats['mood'] = 'rest'
	elif get_overwatch_hardship(no_mod=True)>=3.5:
		_stats['mood'] = 'intrigue'
	else:
		_stats['mood'] = 'hurt'

def record_encounter(amount, life_ids=None):
	WORLD_INFO['overwatch']['human_encounters'] += amount
	WORLD_INFO['overwatch']['last_updated'] = WORLD_INFO['ticks']
	
	if life_ids:
		WORLD_INFO['overwatch']['tracked_alife'].extend(life_ids)
	
	logging.debug('[Overwatch] encounter (%s)' % amount)

def record_dangerous_event(amount):
	WORLD_INFO['overwatch']['danger_experienced'] += amount
	WORLD_INFO['overwatch']['last_updated'] = WORLD_INFO['ticks']
	
	logging.debug('[Overwatch] Danger (%s)' % amount)

def record_loss(amount):
	WORLD_INFO['overwatch']['loss_experienced'] += amount
	WORLD_INFO['overwatch']['last_updated'] = WORLD_INFO['ticks']
	
	logging.debug('[Overwatch] Loss (%s)' % amount)

def record_injury(amount):
	WORLD_INFO['overwatch']['injury'] += amount
	WORLD_INFO['overwatch']['last_updated'] = WORLD_INFO['ticks']
	
	logging.debug('[Overwatch] injury (%s)' % amount)