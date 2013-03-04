from globals import *

import life as lfe

import alife_collect_items
import alife_hidden
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

def think(life, source_map):
	sight.look(life)
	sound.listen(life)
	understand(life, source_map)

def flag(life,flag):
	life['flags'][flag] = True

def unflag(life,flag):
	life['flags'][flag] = False

def get_flag(life,flag):
	if not flag in life['flags']:
		return False
	
	return life['flags'][flag]

def flag_item(life,item,flag):
	print ' '.join(life['name'])
	
	if not flag in life['know_items'][item['uid']]['flags']:
		life['know_items'][item['uid']]['flags'].append(flag)
		logging.debug('%s flagged item %s with %s' % (' '.join(life['name']),item['uid'],flag))
		
		return True
	
	return False

def remember_item(life,item):
	if not item['uid'] in life['know_items']:
		life['know_items'][item['uid']] = {'item': item,
			'score': judgement.judge_item(life,item),
			'last_seen_at': item['pos'][:],
			'flags': []}
		
		return True
	
	return False

def understand(life,source_map):
	_alife_seen = []
	_alife_not_seen = []
	_targets_seen = []
	_targets_not_seen = []
	_neutral_targets = []
	_known_targets_not_seen = life['know'].keys()
	
	if get_flag(life, 'surrendered'):
		return False
	
	if lfe.get_total_pain(life) > life['pain_tolerance']/2:
		communicate(life,'surrender')
	
	for entry in life['seen']:
		_known_targets_not_seen.remove(entry)
		target = life['know'][entry]
		_score = target['score']
		
		if target['life']['asleep']:
			continue
		
		if snapshots.process_snapshot(life,target['life']):
			_score = judgement.judge(life,target)
			target['score'] = _score
			
			logging.info('%s judged %s with score %s.' % (' '.join(life['name']),' '.join(target['life']['name']),_score))
		
		_alife_seen.append({'who': target,'score': _score})
		
		if _score <= 0:
			_targets_seen.append({'who': target,'score': _score})
		
		#if _score <= 0 and _score > _target['score']:
		#	_target['who'] = target
		#	_target['score'] = _score
		#elif _score>0:
		#	_neutral_targets.append(target)
	
	for _not_seen in _known_targets_not_seen:
		#TODO: 350?
		if life['know'][_not_seen]['last_seen_time']<350:
			life['know'][_not_seen]['last_seen_time'] += 1	
	
	_known_targets_not_seen = [life['know'][entry] for entry in _known_targets_not_seen]
	
	#if not _targets_seen:
	#	#TODO: No visible target, doesn't mean they're not there
	#	#_lost_target = sight.handle_lost_los(life)
	#	
	#	#if _lost_target['target']:
	#	#	_target = {}
	#	#	_target['who'] = _lost_target['target']
	#	#	_target['score'] = _lost_target['target']['score']
	#	#	_target['danger_score'] = _lost_target['score']
	#	#	_target['last_seen_time'] = _lost_target['target']['last_seen_time']
	#	#else:
	#	#	#TODO: Some kind of cooldown here...
	#	#	print 'No lost targets'
	
	#if _target['who']:
	#	_targets.append(_target['who'])
	
	METHODS = [alife_hide, alife_hidden, alife_collect_items]
	_seen = [life['know'][entry] for entry in life['seen']]
	
	for method in METHODS:
		_return = method.conditions(life, _alife_seen, _alife_not_seen, _targets_seen, _targets_not_seen, source_map)
		
		if _return == STATE_CHANGE:
			lfe.change_state(life, method.STATE)
		
		if _return:
			method.tick(life, _alife_seen, _alife_not_seen, _targets_seen, _targets_not_seen, source_map)
	
	#if _target['who']:
	#	if judgement.in_danger(life,_target):
	#		movement.handle_hide_and_decide(life,_target['who'],source_map)
	#	else:
	#		if speech.has_considered(life,_target['who']['life'],'surrendered') and not speech.has_considered(life,_target['who']['life'],'resist'):
	#			if speech.consider(life,_target['who']['life'],'asked_to_comply'):
	#				_visible_items = lfe.get_all_visible_items(_target['who']['life'])
	#				
	#				if _visible_items:
	#					_item_to_drop = _visible_items[0]
	#					speech.communicate(life,'demand_drop_item',item=_item_to_drop,target=_target['who']['life'])
	#					
	#					lfe.say(life,'Drop that %s!' % lfe.get_inventory_item(_target['who']['life'],_item_to_drop)['name'])
	#					lfe.clear_actions(life,matches=[{'action': 'shoot'}])
	#				else:
	#					logging.warning('No items visible on target!')
	#			
	#			if speech.has_considered(life,_target['who']['life'],'compliant'):
	#				if not lfe.get_held_items(_target['who']['life'],matches=[{'type': 'gun'}]):
	#					lfe.say(life,'Now get out of here!')
	#					speech.communicate(life,'free_to_go',target=_target['who']['life'])
	#					speech.unconsider(life,_target['who']['life'],'surrendered')
	#			
	#		else:
	#			combat.handle_potential_combat_encounter(life,_target['who'],source_map)
	#	
	#else:
	#	for neutral_target in _neutral_targets:
	#		if speech.has_considered(life, neutral_target['life'], 'greeting'):
	#			continue
	#
	#		speech.communicate(life, 'greeting', target=neutral_target['life'])
	#
	#	survival.survive(life)
