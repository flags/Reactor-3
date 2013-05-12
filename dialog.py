#A note before we start...
#It's impossible to summarize conversations into a single word,
#so we'll be passing around dictionaries that contain details
#of it so we can perform fuzzy matches across memories when
#finding responses.

from globals import *
from alife import judgement, brain

import life as lfe

import numbers

import logging
import random

def create_dialog_with(life, target, info):
	#If we're getting a gist then the conversation has already been started in some respect...
	#we'll get responses for now
	_messages = []
	
	if 'gist' in info:
		_topics, _memories = get_all_relevant_gist_responses(life, info['gist'])
		_messages = [{'sender': life['id'], 'text': info['gist']}]
	else:
		_topics, _memories = get_all_relevant_target_topics(life, target)
		_t, _m = get_all_irrelevant_target_topics(life, target)
		_topics.extend(_t)
		_memories.extend(_m)
		
		calculate_impacts(life, target, _topics)
	
	return {'enabled': True,
		'title': '',
		'sender': life['id'],
		'receiver': target,
		'info': info,
		'starting_topics': _topics,
		'topics': _topics,
		'previous_topics': [],
		'memories': _memories,
		'messages': _messages,
		'index': 0}

def get_all_relevant_gist_responses(life, gist):
	#TODO: We'll definitely need to extend this for fuzzy searching	
	#return [memory for memory in lfe.get_memory(life, matches={'text': gist})]
	_topics = []
	_memories = []
	
	if gist in ['greeting']:
		_topics.append({'text': 'How are you?', 'gist': 'how_are_you'})
		_topics.append({'text': 'I don\'t have time to talk.', 'gist': 'ignore'})
		_topics.append({'text': 'Get out of my face!', 'gist': 'ignore_rude'})
	
	return _topics, _memories

def get_all_relevant_target_topics(life, target):
	_topics = []
	_memories = []
	
	_topics.append({'text': 'How are you?', 'gist': 'how_are_you'})
	_topics.append({'text': 'What\'s new?', 'gist': 'how_are_you'})
	
	_memories.extend([memory for memory in lfe.get_memory(life, matches={'target': target})])
	
	return _topics, _memories

def get_all_irrelevant_target_topics(life, target):
	_topics = []
	_memories = []
	
	#TODO: This spawns a menu for the player to choose the desired ALife
	_topics.append({'text': 'Do you know...', 'gist': 'inquire_about', 'subtopics': get_known_alife})
	
	for ai in life['know']:
		if lfe.get_memory(life, matches={'target': ai}):
			_topics.append({'text': 'Did you know...', 'gist': 'tell_about', 'subtopics': tell_about_alife_select})
			break
	
	_memories.extend([memory for memory in lfe.get_memory(life, matches={'target': target})])
	
	return _topics, _memories

def get_all_responses_to(life, **kwargs):
	print 'Search:',kwargs
	for memory in lfe.get_memory(life, matches=kwargs):
		print memory

def calculate_impacts(life, target, topics):
	#TODO: Unused arguments
	#_score = judgement.judge(life, brain.knows_alife_by_id(life, target))
	
	for topic in topics:
		if 'subtopic' in topic:
			continue
		
		if not topic['gist'] in GIST_MAP:
			logging.warning('\'%s\' was not found in GIST_MAP.' % topic['gist'])
			topic['impact'] = 0
			continue
		
		topic['impact'] = GIST_MAP[topic['gist']]

def get_known_alife(life, chosen):
	_topics = []
	
	for ai in life['know']:
		_name = ' '.join(LIFE[ai]['name'])
		_topics.append({'text': _name,
			'message': 'Do you know %s?' % _name,
			'gist': chosen['gist'],
			'target': ai})
	
	return _topics

def tell_about_alife_select(life, chosen):
	_topics = []
	
	for ai in life['know']:		
		_name = ' '.join(LIFE[ai]['name'])
		_topics.append({'text': _name,
			'gist': chosen['gist'],
			'target': ai,
			'subtopics': tell_about_alife_memories})
	
	return _topics

def tell_about_alife_memories(life, chosen):
	_topics = []
	
	for memory in lfe.get_memory(life, matches={'target': chosen['target']}):
		_topics.append({'text': memory['text'],
			'gist': chosen['gist'],
			'target': chosen['target']})
	
	if not _topics:
		_topics.append({'text': 'No memory of this person!',
			'gist': chosen['gist'],
			'target': chosen['target']})
	
	return _topics

