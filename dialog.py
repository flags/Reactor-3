from globals import *

import graphics as gfx
import life as lfe

import language
import numbers
import menus
import logic
import alife

import logging
import random

def create_dialog_with(life, target_id):
	_dialog = {'id': str(WORLD_INFO['dialogid']),
	           'messages': [],
	           'started_by': life['id'],
	           'target': target_id}
	
	life['dialogs'].append(_dialog['id'])
	
	WORLD_INFO['dialogs'][_dialog['id']] = _dialog
	WORLD_INFO['dialogid'] += 1
	
	return _dialog['id']

def get_dialog(dialog_id):
	return WORLD_INFO['dialogs'][dialog_id]

def end_dialog(dialog_id):
	_dialog = get_dialog(dialog_id)
	
	LIFE[_dialog['started_by']]['dialogs'].remove(dialog_id)
	LIFE[_dialog['target']]['dialogs'].remove(dialog_id)
	
	logging.debug('Dialog between %s and %s is over.' % (' '.join(LIFE[_dialog['started_by']]['name']), ' '.join(LIFE[_dialog['target']]['name'])))

def get_last_message(dialog_id):
	_dialog = get_dialog(dialog_id)
	
	if not _dialog['messages']:
		return None
	
	return _dialog['messages'][len(_dialog['messages'])-1]

def get_listener(dialog_id):
	_dialog = get_dialog(dialog_id)
	_last_message = get_last_message(dialog_id)
	
	if not _last_message:
		return _dialog['target']
	
	if _last_message['from'] == _dialog['started_by']:
		return _dialog['started_by']
	
	return _dialog['target']

def is_turn_to_talk(life, dialog_id):
	if not get_listener(dialog_id) == life['id']:
		return True
	
	return False

def get_matching_message(life, dialog_id, gist):
	_dialog_choices = []
	_target = get_listener(dialog_id)
	
	for dialog_options in DIALOG_TOPICS[gist.upper()]:
		_pass = True
		
		for requirement in dialog_options['requirements']:
			_req = requirement.lower()
			_true = True
			_self_call = False
			_no_args = False
			
			while 1:
				if _req.startswith('!'):
					_req = _req.strip('!')
					_true = False
					
					continue
				elif _req.startswith('@'):
					_req = _req.strip('@')
					_self_call = True
					
					continue
				elif _req.startswith('%'):
					_req = _req.strip('%')
					_no_args = True
					
					continue
				
				break
			
			if not _req in FUNCTION_MAP:
				raise Exception('Function in dialog option \'%s\' does not exist: %s' % (gist, _req))
			
			try:
				if _self_call:
					if not FUNCTION_MAP[_req](life) == _true:
						_pass = False
				elif _no_args:
					if not FUNCTION_MAP[_req]() == _true:
						_pass = False
				else:
					if not FUNCTION_MAP[_req](life, _target) == _true:
						_pass = False
			except Exception, e:
				logging.critical('Function \'%s\' got invalid arugments. See exception below.' % _req)
				raise e
			
			if not _pass:
				break
		
		if _pass:
			_dialog_choices.append(dialog_options)
	
	return _dialog_choices

def add_message(life, dialog_id, gist, text, result, loop=False):
	_dialog = get_dialog(dialog_id)
	
	_message = {'from': life['id'],
	            'gist': gist,
	            'text': text,
	            'read': False,
	            'result': result.lower(),
	            'loop': loop}
	
	print ' '.join(life['name'])+':', text
	
	_dialog['messages'].append(_message)

def say(life, dialog_id, gist, loop=False):
	_chosen_message = random.choice(get_matching_message(life, dialog_id, gist))
	_loop = False

	if _chosen_message['text'].startswith('>') and not loop:
		_chosen_message = random.choice(get_matching_message(life, dialog_id, _chosen_message['text'][1:]))
		_loop = True
	
	_target = get_listener(dialog_id)
	
	add_message(life, dialog_id, _chosen_message['gist'], _chosen_message['text'], _chosen_message['result'], loop=_loop)
	alife.speech.communicate(life, 'dialog', matches=[{'id': _target}], dialog_id=dialog_id)

def process(life, dialog_id):
	if not is_turn_to_talk(life, dialog_id):
		return False
	
	_last_message = get_last_message(dialog_id)
	
	if _last_message['result'] == 'end':
		end_dialog(dialog_id)
	else:
		say(life, dialog_id, _last_message['result'], loop=_last_message['loop'])

def draw_dialog(dialog_id):
	_dialog = get_dialog(dialog_id)
	_last_message = get_last_message(dialog_id)
	_x = MAP_WINDOW_SIZE[0]/2-len(_last_message['text'])/2
	_y = 10
	_responses = get_matching_message(LIFE[SETTINGS['controlling']], dialog_id, _last_message['result'])
	
	gfx.blit_string(_x, _y, _last_message['text'], 'overlay')
	
	for choice in :
		_text = choice['text']
		
		if _text.startswith('>'):
			_text = _text[1:]
		
		gfx.blit_string(_x, _y+3, _text.title(), 'overlay')
		_y += 2
