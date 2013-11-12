from globals import *

import life as lfe

import alife_manage_targets
import alife_manage_items
import alife_visit_camp
import alife_find_camp
import alife_surrender
import alife_discover
import alife_explore
import alife_shelter
import alife_search
import alife_hidden
import alife_combat
import alife_follow
import alife_guard
import alife_cover
import alife_group
import alife_needs
import alife_camp
import alife_talk
import alife_work
import alife_hide
import snapshots
import judgement
import survival
import movement
import memory
import speech
import combat
import logic
import sight
import sound

import logging
import time
import copy

MODULES = [alife_hide,
	alife_hidden,
	alife_talk,
	alife_discover,
	alife_manage_items,
	alife_manage_targets,
	alife_combat,
	alife_work,
	alife_needs,
	alife_group,
	alife_shelter,
	alife_search,
	alife_surrender,
	alife_cover,
	alife_follow,
	alife_guard]

def sort_modules(life):
	global MODULES
	
	_scores = {}
	
	for module in MODULES:
		try:
			_module_tier = module.get_tier(life)
		except AttributeError:
			_module_tier = module.TIER
		
		if _module_tier in _scores:
			_scores[_module_tier].append(module)
		else:
			_scores[_module_tier] = [module]
	
	return _scores

def think(life):
	sight.look(life)
	sound.listen(life)
	memory.process(life)
	judgement.judge(life)
	judgement.judge_jobs(life)
	survival.process(life)
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
	logging.debug('%s flagged %s: %s' % (' '.join(life['name']), ' '.join(LIFE[target_id]['name']), flag))
	life['know'][target_id]['flags'][flag] = value

def unflag_alife(life, target_id, flag):
	logging.debug('%s unflagged %s: %s' % (' '.join(life['name']), ' '.join(LIFE[target_id]['name']), flag))
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
			'score': judgement.judge_item(life, item['uid']),
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

def offload_remembered_item(life, item_uid):
	_item_memory = get_remembered_item(life, item_uid)
	
	_item_memory['offloaded'] = WORLD_INFO['ticks']

def add_impression(life, target_id, gist, modifiers):
	life['know'][target_id]['impressions'][gist] = {'modifiers': modifiers, 'happened_at': WORLD_INFO['ticks']}
	
	lfe.create_and_update_self_snapshot(LIFE[target_id])
	
	logging.debug('%s got impression of %s: %s (%s)' % (' '.join(life['name']), ' '.join(LIFE[target_id]['name']), gist, modifiers))

def get_impression(life, target_id, gist):
	if gist in life['know'][target_id]['impressions']:
		return life['know'][target_id]['impressions'][gist]
	
	return None

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
		
		print alife_id['name']
		print alife_id.keys()
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
		return False
	
	life['know'][target['id']] = {'life': target,
		'fondness': 0,
		'danger': 0,
		'trust': 0,
		'alignment': 'neutral',
		'last_seen_time': -1,
		'met_at_time': WORLD_INFO['ticks'],
		'last_seen_at': target['pos'][:],
		'last_encounter_time': 0,
		'escaped': False,
		'asleep': False,
		'state': target['state'],
		'group': target['group'],
		'dead': False,
		'snapshot': {},
		'sent': [],
		'received': [],
		'impressions': {},
		'questions': [],
		'orders': {},
		'orderid': 1,
		'flags': {}}
	
	#logging.debug('%s met %s.' % (' '.join(life['name']), ' '.join(target['name'])) )

def update_known_life(life, life_id, flag, value):
	_knows = knows_alife_by_id(life, life_id)
	
	_knows[flag] = value

def has_met_in_person(life, target):
	if knows_alife(life, target)['met_at_time'] == -1:
		return False
	
	return True

def get_remembered_item(life, item_id):
	return life['know_items'][item_id]

def get_matching_remembered_items(life, matches, no_owner=False, active=True):
	_matched_items = []
	
	if 'type' in matches and matches['type'] in life['known_items_type_cache']:
		_remembered_items = [life['know_items'][i] for i in life['known_items_type_cache'][matches['type']]]
	else:
		_remembered_items = life['know_items'].values()
	
	for item in _remembered_items:
		if get_item_flag(life, ITEMS[item['item']], 'ignore'):
			continue
		
		if active and 'offloaded' in item:
			continue
		
		if no_owner and item['last_owned_by']:
			continue
		
		if logic.matches(ITEMS[item['item']], matches):
			_matched_items.append(item['item'])
	
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
	_modules = sort_modules(life)
	
	if '_last_module' in life and not life['_last_module'] == _modules.keys()[0]:
		life['think_rate'] = 0
	elif life['state_tier'] <= TIER_COMBAT and life['think_rate_max'] == LIFE_THINK_RATE:
		if life['think_rate'] > 2:
			life['think_rate'] = 2
		
		life['think_rate_max'] = 2
	elif life['state'] in ['discovering', 'following']:
		life['think_rate_max'] = 6
	elif life['state'] == 'idle':
		life['think_rate_max'] = 30
	else:
		life['think_rate_max'] = LIFE_THINK_RATE
	
	life['_last_module'] = _modules.keys()[0]
	
	if life['think_rate']:
		life['think_rate'] -= 1
		return False
	
	life['think_rate'] = life['think_rate_max']
	
	_visible_alife = [knows_alife_by_id(life, t) for t in life['seen']] #Targets we can see
	_non_visible_alife = [knows_alife_by_id(life, k) for k in life['know'] if not k in life['seen']] #Targets we can't see but still might be relevant
	_visible_threats = []#[knows_alife_by_id(life, t) for t in judgement.get_visible_threats(life)]
	_non_visible_threats = []#[knows_alife_by_id(life, t) for t in judgement.get_invisible_threats(life)]
	
	for target in _visible_alife:		
		if snapshots.process_snapshot(life, target['life']):
			judgement.judge_life(life, target['life']['id'])
	
	for module in MODULES:	
		try:		
			module.setup(life)
		except:
			continue
	
	#_stime = time.time()
	_passive_only = False
	_modules_run = False
	#_times = []
	
	_sorted_modules = _modules.keys()
	_sorted_modules.sort()
	
	while _modules:
		_score_tier = _sorted_modules[0]
		module = _modules[_score_tier].pop(0)
		
		try:
			_module_tier = module.get_tier(life)
		except AttributeError:
			_module_tier = module.TIER
		
		if (_module_tier <= life['state_tier'] and not _passive_only) or _module_tier == TIER_PASSIVE:
			_return = module.conditions(life, _visible_alife, _non_visible_alife, _visible_threats, _non_visible_threats, [])
			
			if _return == STATE_CHANGE:
				lfe.change_state(life, module.STATE, _module_tier)
			
			if _return:
				module.tick(life, _visible_alife, _non_visible_alife, _visible_threats, _non_visible_threats, [])
				
				if _return == RETURN_SKIP:
					if not _modules[_score_tier]:
						del _modules[_score_tier]
					continue
				
				_modules_run = True
				if not _module_tier == TIER_PASSIVE:
					_passive_only = True
		
		#_times.append({'time': time.time()-_stime, 'module': module.STATE})
		
		if not _modules[_score_tier]:
			del _modules[_score_tier]
			_sorted_modules.remove(_score_tier)
	
	if not _modules_run:
		lfe.change_state(life, 'idle', TIER_IDLE)
	
	#print life['name'], time.time()-_stime
	