def add_message(life, dialog, chosen):
	_text = chosen['text']
	if 'message' in chosen:
		_text = chosen['message']
	
	_message = {'sender': life['id'], 'text': _text, 'impact': 1}
	dialog['messages'].append(_message)

def reset_dialog(dialog):
	_ret = False
	if dialog['previous_topics']:
		dialog['topics'] = dialog['previous_topics'].pop(0)
		dialog['previous_topics'] = []
		_ret = True
	else:
		dialog['topics'] = dialog['starting_topics']
	
	dialog['title'] = ''
	dialog['index'] = 0
	
	return _ret

def alife_choose_response(life, target, dialog, responses):
	_score = judgement.judge(life, brain.knows_alife_by_id(life, target['id']))
	_choices = [r for r in responses if numbers.clip(_score, -1, 1) == r['impact']]
	
	if _choices:
		_chosen = random.choice(_choices)
		add_message(life, dialog, _chosen)
		process_response(target, life, dialog, _chosen)
	else:
		reset_dialog(dialog)
		logging.error('Dialog didn\'t return anything.')

def process_response(life, target, dialog, chosen):
	_responses = []
	
	#TODO: Unused
	if chosen['gist'].count('positive'):
		_impact = 1
	elif chosen['gist'].count('negative'):
		_impact = -1
	else:
		_impact = 0
	
	if chosen['gist'] == 'how_are_you':
		_responses.append({'text': 'I\'m doing fine.', 'gist': 'status_response_neutral'})
		_responses.append({'text': 'I\'m doing fine, you?', 'gist': 'status_response_neutral_question'})
	elif chosen['gist'].count('status_response'):
		if chosen['gist'].count('question'):
			_responses.append({'text': 'Same.', 'gist': 'status_response'})
	elif chosen['gist'] == 'inquire_about':
		if chosen['target'] == life['id']:
			_responses.append({'text': 'That\'s me. Did you forget who I was?', 'gist': 'inquire_response_positive'})
			_responses.append({'text': 'That\'s my name.', 'gist': 'inquire_response_neutral'})
			_responses.append({'text': 'Who do you think you\'re talking to?', 'gist': 'inquire_response_negative'})
		else:
			if chosen['target'] in life['know']:
				_responses.append({'text': 'Yes, I know him!', 'gist': 'inquire_response_knows_positive', 'target': chosen['target']})
				_responses.append({'text': 'Sure.', 'gist': 'inquire_response_knows_neutral', 'target': chosen['target']})
				_responses.append({'text': 'Maybe.', 'gist': 'inquire_response_knows_negative', 'flags': ['CANBRIBE']})
			else:
				_responses.append({'text': 'I don\'t know who that is, sorry.', 'gist': 'inquire_response_unknown_positive', 'target': chosen['target']})
				_responses.append({'text': 'Sorry, I don\'t know who that is.', 'gist': 'inquire_response_unknown_positive', 'target': chosen['target']})
				_responses.append({'text': 'Can\'t help yah, friend...', 'gist': 'inquire_response_unknown_positive', 'target': chosen['target']})
				_responses.append({'text': 'I don\'t.', 'gist': 'inquire_response_unknown_neutral', 'target': chosen['target']})
				_responses.append({'text': 'Never heard that name before.', 'gist': 'inquire_response_unknown_neutral', 'target': chosen['target']})
				_responses.append({'text': 'I don\'t recall hearing that name.', 'gist': 'inquire_response_unknown_neutral', 'target': chosen['target']})
				_responses.append({'text': 'If I did, why would I tell you?', 'gist': 'inquire_response_unknown_negative', 'target': chosen['target'], 'flags': ['CANBRIBE']})
				_responses.append({'text': 'Why would I tell you?', 'gist': 'inquire_response_unknown_negative', 'target': chosen['target'], 'flags': ['CANBRIBE']})
	elif chosen['gist'].count('inquire_response'):
		#TODO: How about something similar to get_known_life()?
		#TODO: Or just a way to trigger a submenu response from a gist?
		if chosen['gist'].count('knows'):
			_responses.append({'text': 'Where was the last place you saw him?', 'gist': 'last_seen_target_at', 'target': chosen['target']})
	elif chosen['gist'] == 'last_seen_target_at':
		if 'target' in chosen:
			_responses.append({'text': 'Check here: ', 'gist': 'saw_target_at', 'target': chosen['target']})
		else:
			_responses.append({'text': 'Not telling you!', 'gist': 'saw_target_at'})
	else:
		logging.error('Gist \'%s\' did not generate any responses.' % chosen['gist'])
	
	#if not 'player' in life and not _responses:
	#	_responses.append({'text': 'No valid response.', 'gist': 'conversation_error'})
	
	calculate_impacts(life, target, _responses)
	
	if 'player' in life:
		if _responses:
			dialog['topics'] = _responses
			dialog['index'] = 0
		else:
			reset_dialog(dialog)
			
		return True
	
	alife_choose_response(life, target, dialog, _responses)

