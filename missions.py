from globals import MISSION_DIR, MISSIONS, FUNCTION_MAP

import graphics as gfx

import copy
import os

def load_mission(mission_file):
	_mission = {'name': mission_file.rpartition(os.sep)[2].replace('_', ' ').split('.')[0].title(),
	            'stages': {},
	            'stage_index': 1}
	_stage = {}
	_current_stage = None

	with open(mission_file, 'r') as _file:
		for line in _file.readlines():
			line = line.rstrip()
			
			if not line:
				continue
			
			if line.startswith('='):
				if _current_stage:
					_step_id = len(_mission['stages'][_current_stage]['steps'])+1
					_mission['stages'][_current_stage]['steps'][_step_id] = _step.copy()
				
				_current_stage = int(line.split('=')[1])
				_mission['stages'][_current_stage] = {'steps': {},
				                                      'flags': {},
				                                      'step_index': 1}
				continue
			
			elif line.startswith('COMPLETE'):
				_step_id = len(_mission['stages'][_current_stage]['steps'])+1
				_mission['stages'][_current_stage]['steps'][_step_id] = _step.copy()
				_current_stage = None
				
				continue
			
			_args = [l.lower() for l in line.split(' ')]
			
			if _args[0] == 'set':
				_step = {'mode': 'set',
				         'flag': _args[1],
				         'func': _args[2]}

			elif _args[0] == 'exec':
				_step = {'mode': 'exec',
				         'func': _args[1],
				         'args': _args[2:]}
			
			elif _args[0] == 'jumpif':
				_step = {'mode': 'jumpif',
				         'stage': _args[1],
				         'args': _args[2:]}
			
			if not _current_stage:
				raise Exception('No stage set: Missing stage tag.')
			
			_step_id = len(_mission['stages'][_current_stage]['steps'])+1
			_mission['stages'][_current_stage]['steps'][_step_id] = _step.copy()
	
	MISSIONS[mission_file.rpartition(os.sep)[2].split('.')[0]] = _mission

def load_all_missions():
	for (dirpath, dirnames, filenames) in os.walk(MISSION_DIR):
		for filename in [f for f in filenames if f.endswith('.dat')]:
			load_mission(os.path.join(dirpath, filename))

def create_mission(mission_name):
	if not mission_name in MISSIONS:
		raise Exception('Mission does not exist: %s' % mission_name)
	
	return copy.deepcopy(MISSIONS[mission_name])

def remember_mission(life, mission):
	life['missions'][len(life['missions'])+1] = mission

def activate_mission(life, mission_id):
	life['mission_id'] = mission_id
	
	if 'player' in life:
		gfx.glitch_text('Mission: %s' % life['missions'][life['mission_id']]['name'])

def exec_func(life, func, *args):
	return FUNCTION_MAP[func](life, *args)

def do_mission(life, mission_id):
	_mission = life['missions'][_mission_id]
	_stage = _mission['stages'][_mission['stage_index']]
	_step = _stage['steps'][_stage['step_index']]
	_steps_to_take = 0
	
	if _step['mode'] == 'exec':
		_func = exec_func(life, _step['func'], *_step['args'])
		_steps_to_take += 1
	
	elif _step['mode'] == 'set':
		_func = exec_func(life, _step['func'])
		_steps_to_take += 1
		
		_mission['flags'][_step['flag']] = _func
	
	_mission['stage_index'] += _steps_to_take