from globals import *

import life as lfe

import action

import traceback
import logging
import sys

def has_goal(life, name):
	return [g for g in life['goals'].values() if g['name'] == name]

def get_active_goals(life):
	_active = []
	
	for goal in [g for g in life['goals'].values() if not g['complete']]:
		if perform_goal(life, goal['id'], only_required=True):
			_active.append(goal['id'])

	return _active

def get_goal_via_id(life, goal_id):
	if goal_id in life['goals']:
		return life['goals'][goal_id]
	
	raise Exception('%s has no goal with ID `%s`' % (' '.join(life['name']), goal_id))

def get_criteria(life, goal_id, criteria_id):
	_goal = get_goal_via_id(life, goal_id)
	
	if criteria_id in _goal['criteria']:
		return _goal['criteria'][criteria_id]
	
	raise Exception('%s has no goal with criteria ID `%s`' % (' '.join(life['name']), criteria_id))

def add_goal(life, name, **kwargs):
	if has_goal(life, name):
		return False
	
	_goal = {'name': name,
		'criteria': {},
		'id': WORLD_INFO['goalid'],
		'cid': 1,
		'flags': {},
		'tags': {},
		'complete_on_answer': [],
		'complete': False}

	if 'investigate' in kwargs:
		_goal['tags']['investigate'] = True
	
	life['goals'][_goal['id']] = _goal
	
	WORLD_INFO['goalid'] += 1
	logging.debug('%s added goal: %s' % (' '.join(life['name']), name))
	
	return _goal['id']

def flag(life, goal_id, flag, value):
	_goal = get_goal_via_id(life, goal_id)
	
	_goal['flags'][flag] = value

def get_flag(life, goal_id, flag):
	_goal = get_goal_via_id(life, goal_id)
	
	if not flag in _goal['flags']:
		raise Exception('%s: group \'%s\' does not have flag: %s' % (' '.join(life['name']), _goal['name'], flag))
	
	return _goal['flags'][flag]

def add_criteria(life, goal_id, kind, criteria, required=False):
	_goal = get_goal_via_id(life, goal_id)
	
	criteria['id'] = _goal['cid']
	criteria['sub_criteria'] = []
	criteria['type'] = kind
	criteria['required'] = required
	_goal['criteria'][criteria['id']] = criteria
	_goal['cid'] += 1
	
	logging.debug('%s added criteria to goal \'%s\': %s' % (' '.join(life['name']), _goal['name'], criteria['type']))
	
	return criteria['id']

def add_action(life, goal_id, action, required=False):
	_goal = get_goal_via_id(life, goal_id)
	
	return add_criteria(life, goal_id, 'action', {'action': action}, required=required)

def add_task(life, goal_id, callback, **kwargs):
	_goal = get_goal_via_id(life, goal_id)
	
	return add_criteria(life, goal_id, 'task', {'args': kwargs})

def add_memory(life, goal_id, memory):
	_goal = get_goal_via_id(life, goal_id)
	
	return add_criteria(life, goal_id, 'memory', {'matching': memory})

def filter_criteria(life, goal_id, criteria_id, callback, invert=False):
	_goal = get_goal_via_id(life, goal_id)
	
	_criteria = get_criteria(life, goal_id, criteria_id)
	_criteria['sub_criteria'].append({'filter': callback})
	_criteria['invert'] = invert
	
	logging.debug('%s added sub-criteria filter to \'%s\' in goal \'%s\'' % (' '.join(life['name']), criteria_id, goal_id))

def filter_criteria_with_action(life, goal_id, criteria_id, action):
	_goal = get_goal_via_id(life, goal_id)
	
	_criteria = get_criteria(life, goal_id, criteria_id)
	_criteria['sub_criteria'].append({'filter_action': action})
	
	logging.debug('%s added sub-criteria filter_action to \'%s\' in goal \'%s\'' % (' '.join(life['name']), criteria_id, goal_id))

