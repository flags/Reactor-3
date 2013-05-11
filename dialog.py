#A note before we start...
#It's impossible to summarize conversations into a single word,
#so we'll be passing around dictionaries that contain details
#of it so we can perform fuzzy matches across memories when
#finding responses.

from globals import *
from alife import judgement, brain

import life as lfe

import logging

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
		'sender': life['id'],
		'receiver': target,
		'info': info,
		'topics': _topics,
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
	_topics.append({'text': 'Do you know...', 'subtopic': get_known_alife})
	
	_memories.extend([memory for memory in lfe.get_memory(life, matches={'target': target})])
	
	return _topics, _memories

def get_all_responses_to(life, **kwargs):
	print 'Search:',kwargs
	for memory in lfe.get_memory(life, matches=kwargs):
		print memory

def calculate_impacts(life, target, topics):
	#TODO: Unused
	_score = judgement.judge(life, brain.knows_alife_by_id(life, target))
	
	for topic in topics:
		if 'subtopic' in topic:
			continue
		
		if not topic['gist'] in GIST_MAP:
			logging.warning('\'%s\' was not found in GIST_MAP.')
			topic['impact'] = 0
			continue
		
		topic['impact'] = GIST_MAP[topic['gist']]
		
def get_known_alife(life):
	pass

def give_menu_response(life, dialog):
	_chosen = dialog['topics'][dialog['index']]
	_message = {'sender': life['id'], 'text': _chosen['text'], 'impact': 1}
	dialog['messages'].append(_message)

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
		console_set_default_foreground(dialog['console'], white)

	#TODO: Too tired to do this... :-)
	_index = -1
	_y = 1
	for line in [d['text'] for d in dialog['topics']]:
		_index += 1
		_x = 1
		
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
	for m in dialog['messages']:
		part = (' '.join(LIFE[m['sender']]['name']), m['text'])
		_x = 41
		
		_impact = m['impact']
		for line in part:			
			if _impact == 1:
				console_set_default_foreground(dialog['console'], green)
			elif not _impact:
				console_set_default_foreground(dialog['console'], white)
			else:
				console_set_default_foreground(dialog['console'], red)
			
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

