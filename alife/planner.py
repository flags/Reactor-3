from globals import *

import life as lfe

import rawparse


def parse_goals(life):
	_goals = {}
	
	for section in rawparse.get_raw_sections(life):
		if not section.startswith('goal'):
			continue
		
		_goal_name = section.partition('_')[2]
		
		if not _goal_name:
			raise Exception('Invalid goal name: Must contain characters after `_`.')
		
		_raw_goal_tier = lfe.execute_raw(life, section, 'tier')
		
		if _raw_goal_tier == 'relaxed':
			_goal_tier = TIER_RELAXED
		elif _raw_goal_tier == 'survival':
			_goal_tier = TIER_SURVIVAL
		else:
			raise Exception('No priority set for goal: %s.' % _goal_name)
		
		_goals[_goal_name] = {'tier': _raw_goal_tier,
		                      'section': section}
	
	return _goals

def get_next_goal(life):
	_next_goal = {'highest': None, 'goal': None}
	
	for goal in life['goals']:
		if not lfe.execute_raw(life, life['goals'][goal]['section'], 'desire'):
			if life['goals'][goal]['tier']>_next_goal['highest'] and has_valid_plan_for_goal(life, goal):
				_next_goal['highest'] = life['goals'][goal]['tier']
				_next_goal['goal'] = goal
		
	return _next_goal['goal'], _next_goal['highest']

def has_valid_plan_for_goal(life, goal_name, execute=False):
	#for action in rawparse.get_arguments(life, _section, 'conditions'):
	for action in rawparse.get_arguments(life, 'goal_%s' % goal_name, 'actions'):
		_ret = execute_action(life, action[0]['string'])
		
		if _ret:
			if not execute:
				return True
			
			FUNCTION_MAP[_ret](life)
			break
	
	return False

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

def think(life):
	_goal_name = life['state']
	
	if has_valid_plan_for_goal(life, _goal_name, execute=True):
		print 'Plan OK', _goal_name