def match_criteria(life, goal_id, criteria_id, callback, **kwargs):
	_goal = get_goal_via_id(life, goal_id)
	
	_criteria = get_criteria(life, goal_id, criteria_id)
	_criteria['sub_criteria'].append({'match': callback, 'args': kwargs})
	
	logging.debug('%s added sub-criteria match to \'%s\' in goal \'%s\'' % (' '.join(life['name']), criteria_id, goal_id))

def match_action(life, goal_id, criteria_id, action):
	_goal = get_goal_via_id(life, goal_id)
	
	_criteria = get_criteria(life, goal_id, criteria_id)
	_criteria['sub_criteria'].append({'match_action': action})
	
	logging.debug('%s added sub-criteria match_action to \'%s\' in goal \'%s\'' % (' '.join(life['name']), criteria_id, goal_id))

def check_for_goal_finish(life, goal_id, passed=False):
	_goal = get_goal_via_id(life, goal_id)
	
	if _goal['complete']:
		return True
	
	for question in _goal['complete_on_answer']:
		if lfe.get_memory_via_id(life, question)['answered']:
			print 'DELETED GOAL!' * 100
			_goal['complete'] = True
			break
	
	if passed:
		print 'DELETED GOAL!' * 100
		_goal['complete'] = True
		
		print 'FINISHED GOAL' * 50

def perform_goal(life, goal_id, only_required=False):
	_goal = get_goal_via_id(life, goal_id)
	_passed = True
	
	for criteria in _goal['criteria'].values():
		if only_required and not criteria['required']:
			continue
		
		criteria['result'] = None
		
		if criteria['type'] == 'memory':
			criteria['result'] = lfe.get_memory(life, matches=criteria['memory'])
			
		elif criteria['type'] == 'action':
			criteria['result'] = action.execute(criteria['action'])
	
		if criteria['result']:
			_process = process_criteria(life, goal_id, criteria['id'], criteria['result'])
			criteria['result'] = _process
			
			if not criteria['result']:
				print 'Goal not met', life['name'], criteria				
				_passed = False
				continue
		else:
			if not meet_criteria(life, goal_id, criteria['id']):
				_passed = False
				continue
	
	check_for_goal_finish(life, _goal['id'], passed=_passed)
	
	return _passed

def meet_criteria(life, goal_id, criteria_id):
	""" Perform actions that will generate criteria """
	_goal = get_goal_via_id(life, goal_id)
	_criteria = get_criteria(life, goal_id, criteria_id)
	
	if 'match' in _criteria:
		_criteria['result'] = _criteria['match'](life, *_criteria['args'])
	elif 'match_action' in _criteria:
		_criteria['result'] = action.execute(_criteria['match_action'])
	elif 'filter' in _criteria:
		_criteria['result'] = [entry for entry in result if not _criteria['filter'](life, entry) == _criteria['invert']]
	elif 'filter_action' in _criteria:
		_criteria['result'] = action.execute(_criteria['filter_action'])

def process_criteria(life, goal_id, criteria_id, result):
	""" Checks result of goal """
	_goal = get_goal_via_id(life, goal_id)
	_criteria = get_criteria(life, goal_id, criteria_id)
	
	for sub_criteria in _criteria['sub_criteria']:
		if 'match' in sub_criteria:
			_criteria['result'] = sub_criteria['match'](life, **sub_criteria['args'])
		elif 'match_action' in sub_criteria:
			_criteria['result'] = action.execute(sub_criteria['match_action'])
		elif 'filter' in sub_criteria:
			#print 'HERE' * 75
			#for entry in result:
			#	print sub_criteria['filter'](life, entry)
				
			_criteria['result'] = [entry for entry in result if sub_criteria['filter'](life, entry)]
		elif 'filter_action' in sub_criteria:
			_criteria['result'] = action.execute(sub_criteria['filter_action'])
		
		if _criteria['result']:
			print 'Sub-criteria passed:', sub_criteria
		else:
			print 'Sub-criteria failed:', sub_criteria
			break
	
	return _criteria['result']
