from globals import *

import graphics as gfx
import life as lfe

import language
import numbers
import drawing
import menus
import logic
import alife

import logging
import random
import re

def create_dialog_with(life, target_id, remote=False, **kwargs):
	_dialog = {'id': str(WORLD_INFO['dialogid']),
	           'messages': [],
	           'flags': kwargs,
	           'started_by': life['id'],
	           'target': target_id,
	           'choices': [],
	           'remote': remote,
	           'cursor_index': 0}
	
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

	if SETTINGS['controlling'] in [_dialog['started_by'], _dialog['target']]:
		lfe.focus_on(LIFE[SETTINGS['controlling']])
	
	logging.debug('Dialog between %s and %s is over.' % (' '.join(LIFE[_dialog['started_by']]['name']), ' '.join(LIFE[_dialog['target']]['name'])))

def get_flag(dialog_id, flag):
	return get_dialog(dialog_id)['flags'][flag.lower()]

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

def execute_function(life, target, dialog_id, function):
	_dialog = get_dialog(dialog_id)
	_function = function.lower()
	_pass = True
	_flags = {'true': True,
	          'self_call': False,
	          'no_args': False,
	          'return': False,
	          'pass_flags': False}
	_flag_map = {'!': {'true': False},
	             '@': {'self_call': True},
	             '%': {'no_args': True},
	             '$': {'return': True},
	             '^': {'pass_flags': True}}
	
	while 1:
		_flag = _function[0]
		
		if not _flag in _flag_map:
			break
		
		_function = _function[1:]
		_flags.update(_flag_map[_flag])
	
	if not _function in FUNCTION_MAP:
		raise Exception('Function does not exist: %s' % _function)
	
	print life['name'], _function, _flags, _dialog['flags']
	
	#try:
	if _flags['self_call']:
		if _flags['pass_flags']:
			_func = FUNCTION_MAP[_function](life, **_dialog['flags'])
		else:
			_func = FUNCTION_MAP[_function](life)
		
		if not _func == _flags['true']:
			_pass = False
	elif _flags['no_args']:
		if _flags['pass_flags']:
			_func = FUNCTION_MAP[_function](**_dialog['flags'])
		else:
			_func = FUNCTION_MAP[_function]()
		
		if not _func == _flags['true']:
			_pass = False
	else:
		if _flags['pass_flags']:
			_func = FUNCTION_MAP[_function](life, target, **_dialog['flags'])
		else:
			_func = FUNCTION_MAP[_function](life, target)
		
		if not _func == _flags['true']:
			_pass = False
	
	#print _function, _flags, _func
	#except Exception, e:
	#	logging.critical('Function \'%s\' got invalid arugments. See exception below.' % _function)
	#	raise e
	
	if _flags['return']:
		return _func
	
	if _pass:
		return True
	
	return False

def get_matching_message(life, dialog_id, gist):
	_dialog_choices = []
	_target = get_listener(dialog_id)
	
	if not gist.upper() in DIALOG_TOPICS:
		raise Exception('Dialog hit dead end due to no matching gist: %s' % gist)
	
	for dialog_option in DIALOG_TOPICS[gist.upper()]:
		_pass = True
		
		for requirement in dialog_option['requirements']:
			if not execute_function(life, _target, dialog_id, requirement):
				_pass = False
				break
		
		if not _pass:
			continue
		
		_dialog_choices.append(dialog_option)
	
	if not _dialog_choices:
		raise Exception('No dialog choices for gist: %s' % gist)
	
	return _dialog_choices

def add_message(life, dialog_id, gist, action, result, loop=False):
	_dialog = get_dialog(dialog_id)
	
	if _dialog['started_by'] == life['id']:
		_target = _dialog['target']
	else:
		_target = _dialog['started_by']
	
	_text = None
	for _entry in action.split(','):
		if _entry.startswith('\"'):
			_text = reformat_text(life, _target, dialog_id, _entry[1:].split('\"')[0])
		#elif _entry.startswith('>'):
		#	while _text.startswith('>') and not loop:
		#		_text = _text[1:]
		#		_chosen_message = random.choice(get_matching_message(life, dialog_id, _text))
		#		_loop = True
		else:
			_return = execute_function(life, _target, dialog_id, _entry)
			
			if isinstance(_return, str):
				_text = _return
			elif isinstance(_return, list):
				_text = random.choice(_return)
	
	if not _text:
		_text = '%s says nothing.' % ' '.join(life['name'])
	
	_message = {'from': life['id'],
	            'gist': gist,
	            'text': _text,
	            'read': False,
	            'result': result.lower().split(','),
	            'next_gist': None,
	            'loop': loop}
	
	if _dialog['remote']:
		print ' '.join(life['name'])+' (radio):', _text
	else:
		print ' '.join(life['name'])+':', _text
	
	_dialog['messages'].append(_message)
	
	for result in _message['result']:
		_result = reformat_text(life, _target, dialog_id, result)
		
		if _result.startswith('>'):
			_message['next_gist'] = _result[1:]
		else:
			if _result.count('='):
				_func = _result.split('=')[1]
			else:
				_func = _result
			
			if _func.count('\"'):
				_return = _func.partition('\"')[2].partition('\"')[0]
			else:
				_return = execute_function(life, _target, dialog_id, _func)
			
			if _result.count('='):
				_dialog['flags'][_result.split('=')[0]] = _return
				print 'returned', gist, _result, _func, _return
	
	alife.speech.communicate(life, 'dialog', matches=[{'id': _target}], dialog_id=dialog_id, radio=_dialog['remote'])

