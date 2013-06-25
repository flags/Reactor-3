from globals import *

import life as lfe

import alife_manage_targets
import alife_manage_items
import alife_manage_camp
import alife_visit_camp
import alife_find_camp
import alife_discover
import alife_explore
import alife_hidden
import alife_combat
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
import sight
import sound

import logging
import time
import copy

MODULES = [alife_hide,
	alife_hidden,
	alife_talk,
	alife_explore,
	alife_discover,
	alife_find_camp,
	alife_visit_camp,
	alife_camp,
	alife_manage_items,
	alife_manage_camp,
	alife_manage_targets,
	alife_combat,
	alife_work,
	alife_needs,
	alife_group]

def think(life, source_map):
	sight.look(life)
	sound.listen(life)
	memory.process(life)
	understand(life, source_map)

def store_in_memory(life, key, value):
	life['tempstor2'][key] = value

def retrieve_from_memory(life, key):
	if key in life['tempstor2']:
		return life['tempstor2'][key]
	
	return None

def flag(life, flag, value=True):
	life['flags'][flag] = value

def unflag(life, flag):
	life['flags'][flag] = False

def get_flag(life, flag):
	if not flag in life['flags']:
		return False
	
	return life['flags'][flag]

def flag_alife(life, target, flag, value=True):
	life['know'][target['id']]['flags'][flag] = value

def unflag_alife(life, target, flag):
	del life['know'][target['id']]['flags'][flag] 

def get_alife_flag(life, target, flag):
	if not flag in life['know'][target['id']]['flags']:
		return False
	
	return life['know'][target['id']]['flags'][flag]

def flag_item(life, item, flag, value=True):
	if not item['uid'] in life['know_items']:
		remember_item(life, item)
	
	if not flag in life['know_items'][item['uid']]['flags']:
		life['know_items'][item['uid']]['flags'][flag] = value
		logging.debug('%s flagged item %s with %s' % (' '.join(life['name']),item['uid'],flag))
		
		return True
	
	return False

def get_item_flag(life, item, flag):
	if flag in life['know_items'][item['uid']]['flags']:
		return life['know_items'][item['uid']]['flags'][flag]
	
	return False

def remember_item(life, item):
	#TODO: Doing too much here. Try to get rid of this check.
	if not item['uid'] in life['know_items']:
		life['know_items'][item['uid']] = {'item': item,
			'score': judgement.judge_item(life,item),
			'last_seen_at': item['pos'][:],
			'last_seen_time': 0,
			'shared_with': [],
			'flags': {}}
		
		return True
	
	return False

def remember_item_secondhand(life, target, item_memory):
	_item = item_memory.copy()
	_item['flags'] = []
	_item['from'] = target['id']

	life['know_items'][_item['item']['uid']] = _item

	#logging.debug('%s gained secondhand knowledge of item #%s from %s.' % (' '.join(life['name']), _item['item']['uid'], ' '.join(target['name'])))

def add_impression(life, target_id, gist, modifiers):
	life['know'][target_id]['impressions'][gist] = {'modifiers': modifiers, 'happened_at': WORLD_INFO['ticks']}
	
	lfe.create_and_update_self_snapshot(LIFE[target_id])
	
	logging.debug('%s got impression of %s: %s (%s)' % (' '.join(life['name']), ' '.join(LIFE[target_id]['name']), gist, modifiers))

def get_impression(life, target_id, gist):
	if gist in life['know'][target_id]['impressions']:
		return life['know'][target_id]['impressions'][gist]
	
	return None

def knows_alife(life, alife):
	if alife['id'] in life['know']:
		return life['know'][alife['id']]
	
	return False

def knows_alife_by_id(life, alife_id):
	if not isinstance(alife_id, int):
		print alife_id.keys()
		raise Exception('Not a valid ID.')
	
	if alife_id in life['know']:
		return life['know'][alife_id]
	
	return False

def meet_alife(life, target):
	life['know'][target['id']] = {'life': target,
		'fondness': 0,
	    'danger': 0,
		'trust': 0,
		'likes': copy.deepcopy(target['likes']),
		'last_seen_time': 0,
		'met_at_time': WORLD_INFO['ticks'],
		'last_seen_at': target['pos'][:],
		'last_encounter_time': -1000,
		'escaped': False,
		'snapshot': {},
		'sent': [],
		'received': [],
		'impressions': {},
		'flags': {}}
	
	#logging.debug('%s met %s.' % (' '.join(life['name']), ' '.join(target['name'])) )

def has_met_in_person(life, target):
	if get_remembered_alife(life, target)['met_at_time'] == -1:
		return False
	
	return True

def get_remembered_alife(life, target):
	return life['know'][target['id']]

def get_remembered_item(life, item):
	return life['know_items'][item['uid']]

def get_matching_remembered_items(life, matches):
	_matched_items = []
	for item in [i['item'] for i in life['know_items'].values()]:
		if logic.matches(item, matches):
			_matched_items.append(item['uid'])
	
	return _matched_items

def has_remembered_item(life, item):
	if item['uid'] in life['know_items']:
		return True
	
	return False

def has_shared_item_with(life, target, item):
	if target['id'] in life['know_items'][item['uid']]['shared_with']:
		return True
	
	return False

def share_item_with(life, target, item):
	life['know_items'][item['uid']]['shared_with'].append(target['id'])

	logging.debug('%s shared item #%s (%s) with %s.' % (' '.join(life['name']), item['uid'], item['name'], ' '.join(target['name'])))

def remember_known_item(life, item_uid):
	if item_uid in life['know_items']:
		return life['know_items'][item_uid]
	
	return False

def generate_needs(life):
	#TODO: We don't generate all of our needs here, so this is a bit misleading
	#Needs can be created anywhere in the ALife loop just so long as you do it early/before brain.think()
	
	if 'USES_FIREARMS' in life:
		if combat.has_weapon(life):
			unflag(life, 'no_weapon')
		else:
			flag(life, 'no_weapon')

def understand(life, source_map):
	if life['think_rate']:
		life['think_rate'] -= 1
		return False
	
	life['think_rate'] = life['think_rate_max']
	
	_visible_alife = [knows_alife_by_id(life, t) for t in life['seen']] #Targets we can see
	_non_visible_alife = [knows_alife_by_id(life, k) for k in life['know'] if not k in life['seen']] #Targets we can't see but still might be relevant
	_visible_threats = [knows_alife_by_id(life, t) for t in judgement.get_visible_threats(life)]
	_non_visible_threats = [knows_alife_by_id(life, t) for t in judgement.get_invisible_threats(life)]
	
	for target in _visible_alife:		
		if snapshots.process_snapshot(life, target['life']):
			judgement.judge(life, target['life']['id'])
	
	generate_needs(life)
	
	for module in MODULES:	
		try:		
			module.setup(life)
		except:
			continue
	
	_modules_run = False
	_times = []
	for module in MODULES:
		_stime = time.time()
		_return = module.conditions(life, _visible_alife, _non_visible_alife, _visible_threats, _non_visible_threats, source_map)
		
		if _return == STATE_CHANGE:
			lfe.change_state(life, module.STATE)
		
		if _return:
			module.tick(life, _visible_alife, _non_visible_alife, _visible_threats, _non_visible_threats, source_map)
			
			if _return == RETURN_SKIP:
				continue
			
			_modules_run = True
		
		_times.append({'time': time.time()-_stime, 'module': module.STATE})
	
	if not _modules_run:
		lfe.change_state(life, 'idle')
	
	#print ' '.join(life['name'])
	#for entry in _times:
	#	print '\t%s: %s' % (entry['module'], entry['time'])
