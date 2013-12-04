from globals import *

import life as lfe

import logging
import os

def add_goal(life, goal_name, desire, tier, loop_until, set_flags):
	if tier == 'relaxed':
		_tier = TIER_RELAXED
	elif tier == 'survival':
		_tier = TIER_SURVIVAL
	elif tier == 'urgent':
		_tier = TIER_URGENT
	elif tier == 'combat':
		_tier = TIER_COMBAT
	elif tier == 'tactic':
		_tier = TIER_TACTIC
	else:
		logging.error('Invalid tier in life type \'%s\': %s' % (life['species'], tier))
		_tier = TIER_RELAXED
	
	life['goap_goals'][goal_name] = {'desire': desire.split(','),
	                                 'tier': _tier,
	                                 'loop_until': loop_until.split(','),
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
	_loop_until = ''
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
					add_goal(life, _goal_name, _desire, _tier, _loop_until, _set_flags)
					
					_goal_name = ''
					_desire = ''
					_tier = ''
					_loop_until = ''
					_set_flags = ''
				elif _action_name:
					add_action(life, _action_name, _desire, _satisfies, _loop_until, _execute, _set_flags, _non_critical)
					
					_action_name = ''
					_desire = ''
					_tier = ''
					_loop_until = ''
					_set_flags = ''
					_execute = ''
					_satisfies = ''
					_non_critical = False
				

def find_actions_that_satisfy(life, desires):
	_valid_actions = []
	
	for action in life['goap_actions']:
		_break = False
		#_run_anyways = False
		
		for desire in desires:
			_continue_instead = False
			
			if desire.startswith('-'):
				continue
			elif desire.startswith('*'):
				_continue_instead = True
			#elif desire.startswith('+'):
			#	_run_anyways = True
			
			_desire = desire.replace('-', '').replace('*', '')
			
			if not _desire in life['goap_actions'][action]['satisfies']:
				if _continue_instead:
					continue
				else:
					#print 'action %s failed to meet the desires of %s' % (action, _desire)
					_break = True
					break
		
		if _break:
			continue
		
		_looping = False
		for loop_until_func in life['goap_actions'][action]['loop_until']:
			if not execute(life, loop_until_func):
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

def execute(life, func):
	_true = True
	_self_call = False
	
	while 1:
		if func.startswith('!'):
			func = func[1:]
			_true = False
		elif func.startswith('%'):
			func = func[1:]
			_self_call = True
		elif func.startswith('-'):
			func = func[1:]
		elif func.startswith('*'):
			func = func[1:]
		else:
			break
	
	
	if _self_call:
		if FUNCTION_MAP[func]() == _true:
			return True
	elif FUNCTION_MAP[func](life) == _true:
		return True
	
	return False

def execute_plan(life, plan):
	for action in plan:
		try:
			if not FUNCTION_MAP[life['goap_actions'][action]['execute']](life):
				break
		except KeyError:
			raise Exception('Invalid function in life type \'%s\' for action \'%s\': %s' % (life['species'], action, life['goap_actions'][action]['execute']))

def get_next_goal(life):
	_next_goal = {'highest': None, 'goal': None, 'plan': None}
	
	for goal in life['goap_goals']:
		_break = False
		
		for desire in life['goap_goals'][goal]['desire']:
			if '*' in desire:
				continue
			
			if execute(life, desire):
				#print life['name'], 'skipping', goal, 'because of', desire
				
				_loop = False
				if life['goap_goals'][goal]['loop_until'] and len(life['goap_goals'][goal]['loop_until'][0]):
					_loop = True
					
					for func in life['goap_goals'][goal]['loop_until']:
						if execute(life, func):
							_loop = False
							break
				
				if not _loop:
					_break = True
					break
		
		if _break:
			continue
		
		_plan = has_valid_plan_for_goal(life, goal)
		
		if not _plan:
			_plan = ['idle']
		
		if _plan and life['goap_goals'][goal]['tier'] > _next_goal['highest']:
			_next_goal['highest'] = life['goap_goals'][goal]['tier']
			_next_goal['goal'] = goal
			_next_goal['plan'] = _plan
		#elif not _plan:
		#	logging.warning('Failed to find plan for goal \'%s\'.' % goal)
		
	return _next_goal['goal'], _next_goal['highest'], _next_goal['plan']

def think(life):
	_goal_name = life['state']
	
	#TODO: Cache this
	_plan = has_valid_plan_for_goal(life, _goal_name)
	execute_plan(life, _plan)
