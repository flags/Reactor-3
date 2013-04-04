from globals import *

import life as lfe

import alife_collect_items
import alife_manage_items
import alife_find_camp
import alife_discover
import alife_explore
import alife_hidden
import alife_combat
import alife_camp
import alife_talk
import alife_hide
import snapshots
import judgement
import survival
import movement
import speech
import combat
import sight
import sound

import logging
import time

MODULES = [alife_hide,
	alife_hidden,
	alife_collect_items,
	alife_talk,
	alife_explore,
	alife_discover,
	alife_manage_items,
	alife_find_camp,
	alife_camp,
	alife_combat]

def think(life, source_map):
	sight.look(life)
	sound.listen(life)
	understand(life, source_map)

def store_in_memory(life, key, value):
	print life['name']
	for key in life.keys():
		print key
	life['tempstor2'][key] = value

def retrieve_from_memory(life, key):
	if key in life['tempstor2']:
		return life['tempstor2'][key]
	
	return None

def flag(life, flag):
	life['flags'][flag] = True

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

	logging.debug('%s gained secondhand knowledge of item #%s from %s.' % (' '.join(life['name']), _item['item']['uid'], ' '.join(target['name'])))

def add_impression(life, target, gist, score):
	life['know'][target['id']]['impressions'][gist] = {'score': score, 'happened_at': WORLD_INFO['ticks']}
	
	logging.debug('%s got impression of %s: %s (%s)' % (' '.join(life['name']), ' '.join(target['name']), gist, score))

def knows_alife(life, alife):
	if alife['id'] in life['know']:
		return life['know'][alife['id']]
	
	return False

def meet_alife(life, target):
	life['know'][target['id']] = {'life': target,
		'score': 0,
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
	
	logging.debug('%s met %s.' % (' '.join(life['name']), ' '.join(target['name'])) )

def has_met_in_person(life, target):
	if get_remembered_alife(life, target)['met_at_time'] == -1:
		return False
	
	return True

def get_remembered_alife(life, target):
	return life['know'][target['id']]

def get_remembered_item(life, item):
	return life['know_items'][item['uid']]

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

	logging.debug('%s shared item #%s with %s.' % (' '.join(life['name']), item['uid'], ' '.join(target['name'])))

def remember_known_item(life, item_uid):
	if item_uid in life['know_items']:
		return life['know_items'][item_uid]
	
	return False

def generate_needs(life):
	if combat.has_weapon(life):
		unflag(life, 'no_weapon')
	else:
		flag(life, 'no_weapon')
	
	if lfe.get_all_inventory_items(life, matches=[{'type': 'backpack'}]):
		unflag(life, 'no_backpack')
	else:
		flag(life, 'no_backpack')
		

def understand(life,source_map):
	_alife_seen = []
	_alife_not_seen = []
	_targets_seen = []
	_neutral_targets = []
	_targets_not_seen_pre = life['know'].keys()
	_targets_not_seen = []
	
	if get_flag(life, 'surrendered'):
		return False
	
	if lfe.get_total_pain(life) > life['pain_tolerance']/2:
		speech.announce(life, 'call_for_help')
	
	for entry in life['seen']:
		_targets_not_seen_pre.remove(entry)
		target = life['know'][entry]
		_score = target['score']
		
		if snapshots.process_snapshot(life, target['life']):
			_score = judgement.judge(life, target)
			target['score'] = _score
			
			logging.info('%s judged %s with score %s.' % (' '.join(life['name']),' '.join(target['life']['name']),_score))
		
		_alife_seen.append({'who': target,'score': _score})
		
		if _score < 0:
			_targets_seen.append({'who': target,'score': _score})
	
	for _not_seen in _targets_not_seen_pre:
		target = life['know'][_not_seen]
		
		if snapshots.process_snapshot(life, life['know'][_not_seen]['life']):
			_score = judgement.judge(life, life['know'][_not_seen])
			life['know'][_not_seen]['score'] = _score
			
			logging.info('%s judged %s with score %s.' % (' '.join(life['name']),' '.join(target['life']['name']),_score))
		
		if life['know'][_not_seen]['score'] >= 0:
			_alife_not_seen.append({'who': target,'score': life['know'][_not_seen]['score']})
			continue
		
		_targets_not_seen.append({'who': target,'score': life['know'][_not_seen]['score']})
	
	generate_needs(life)
	
	_modules_run = False
	_times = []
	for module in MODULES:
		_stime = time.time()
		_return = module.conditions(life, _alife_seen, _alife_not_seen, _targets_seen, _targets_not_seen, source_map)
		
		if _return == STATE_CHANGE:
			lfe.change_state(life, module.STATE)
		
		if _return:
			module.tick(life, _alife_seen, _alife_not_seen, _targets_seen, _targets_not_seen, source_map)
			
			if _return == RETURN_SKIP:
				continue
			
			_modules_run = True
		
		_times.append({'time': time.time()-_stime, 'module': module.STATE})
	
	if not _modules_run:
		lfe.change_state(life, 'idle')
	
	#print ' '.join(life['name'])
	#for entry in _times:
	#	print '\t%s: %s' % (entry['module'], entry['time'])
