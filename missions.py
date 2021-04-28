from globals import MISSION_DIR, MISSIONS, FUNCTION_MAP, LIFE

import graphics as gfx
import life as lfe

import copy
import json
import os

def load_mission(mission_file):
	_mission = {'name': mission_file.rpartition(os.sep)[2].replace('_', ' ').split('.')[0].title(),
	            'stages': {},
	            'stage_index': 1,
	            'tasks': {},
	            'flags': {}}
	_stage = {}
	_current_stage = None
	_creating = False

	with open(mission_file, 'r') as _file:
		for line in _file.readlines():
			if line.startswith('#'):
				continue
			
			line = line.rstrip()
			
			if not line:
				continue
			
			if line.startswith('=CREATE'):
				_creating = True
				
			elif line.startswith('='):
				_creating = False
				
				if _current_stage:
					_step_id = len(_mission['stages'][str(_current_stage)]['steps'])+1
					_mission['stages'][str(_current_stage)]['steps'][str(_step_id)] = _step.copy()
				
				_current_stage = int(line.split('=')[1])
				_mission['stages'][str(_current_stage)] = {'steps': {},
				                                           'step_index': 1}
				continue
			
			#elif line.startswith('COMPLETE'):
			#	_step_id = len(_mission['stages'][_current_stage]['steps'])+1
			#	_mission['stages'][_current_stage]['steps'][_step_id] = _step.copy()
			#	_current_stage = None
			#	
			#	continue
			
			_args = [l.lower() for l in line.split(' ')]
			
			if _current_stage:
				if _args[0] == 'set':
					_step = {'mode': 'set',
						     'flag': _args[1],
						     'func': _args[2],
						     'args': _args[3:]}
	
				elif _args[0] in ['exec', 'wait']:
					_step = {'mode': _args[0],
						     'func': _args[1],
						     'args': _args[2:]}
				
				elif _args[0] == 'jump':
					_step = {'mode': 'jump',
						     'stage': int(_args[1]),
						     'args': []}
				
				elif _args[0] == 'jumpif':
					_step = {'mode': 'jumpif',
						     'stage': int(_args[1]),
						     'func': _args[2],
						     'args': _args[3:]}
				
				elif _args[0] == 'loop':
					_step = {'mode': 'loop'}
				
				elif _args[0] == 'finish':
					_step = {'mode': 'finish',
						     'task': _args[1]}
				
				elif _args[0] == 'task':
					_mission['tasks'][_args[1]] = {'completed': False, 'description': ' '.join(_args[2:]).replace('\"', '')}
				
				elif _args[0] == 'complete':
					_step = {'mode': 'complete'}
			
				_step_id = len(_mission['stages'][str(_current_stage)]['steps'])+1
				_mission['stages'][str(_current_stage)]['steps'][str(_step_id)] = _step.copy()
			elif _creating:
				if _args[0] == 'task':
					_mission['tasks'][_args[1]] = {'completed': False, 'description': ' '.join(_args[2:]).replace('\"', '')}
	
	MISSIONS[mission_file.rpartition(os.sep)[2].split('.')[0]] = _mission

def load_all_missions():
	for (dirpath, dirnames, filenames) in os.walk(MISSION_DIR):
		for filename in [f for f in filenames if f.endswith('.dat')]:
			load_mission(os.path.join(dirpath, filename))

def create_mission(mission_name, **kwargs):
	if not mission_name in MISSIONS:
		raise Exception('Mission does not exist: %s' % mission_name)
	
	_mission = copy.deepcopy(MISSIONS[mission_name])
	_mission['flags'].update(kwargs)
	
	return _mission

def create_mission_and_give(life, mission_name, target_id, **kwargs):
	_mission = create_mission(mission_name, **kwargs)
	
	return remember_mission(LIFE[target_id], _mission)

def create_mission_for_self(life, mission_name, **kwargs):
	return create_mission_and_give(life, mission_name, life['id'], **kwargs)

def remember_mission(life, mission):
	_id = str(len(life['missions'])+1)
	
	life['missions'][_id] = mission
	
	if 'player' in life and not life['mission_id']:
		life['mission_id'] = _id
		
		gfx.glitch_text('Added Mission: %s' % mission['name'])
	
	return _id

def activate_mission(life, mission_id):
	life['mission_id'] = mission_id
	
	if 'player' in life:
		_active_task_description = get_active_task(life, mission_id)['description']
		gfx.glitch_text('Task: %s' % _active_task_description)

def get_active_task(life, mission_id):
	_mission = life['mission_id'][mission_id]
	
	if not _mission['tasks']:
		return None
	
	return [t for t in _mission['tasks'] if not _mission['tasks'][t]['completed']][0]

def has_mission_with_name(life, mission_name):
	for mission in list(life['missions'].values()):
		if mission['name'] == mission_name:
			return True
	
	return False

def change_task_description(life, mission_id, task_number, description):
	_mission = life['missions'][mission_id]
	_mission['tasks'][str(task_number)]['description'] = description

def complete_mission(life, mission_id):
	if 'player' in life:
		gfx.glitch_text('Mission complete: %s' % life['missions'][mission_id]['name'])
	
	if life['mission_id'] == mission_id:
		life['mission_id'] = None
	
	del life['missions'][mission_id]

def exec_func(life, func, *args, **kwargs):
	if func[0] == '!':
		return not FUNCTION_MAP[func[1:]](life, *args, **kwargs)
	
	#try:
	return FUNCTION_MAP[func](life, *args, **kwargs)
	#except:
	#	raise Exception('Failed to execute: %s' % func)

def do_mission(life, mission_id):
	_mission = life['missions'][mission_id]
	
	while 1:
		_stage = _mission['stages'][str(_mission['stage_index'])]
		_step = _stage['steps'][str(_stage['step_index'])]
		_args = []
		_kwargs = {}
		
		if _step['mode'] == 'complete':
			complete_mission(life, mission_id)
			
			return False
		
		elif _step['mode'] in ['jump', 'loop']:
			_stage['step_index'] = 1
			
			if _step['mode'] == 'jump':
				_mission['stage_index'] = _step['stage']
				
				continue
			else:
				return False
		
		elif _step['mode'] == 'finish':
			_mission['tasks'][_step['task']]['completed'] = True
			_stage['step_index'] += 1
			
			continue
		
		for arg in _step['args']:
			if arg.startswith('%'):
				_args.append(_mission['flags'][arg[1:len(arg)-1]])
			elif arg.startswith('{'):
				for flag in arg.split(':'):
					_flag = flag.partition('%')[2].rpartition('%')[0]
					
					if _flag:
						arg = arg.replace('%%%s%%' % _flag, '\"%s\"' % _mission['flags'][_flag])
				
				_kwargs.update(json.loads(arg))
			elif arg.count('.'):
				_args.append(float(arg))
			else:
				_args.append(arg)
		
		if _kwargs:
			_func = exec_func(life, _step['func'], *_args, **_kwargs)
		else:
			_func = exec_func(life, _step['func'], *_args)
		
		if _step['mode'] in ['wait', 'jumpif']:
			if _func:
				if _step['mode'] == 'wait':
					_stage['step_index'] += 1
				else:
					_stage['step_index'] = 1
					_mission['stage_index'] = _step['stage']
					
					continue
			elif _step['mode'] == 'jumpif':
				_stage['step_index'] += 1
				
				continue
			else: #Wait
				return True
		
		elif _step['mode'] == 'set':
			_mission['flags'][_step['flag']] = _func
			_stage['step_index'] += 1
		
		elif _step['mode'] == 'exec':
			_stage['step_index'] += 1
		
		else:
			return False
