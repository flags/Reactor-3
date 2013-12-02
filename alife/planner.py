from globals import *

import life as lfe

import logging
import os

def add_goal(life, goal_name, desire, tier, set_flags):
	if tier == 'relaxed':
		_tier = TIER_RELAXED
	elif tier == 'survival':
		_tier = TIER_SURVIVAL
	else:
		logging.error('Invalid tier in life type \'%s\': %s' % (life['species'], tier))
		_tier = TIER_RELAXED
	
	life['goap_goals'][goal_name] = {'desire': desire.split(','),
	                                 'tier': _tier,
	                                 'set_flags': set_flags.split(',')}
	
	logging.debug('Created goal: %s' % goal_name)

def add_action(life, action_name, desire, satisfies, loop_until, execute, set_flags, non_critical):
	life['goap_actions'][action_name] = {'desire': desire.split(','),
	                                     'satisfies': satisfies.split(','),
	                                     'loop_until': loop_until.split(','),
	                                     'execute': execute,
	                                     'set_flags': set_flags.split(','),
	                                     'non_critical': non_critical == 'true'}
	
	logging.debug('Created action: %s' % action_name)

def parse_goap(life):
	logging.debug('Parsing GOAP for life type \'%s\'' % life['species'])
	
	_action_name = ''
	_goal_name = ''
	_desire = ''
	_tier = ''
	_loop = ''
	_set_flags = ''
	_execute = ''
	_satisfies = ''
	_non_critical = False
	
	with open(os.path.join(LIFE_DIR, life['species']+'.goap'), 'r') as _goap:
		for line in _goap.readlines():
			line = line.rstrip().lower()
			
			if line.startswith('[goal_'):
				_goal_name = line.split('[')[1].split(']')[0].partition('_')[2]
			elif line.startswith('[action_'):
				_action_name = line.split('[')[1].split(']')[0].partition('_')[2]			
			elif line.startswith('tier'):
				_tier = line.partition(':')[2].strip()			
			elif line.startswith('desire'):
				_desire = line.partition(':')[2].strip()
			elif line.startswith('set_flags'):
				_set_flags = line.partition(':')[2].strip()
			elif line.startswith('loop_until'):
				_loop_until = line.partition(':')[2].strip()
			elif line.startswith('execute'):
				_execute = line.partition(':')[2].strip()
			elif line.startswith('satisfies'):
				_satisfies = line.partition(':')[2].strip()
			elif line.startswith('non_critical'):
				_non_critical = line.partition(':')[2].strip()
			elif not line:
				if _goal_name:
					add_goal(life, _goal_name, _desire, _tier, _set_flags)
					
					_goal_name = ''
					_desire = ''
					_tier = ''
					_loop = ''
					_set_flags = ''
				elif _action_name:
					add_action(life, _action_name, _desire, _satisfies, _loop_until, _execute, _set_flags, _non_critical)
					
					_action_name = ''
					_desire = ''
					_tier = ''
					_loop = ''
					_set_flags = ''
					_execute = ''
					_satisfies = ''
					_non_critical = False
				

def find_actions_that_satisfy(life, desires):
	_valid_actions = []
	
	for action in life['goap_actions']:
		_break = False
		
		for desire in desires:
			if not desire in life['goap_actions'][action]['satisfies']:
				#print '%s not in action %s: discarding' % (desire, action)
				_break = True
				break
		
		if _break:
			continue
		
		_looping = False
		for loop_until_func in life['goap_actions'][action]['loop_until']:
			if not FUNCTION_MAP[loop_until_func](life):
				_looping = True
				
		if _looping:
			_valid_actions.append(action)
		
		break

	if _valid_actions and life['goap_actions'][_valid_actions[0]]['desire']:
		_valid_actions.extend(find_actions_that_satisfy(life, life['goap_actions'][_valid_actions[0]]['desire']))

	#print 'Valid:', _valid_actions
	return _valid_actions

def has_valid_plan_for_goal(life, goal_name):
	_plan = find_actions_that_satisfy(life, life['goap_goals'][goal_name]['desire'])
	_plan.reverse()
	
	#Revise
	_check_next = False
	for action in _plan[:]:
		if life['goap_actions'][action]['non_critical']:
			_check_next = True
		elif _check_next:
			_break = False
			
			for loop_until_func in life['goap_actions'][action]['loop_until']:
				if not FUNCTION_MAP[loop_until_func](life):
					_break = True
					break
			
			if not _break:
				_plan.remove(action)
			
			_check_next = False
	
	return _plan

def execute_plan(life, plan):
	for action in plan:
		try:
			if not FUNCTION_MAP[life['goap_actions'][action]['execute']](life):
				break
		except KeyError:
			raise Exception('Invalid function in life type \'%s\' for action \'%s\': %s' % (life['species'], action, life['goap_actions'][action]['execute']))

def get_next_goal(life):
	_next_goal = {'highest': None, 'goal': None}
	
	for goal in life['goap_goals']:
		_plan = has_valid_plan_for_goal(life, goal)
		
		if _plan and life['goap_goals'][goal]['tier'] > _next_goal['highest']:
			_next_goal['highest'] = life['goap_goals'][goal]['tier']
			_next_goal['goal'] = goal
		
	return _next_goal['goal'], _next_goal['highest']

def think(life):
	_goal_name = life['state']
	
	#TODO: Cache this
	_plan = has_valid_plan_for_goal(life, _goal_name)
	print life['name'], _plan
	execute_plan(life, _plan)