def reformat_text(life, target, dialog_id, text):
	_dialog = get_dialog(dialog_id)
	
	if text.count('%')%2:
		raise Exception('Closing \% not matched in string: %s' % text)
	
	for match in re.findall('%[\^\@\$\*\w]*%', text):
		_flag = match.replace('%', '').lower()
		
		if _flag.startswith('*'):
			_flag = _flag[1:]
			text = text.replace(match, execute_function(life, target, dialog_id, _flag))
		else:
			text = text.replace(match, _dialog['flags'][_flag])
	
	return text

def say_via_gist(life, dialog_id, gist, loop=False):
	_chosen_message = random.choice(get_matching_message(life, dialog_id, gist))
	_target = get_listener(dialog_id)
	_text = _chosen_message['text']#reformat_text(life, _target, dialog_id, _chosen_message['text'])
	_loop = False

	if not loop:
		while _text.startswith('>'):
			_text = _text[1:]
			_chosen_message = random.choice(get_matching_message(life, dialog_id, _text))
			_text = _chosen_message['text']
			_loop = True
	
	if 'player' in life:
		logic.show_event(_text.replace('\"', ''), life=life)
	
	add_message(life, dialog_id, _chosen_message['gist'], _chosen_message['text'], _chosen_message['result'], loop=_loop)

def select_choice(dialog_id):
	_dialog = get_dialog(dialog_id)
	_choice = _dialog['choices'][_dialog['cursor_index']]
	
	_loop = False
	if _choice in _dialog['loop_choices']:
		_loop = True
	
	_text = _choice['text']
	_text = _text[_text.index('\"')+1:_text.index('\"')-1]
	
	if not _text.endswith('...'):
		logic.show_event(_text, life=LIFE[SETTINGS['controlling']])
	
	add_message(LIFE[SETTINGS['controlling']], _dialog['id'], _choice['gist'], _choice['text'], _choice['result'], loop=_loop)

def process_dialog_for_player(dialog_id, loop=False):
	_dialog = get_dialog(dialog_id)
	_dialog['choices'] = []
	_dialog['loop_choices'] = []
	_dialog['cursor_index'] = 0	
	_last_message = get_last_message(dialog_id)
	
	if loop:
		end_dialog(dialog_id)
		return False
	
	for response in get_matching_message(LIFE[SETTINGS['controlling']], dialog_id, _last_message['next_gist']):
		_to_check = [response]
		while _to_check:
			_response = _to_check.pop()
			
			if _response['text'].startswith('>'):
				_text = reformat_text(LIFE[SETTINGS['controlling']], get_listener(dialog_id), dialog_id, _response['text'][1:])
				_to_check.extend(get_matching_message(LIFE[SETTINGS['controlling']], dialog_id, _text))
				_dialog['loop_choices'].extend(_to_check)
			else:
				_dialog['choices'].append(_response)
	
	_dialog['max_cursor_index'] = len(_dialog['choices'])

def process(life, dialog_id):
	if not is_turn_to_talk(life, dialog_id):
		return False
	
	_last_message = get_last_message(dialog_id)
	
	if _last_message['next_gist'] == 'end':
		end_dialog(dialog_id)
	elif 'player' in life:
		process_dialog_for_player(dialog_id, loop=_last_message['loop'])
	else:
		say_via_gist(life, dialog_id, _last_message['next_gist'], loop=_last_message['loop'])

def draw_dialog(dialog_id):
	_dialog = get_dialog(dialog_id)
	_last_message = get_last_message(dialog_id)
	_x = MAP_WINDOW_SIZE[0]/2-len(_last_message['text'])/2
	_y = 10
	_line_of_sight = drawing.diag_line(LIFE[_dialog['started_by']]['pos'], LIFE[_dialog['target']]['pos'])
	
	if len(_line_of_sight)<=1:
		_center_pos = LIFE[_dialog['started_by']]['pos']
	else:
		_center_pos = list(_line_of_sight[len(_line_of_sight)/2])
		_center_pos.append(2)
	
	if SETTINGS['controlling'] == _dialog['started_by']:
		_target = _dialog['target']
	else:
		_target = _dialog['started_by']
	
	_target_portrait = lfe.draw_life_icon(LIFE[_target], draw_alignment=True)
	
	_lines = []
	                                   
	gfx.camera_track(_center_pos)
	gfx.blit_string(_x-2, _y, _target_portrait[0], 'overlay', fore_color=_target_portrait[1])#, back_color=tcod.darkest_gray)
	gfx.blit_string(_x, _y, _last_message['text'], 'overlay')#, back_color=tcod.darkest_gray)
	
	for choice in _dialog['choices']:
		_text = choice['text'][choice['text'].index('\"')+1:choice['text'].index('\"')-1]
		
		if not _text.startswith('>'):
			_text = '> '+_text
		
		_n_x = MAP_WINDOW_SIZE[0]/2-len(_text)/2
		
		if _n_x < _x:
			_x = _n_x
	
	for choice in _dialog['choices']:
		_text = choice['text'][choice['text'].index('\"')+1:choice['text'].index('\"')-1]
		
		if _dialog['cursor_index'] == _dialog['choices'].index(choice):
			_text = '> '+_text
		
		_lines.append(_text)
	
	for line in _lines:
		gfx.blit_string(_x, _y+3, line, 'overlay')#, back_color=tcod.darkest_gray)
		_y += 2
