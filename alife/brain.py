from globals import *

import life as lfe

import alife_group
import alife_needs
import alife_work
import alife_talk

import snapshots
import judgement
import survival
import movement
import factions
import planner
import numbers
import memory
import speech
import combat
import stats
import logic
import sight
import sound

import logging
import time
import copy

CONSTANT_MODULES = [alife_needs,
                    alife_group,
                    alife_talk,
                    alife_work]


def parse(life):
	sight.look(life)
	sound.listen(life)
	memory.process(life)
	judgement.judge(life)
	judgement.judge_jobs(life)
	survival.process(life)

def act(life):
	understand(life)
	
	if lfe.ticker(life, 'update_camps', UPDATE_CAMP_RATE):
		judgement.update_camps(life)

def store_in_memory(life, key, value):
	life['tempstor2'][key] = value

def retrieve_from_memory(life, key):
	if key in life['tempstor2']:
		return life['tempstor2'][key]
	
	return False

def flag(life, flag, value=True):
	life['flags'][flag] = value

def unflag(life, flag):
	life['flags'][flag] = False

def get_flag(life, flag):
	if not flag in life['flags']:
		return False
	
	return life['flags'][flag]

def alife_has_flag(life, target_id, flag):
	if flag in life['know'][target_id]['flags']:
		return True
	
	return False

def flag_alife(life, target_id, flag, value=True):
	#logging.debug('%s flagged %s: %s' % (' '.join(life['name']), ' '.join(LIFE[target_id]['name']), flag))
	
	life['know'][target_id]['flags'][flag] = value

def unflag_alife(life, target_id, flag):
	#logging.debug('%s unflagged %s: %s' % (' '.join(life['name']), ' '.join(LIFE[target_id]['name']), flag))
	
	del life['know'][target_id]['flags'][flag] 

def alife_has_flag(life, target_id, flag):
	if flag in life['know'][target_id]['flags']:
		return True
	
	return False

def get_alife_flag(life, target_id, flag):
	if not flag in life['know'][target_id]['flags']:
		return False
	
	return life['know'][target_id]['flags'][flag]

def flag_item(life, item, flag, value=True):
	if not item['uid'] in life['know_items']:
		remember_item(life, item)
	
	if not flag in life['know_items'][item['uid']]['flags']:
		print life['know_items'][item['uid']]
		life['know_items'][item['uid']]['flags'][flag] = value
		logging.debug('%s flagged item %s with %s' % (' '.join(life['name']),item['uid'],flag))
		
		return True
	
	return False

def get_item_flag(life, item, flag):
	if flag in life['know_items'][item['uid']]['flags']:
		return life['know_items'][item['uid']]['flags'][flag]
	
	return False

def remember_item(life, item):
	#logging.debug('%s learned about %s (%s)' % (' '.join(life['name']), item['name'], item['uid']))
	
	#TODO: Doing too much here. Try to get rid of this check.
	if not item['uid'] in life['know_items']:
		life['know_items'][item['uid']] = {'item': item['uid'],
			'score': judgement.judge_item(life, item['uid'], initial=True),
			'last_seen_at': item['pos'][:],
			'last_seen_time': 0,
			'last_owned_by': item['owner'],
			'shared_with': [],
			'lost': False,
			'flags': {}}
		
		if item['type'] in life['known_items_type_cache']:
			life['known_items_type_cache'][item['type']].append(item['uid'])
		else:
			life['known_items_type_cache'][item['type']] = [item['uid']]
		
		return True
	
	return True

def remembers_item(life, item):
	if item['uid'] in life['know_items']:
		return life['know_items'][item['uid']]
	
	return False

def update_item_secondhand(life, item_memory):
	if item_memory['item'] in life['know_items']:
		life['know_items'][item_memory['item']].update(copy.deepcopy(item_memory))
	else:
		life['know_items'][item_memory['item']] = copy.deepcopy(item_memory)
	
	logging.debug('%s updated item secondhand: %s' % (' '.join(life['name']), ITEMS[item_memory['item']]['name']))

def offload_remembered_item(life, item_uid):
	_item_memory = get_remembered_item(life, item_uid)
	
	_item_memory['offloaded'] = WORLD_INFO['ticks']

def knows_alife(life, alife):
	if life['id'] == alife['id']:
		raise Exception('Life asking about itself (via dict). Stopping.')
	
	if alife['id'] in life['know']:
		return life['know'][alife['id']]
	
	return False

def knows_alife_by_id(life, alife_id):
	if isinstance(alife_id, dict):
		if life['id'] == alife_id['id']:
			raise Exception('Life asking about itself (via ID). Stopping.')
		
		raise Exception('Not a valid ID.')
	
	if life['id'] == alife_id:
		raise Exception('Life asking about itself (via ID). Stopping.')
	
	if alife_id in life['know']:
		return life['know'][alife_id]
	
	return False

