from globals import MISSION_DIR, MISSIONS

import os

def load_mission(mission_file):
	_mission = {'stages': {},
	            'task_index': 0}
	_stage = {}
	_current_stage = None

	with open(mission_file, 'r') as _file:
		for line in _file.readlines():
			line = line.rstrip()
			
			if not line:
				continue
			
			if line.startswith('='):
				if _current_stage:
					_mission['stages'][_current_stage] = _stage
				
				_stage = {'mode': None,
				          'flags': {}}
				_current_stage = int(line.split('=')[1])
				
				continue
			
			elif line.startswith('COMPLETE'):
				_mission['stages'][_current_stage] = _stage
				_current_stage = None
				
				continue
			
			elif line.startswith('SET'):
				_stage['mode'] = 'set'
			
			_args = line.split(' ')[1:]
			_stage['func'] = _args[0]
			_stage['args'] = _args[1:]
			
			if not _current_stage:
				raise Exception('No stage set: Missing stage tag.')
				
			_mission[_current_stage] = _stage
	
	print _mission

def load_all_missions():
	for (dirpath, dirnames, filenames) in os.walk(MISSION_DIR):
		for filename in [f for f in filenames if f.endswith('.dat')]:
			load_mission(os.path.join(dirpath, filename))

load_all_missions()