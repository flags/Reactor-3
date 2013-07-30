import logging

def create(name, complete_callback, complete_arguments, fail_callback, fail_arguments, repeat_every):
	_event = {'name': name,
	          'pass_on': {'callback': complete_callback, 'arguments': complete_arguments},
	          'fail_on': {'callback': fail_callback, 'arguments': fail_arguments},
	          'repeat': repeat_every,
	          'completed': False,
	          'failed': False,
	          'flags': {}}
	
	return _event

def process_event(event):
	if _event['completed']:
		return True
	
	if event['complete_on']['callback'](**event['complete_on']['arguments']):
		_event['completed'] = True
		return True
		
	if event['fail_on']['callback'](**event['fail_on']['arguments']):
		event['failed'] = True
		return False
	
	return True

def flag(event, flag, value):
	_event['flags'][flag] = value

def unflag(event, flag):
	del _event['flags'][flag]

def get_flag(event, flag):
	if flag in _event['flags']:
		return _event['flags'][flag]
	
	return False