def meet_alife(life, target):
	if life['id'] == target['id']:
		raise Exception('Life \'%s\' learned about itself. Stopping.' % ' '.join(life['name']))
	
	if target['id'] in life['know']:
		return life['know'][target['id']]
	
	life['know'][target['id']] = {'life': target,
		'danger': 0,
		'trust': 0,
		'alignment': 'neutral',
		'last_seen_time': -1,
		'time_visible': 0,
		'met_at_time': WORLD_INFO['ticks'],
		'last_seen_at': None,
		'last_encounter_time': 0,
		'items': [],
		'escaped': False,
		'asleep': False,
		'state': None,
		'state_tier': None,
		'group': None,
		'dead': False,
		'snapshot': {},
		'sent': {},
		'questions': [],
		'orders': {},
		'orderid': 1,
		'flags': {}}
	
	if factions.is_enemy(life, target['id']):
		stats.establish_hostile(life, target['id'])
	else:
		stats.establish_trust(life, target['id'])
	
	#logging.debug('%s met %s.' % (' '.join(life['name']), ' '.join(target['name'])) )
	return life['know'][target['id']]

def update_known_life(life, life_id, flag, value):
	_knows = knows_alife_by_id(life, life_id)
	_knows[flag] = value
	
	if 'player' in life:
		if flag == 'last_seen_at':
			logic.show_event('<Updated location of %s>' % (' '.join(LIFE[life_id]['name'])), pos=value, delay=2)
	
	logging.debug('%s updated location of %s: %s' % (' '.join(life['name']), ' '.join(LIFE[life_id]['name']), value))

def has_met_in_person(life, target):
	if knows_alife(life, target)['met_at_time'] == -1:
		return False
	
	return True

def get_remembered_item(life, item_id):
	return life['know_items'][item_id]

def get_matching_remembered_items(life, matches, no_owner=False, active=True, only_visible=False):
	_matched_items = []
	
	if 'type' in matches and matches['type'] in life['known_items_type_cache']:
		_remembered_items = [life['know_items'][i] for i in life['known_items_type_cache'][matches['type']]]
	else:
		_remembered_items = life['know_items'].values()
	
	for item in _remembered_items:
		_item = ITEMS[item['item']]
		
		if get_item_flag(life, _item, 'ignore'):
			continue
		
		if active and 'offloaded' in item:
			continue
		
		if no_owner and item['last_owned_by']:
			continue
				
		if only_visible and not sight.can_see_position(life, _item['pos']):
			continue
		
		if _item['lock']:
			continue
		
		if 'parent' in _item and _item['parent']:
			continue
		
		if logic.matches(_item, matches):
			_matched_items.append(item['item'])
	
	return _matched_items

def get_multi_matching_remembered_items(life, matches, no_owner=False, active=True, only_visible=False):
	_matched_items = []
	
	for match in matches:
		_matched_items.extend(get_matching_remembered_items(life, match, no_owner=no_owner, active=active, only_visible=only_visible))
	
	return _matched_items

def has_remembered_item(life, item_id):
	if item_id in life['know_items']:
		return True
	
	return False

def has_shared_item_with(life, target, item_id):
	if target['id'] in life['know_items'][item_id]['shared_with']:
		return True
	
	return False

def share_item_with(life, target, item_id):
	life['know_items'][item_id]['shared_with'].append(target['id'])

	#logging.debug('%s shared item #%s (%s) with %s.' % (' '.join(life['name']), item['uid'], item['name'], ' '.join(target['name'])))

def remember_known_item(life, item_id):
	if item_id in life['know_items']:
		return life['know_items'][item_id]
	
	return False

def understand(life):
	if SETTINGS['controlling']:
		_dist_to_player = numbers.distance(life['pos'], LIFE[SETTINGS['controlling']]['pos'])
		if _dist_to_player < 100:
			if life['think_rate_max']>=30:
				if _dist_to_player < 75:
					life['think_rate_max'] = 1
					life['online'] = True
					logging.debug('[Agent] %s brought online (Reason: Near viewer)' % ' '.join(life['name']))
				
			else:
				life['think_rate_max'] = 1
		else:
			if _dist_to_player >= OFFLINE_ALIFE_DISTANCE and life['online']:
				life['online'] = False
				logging.debug('[Agent] %s went offline (Reason: Away from viewer)' % ' '.join(life['name']))
			elif life['think_rate_max']<30:
				if _dist_to_player < OFFLINE_ALIFE_DISTANCE:
					life['online'] = True
				
				logging.debug('[Agent] %s went passive (Reason: Away from viewer)' % ' '.join(life['name']))
			
			life['think_rate_max'] = numbers.clip(15*(((_dist_to_player-100)+30)/30), 30, 60)
	else:
		life['think_rate_max'] = 5
	
	if not life['online'] or life['asleep']:
		return False
	
	if len(life['actions'])-len(lfe.find_action(life, matches=[{'action': 'move'}, {'action': 'dijkstra_move'}]))>0:
		lfe.clear_actions(life)
		life['path'] = []
		
		return False
	
	if life['think_rate']>0:
		life['think_rate'] -= 1
		
		return False
	
	for module in CONSTANT_MODULES:
		module.setup(life)
	
	life['think_rate'] = life['think_rate_max']
	
	#if life['name'][0].startswith('Tim'):
	#	_goal, _tier, _plan = planner.get_next_goal(life, debug='attack')
	#else:
	_goal, _tier, _plan = planner.get_next_goal(life)
	
	if _goal:
		lfe.change_goal(life, _goal, _tier, _plan)
	else:
		lfe.change_goal(life, 'idle', TIER_RELAXED, [])
		#logging.error('%s has no possible goal.' % ' '.join(life['name']))
		
		return False
	
	planner.think(life)
	