def give_menu_response(life, dialog):
	_chosen = dialog['topics'][dialog['index']]
	if 'subtopics' in _chosen:
		dialog['previous_topics'].append(dialog['topics'])
		dialog['title'] = _chosen['text']
		dialog['topics'] = _chosen['subtopics'](life, _chosen)
		dialog['index'] = 0
	else:
		add_message(life, dialog, _chosen)
		process_response(LIFE[dialog['receiver']], life, dialog, _chosen)

def draw_dialog():
	if not [d['enabled'] for d in SETTINGS['controlling']['dialogs'] if d['enabled']]:
		return False
	
	dialog = [d for d in SETTINGS['controlling']['dialogs'] if d['enabled']][0]
	_sender = LIFE[dialog['sender']]
	_receiver = LIFE[dialog['receiver']]
	
	if not 'console' in dialog:
		dialog['console'] = console_new(WINDOW_SIZE[0], 40)
	else:
		console_rect(dialog['console'],0,0,WINDOW_SIZE[0],40,True,flag=BKGND_DEFAULT)

	#TODO: Too tired to do this... :-)
	_index = -1
	_y = 2
	
	if dialog['title']:
		console_print(dialog['console'],
			1,
			1,
			dialog['title'])
	
	console_set_default_background(dialog['console'], black)
	for d in dialog['topics']:
		line = d['text']
		_index += 1
		_x = 1
		
		if not 'impact' in d:
			console_set_default_foreground(dialog['console'], white)
		elif d['impact'] == 1:
			console_set_default_foreground(dialog['console'], green)
		elif not d['impact']:
			console_set_default_foreground(dialog['console'], white)
		else:
			console_set_default_foreground(dialog['console'], red)
		
		if _index == dialog['index']:
			line = '> %s' % line
		
		while line:
			_line = line
			while len(_line)>=40:
				_words = _line.split(' ')
				_line = ' '.join(_words[:len(_words)-1])
				
			_lines = [_line]
			
			if not _line == line:
				_lines.append(line.replace(_line, ''))
			
			_i = 0
			for txt in _lines:
				console_print(dialog['console'],
					_x+_i,
					_y,
					txt)
				
				_i += 1
				_y += 1
			
			_x += 1
			_y += 1
			
			break
	
	_y = 1
	for m in dialog['messages'][numbers.clip(abs(len(dialog['messages']))-MAX_MESSAGES_IN_DIALOG, 0, 99999):]:
		part = (' '.join(LIFE[m['sender']]['name']), m['text'])
		_x = 41
		
		_impact = m['impact']
		for line in part:			
			if _impact == 1:
				console_set_default_foreground(dialog['console'], black)
				console_set_default_background(dialog['console'], green)
				console_set_background_flag(dialog['console'], BKGND_SET)
			elif not _impact:
				console_set_default_foreground(dialog['console'], white)
				console_set_default_background(dialog['console'], black)
				console_set_background_flag(dialog['console'], BKGND_SET)
			else:
				console_set_default_foreground(dialog['console'], black)
				console_set_default_background(dialog['console'], red)
				console_set_background_flag(dialog['console'], BKGND_SET)
			
			_impact = False
			
			while line:
				_line = line
				while len(_line)>=40:
					_words = _line.split(' ')
					_line = ' '.join(_words[:len(_words)-1])
					
				_lines = [_line]
				
				if not _line == line:
					_lines.append(line.replace(_line, ''))
				
				_i = 0
				for txt in _lines:
					console_print(dialog['console'],
						_x+_i,
						_y,
						txt)
					
					_i += 1
					_y += 1
				
				_x += 1
				_y += 1
				
				break
	
	console_set_background_flag(dialog['console'], BKGND_NONE)

