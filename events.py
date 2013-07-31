from globals import LIFE

import alife

import logging

def create(name, process_callback, process_arguments, complete_callback=None, complete_arguments=None, fail_callback=None, fail_arguments=None, repeat_every=-1):
	_event = {'name': name,
	          'process': {'callback': process_callback, 'arguments': process_arguments},
	          'complete_on': {'callback': complete_callback, 'arguments': complete_arguments},
	          'fail_on': {'callback': fail_callback, 'arguments': fail_arguments},
	          'repeat': repeat_every,
	          'completed': False,
	          'failed': False,
	          'accepted': [],
	          'flags': {}}
	
	return _event

def process_event(event):
	event['failed'] = False
	
	if event['completed']:
		return True
	
	if event['complete_on']['callback'] and event['complete_on']['callback'](**event['complete_on']['arguments']):
		event['completed'] = True
		return True
		
	if event['fail_on']['callback']:
		_args = {}
		
		for key in event['fail_on']['arguments']:
			if isinstance(event['fail_on']['arguments'][key], dict) and '_action' in event['fail_on']['arguments'][key]:
				_args[key] = alife.action.execute(event['fail_on']['arguments'][key])
			else:
				_args[key] = event['fail_on']['arguments'][key]
		
		if alife.action.execute(event['fail_on']['callback'])(**_args):
			event['failed'] = True
			return False
	
	if event['process']:
		_args = {}
		for key in event['process']['arguments']:
			if isinstance(event['process']['arguments'][key], dict) and '_action' in event['process']['arguments'][key]:
				_args[key] = alife.action.execute(event['process']['arguments'][key])
			else:
				_args[key] = event['process']['arguments'][key]
		
		alife.action.execute(event['process']['callback'])(**_args)
	
	return True

def accept(event, life_id):
	event['accepted'].append(life_id)
	
	logging.debug('%s has accepted event: %s' % (' '.join(LIFE[life_id]['name']), event['name']))

def has_accepted(event, life_id):
	if life_id in event['accepted']:
		return True
	
	return False

def clear_accepted(event):
	event['accepted'] = []
	
	logging.debug('Accepted list cleared for event: %s' % event['name'])

def flag(event, flag, value):
	_event['flags'][flag] = value

def unflag(event, flag):
	del _event['flags'][flag]

def get_flag(event, flag):
	if flag in _event['flags']:
		return _event['flags'][flag]
	
	return False