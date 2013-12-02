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

def add_action(life, action_name, desire, satisfies, loop_until, execute, set_flags):
	life['goap_actions'][action_name] = {'desire': desire.split(','),
	                                     'satisfies': satisfies.split(','),
	                                     'loop_until': loop_until.split(','),
	                                     'execute': execute,
	                                     'set_flags': set_flags.split(',')}
	
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
	
	with open(os.path.join(LIFE_DIR, life['species']+'.goap'), 'r') as _goap:
		for line in _goap.readlines():
			line = line.rstrip().lower()
			
			if line.startswith('[goal_'):
				_goal_name = line.split('[')[1].split(']')[0].partition('_')[2]
			elif line.startswith('[action_'):
				if _action_name:
					add_action(life, _action_name, _desire, _satisfies, _loop_until, _execute, _set_flags)
					
					_action_name = ''
					_desire = ''
					_tier = ''
					_loop = ''
					_set_flags = ''
					_execute = ''
					_satisfies = ''
				
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

def find_actions_that_satisfy(life, desires):
	_valid_actions = []
	
	for action in life['goap_actions']:
		_break = False
		
		for desire in desires:
			if not desire in life['goap_actions'][action]['satisfies']:
				_break = True
				break
		
		if _break:
			continue
		
		_valid_actions.append(action)
	
	return _valid_actions

def has_valid_plan_for_goal(life, goal_name):
	return find_actions_that_satisfy(life, life['goap_goals'][goal_name]['desire'])

def execute_action(life, action, conditions=[]):
	_section = 'action_%s' % action
	_conditions = conditions
	
	if rawparse.raw_section_has_identifier(life, _section, 'conditions'):
		for argument_group in rawparse.get_arguments(life, _section, 'conditions'):
			_temp_conditions = []
			_break = False
			
			for argument in argument_group:
				if not execute_action(life, argument):
					_break = True
					break
				
				_temp_conditions.append(action)
				
			if _break:
				continue
			else:
				_conditions.extend(_temp_conditions)
				return True
		
		return False
	
	if rawparse.raw_section_has_identifier(life, _section, 'context'):
		if not lfe.execute_raw(life, _section, 'context'):
			return False
	
	return action

def execute_plan(life, plan):
	for action in plan:
		if not FUNCTION_MAP[life['goap_actions'][action]['execute']](life):
			break

def get_next_goal(life):
	_next_goal = {'highest': None, 'goal': None}
	print life['goap_goals'].keys()
	for goal in life['goap_goals']:
		_plan = has_valid_plan_for_goal(life, goal)
		
		#print goal, _plan
		
		if _plan and life['goap_goals'][goal]['tier'] > _next_goal['highest']:
			_next_goal['highest'] = life['goap_goals'][goal]['tier']
			_next_goal['goal'] = goal
		
	return _next_goal['goal'], _next_goal['highest']

def think(life):
	_goal_name = life['state']
	
	#TODO: Cache this
	_plan = has_valid_plan_for_goal(life, _goal_name)
	execute_plan(life, _plan)
