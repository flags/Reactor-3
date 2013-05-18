#A note before we start...
#It's impossible to summarize conversations into a single word,
#so we'll be passing around dictionaries that contain details
#of it so we can perform fuzzy matches across memories when
#finding responses.

from globals import *

import life as lfe

import numbers
import alife

import logging
import random

def create_dialog_with(life, target, info):
	#If we're getting a gist then the conversation has already been started in some respect...
	#we'll get responses for now
	_messages = []
	
	if 'gist' in info:
		_topics, _memories = get_all_relevant_gist_responses(life, target, info['gist'])					
	else:
		_topics, _memories = get_all_relevant_target_topics(life, target)
		_t, _m = get_all_irrelevant_target_topics(life, target)
		_topics.extend(_t)
		_memories.extend(_m)
		
		calculate_impacts(life, target, _topics)
	
	if not _topics:
		return False
	
	_dialog = {'enabled': True,
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
	
	if 'player' in LIFE[target]:
		LIFE[target]['dialogs'].append(_dialog)
	
	return _dialog

def add_message(life, dialog, chosen):
	_text = chosen['text']
	if 'message' in chosen:
		_text = chosen['message']
	
	if not _text:
		return False
	
	_message = {'sender': life['id'], 'text': _text, 'impact': 1}
	dialog['messages'].append(_message)
	print '%s: %s' % (' '.join(life['name']), _text)

def reset_dialog(dialog):
	_ret = False
	if dialog['previous_topics']:
		dialog['topics'] = dialog['previous_topics'].pop(0)
		dialog['previous_topics'] = []
		_ret = True
	else:
		if not 'player' in LIFE[dialog['sender']]:
			LIFE[dialog['sender']]['dialogs'].remove(dialog)
			
			if dialog in LIFE[dialog['receiver']]['dialogs']:
				LIFE[dialog['receiver']]['dialogs'].remove(dialog)
		else:
			dialog['topics'] = dialog['starting_topics']
	
	dialog['title'] = ''
	dialog['index'] = 0
	
	return _ret

def give_menu_response(life, dialog):
	_chosen = dialog['topics'][dialog['index']]
	
	if _chosen['gist'] == 'ignore_question':
		dialog['question']['ignore'].append(life['id'])
	
	if 'subtopics' in _chosen:
		dialog['previous_topics'].append(dialog['topics'])
		dialog['title'] = _chosen['text']
		dialog['topics'] = _chosen['subtopics'](life, _chosen)
		dialog['index'] = 0
	else:
		add_message(life, dialog, _chosen)
		process_response(LIFE[dialog['receiver']], life, dialog, _chosen)
		modify_trust(LIFE[dialog['sender']], dialog['receiver'], _chosen)
		modify_trust(LIFE[dialog['receiver']], dialog['sender'], _chosen)

def alife_response(life, dialog):
	#List of topics should be fairly relevant if the ALife created the dialog properly.
	#TODO: Score these
	_chosen = random.choice(dialog['topics'])
	
	if 'memory' in _chosen and 'question' in _chosen['memory'] and _chosen['memory']['question']:
		dialog['question'] = _chosen['memory']
	
	#TODO: Too tired :-)
	if 'subtopics' in _chosen:
		dialog['previous_topics'].append(dialog['topics'])
		dialog['title'] = _chosen['text']
		dialog['topics'] = _chosen['subtopics'](life, _chosen)
		dialog['index'] = 0
	else:
		add_message(life, dialog, _chosen)
		process_response(LIFE[dialog['receiver']], life, dialog, _chosen)
		modify_trust(LIFE[dialog['sender']], dialog['receiver'], _chosen)
		modify_trust(LIFE[dialog['receiver']], dialog['sender'], _chosen)

def get_all_relevant_gist_responses(life, target, gist):
	#TODO: We'll definitely need to extend this for fuzzy searching	
	#return [memory for memory in lfe.get_memory(life, matches={'text': gist})]
	_topics = []
	_memories = []
	
	if gist in ['greeting']:
		_topics.append({'text': 'How are you?', 'gist': 'how_are_you'})
		_topics.append({'text': 'I don\'t have time to talk.', 'gist': 'ignore'})
		_topics.append({'text': 'Get out of my face!', 'gist': 'ignore_rude'})
	elif gist == 'questions':
		_topics.extend(get_questions_to_ask(life, {'target': target}))
	
	if _topics and _topics[0]['gist'] == 'end':
		_topics = []
	
	return _topics, _memories

def get_all_relevant_target_topics(life, target):
	_topics = []
	_memories = []
	
	_topics.append({'text': 'What do you do?', 'gist': 'talk_about_self'})
	_topics.append({'text': 'How are you?', 'gist': 'how_are_you', 'like': 1})
	_topics.append({'text': 'What\'s new?', 'gist': 'how_are_you'})
	_topics.append({'text': 'Can I help you with anything?', 'gist': 'offering_help'})
	
	_memories.extend([memory for memory in lfe.get_memory(life, matches={'target': target})])
	
	return _topics, _memories

def get_all_irrelevant_target_topics(life, target):
	_topics = []
	_memories = []
	
	#TODO: This spawns a menu for the player to choose the desired ALife
	_topics.append({'text': 'Do you know...', 'gist': 'inquire_about', 'subtopics': get_known_alife})
	_topics.append({'text': 'Ask about...', 'gist': 'inquire_about_self', 'target': target, 'subtopics': get_possible_alife_questions})
	
	for ai in life['know']:
		if lfe.get_memory(life, matches={'target': ai}):
			_topics.append({'text': 'Did you know...', 'gist': 'tell_about', 'subtopics': tell_about_alife_select})
			break
	
	_memories.extend([memory for memory in lfe.get_memory(life, matches={'target': target})])
	
	return _topics, _memories

def get_possible_alife_questions(life, chosen):
	_topics = []
	
	_topics.append({'text': 'Camps...',
		'gist': 'inquire_about',
		'subtopics': get_known_camps})
	_topics.append({'text': 'What\'s nearby?',
		'gist': 'inquire_about_nearby_locations'})
	
	return _topics

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
			if 'lie' in topic and topic['lie']:
				topic['impact'] = -1
				continue
			
			#logging.warning('\'%s\' was not found in GIST_MAP.' % topic['gist'])
			topic['impact'] = 0
			continue
		
		topic['impact'] = GIST_MAP[topic['gist']]

def format_responses(life, target, responses):
	for entry in responses:
		entry['sender'] = life['id']

def get_known_alife(life, chosen):
	_topics = []
	
	for ai in life['know']:
		_name = ' '.join(LIFE[ai]['name'])
		_topics.append({'text': _name,
			'message': 'Do you know %s?' % _name,
			'gist': chosen['gist'],
			'target': ai})
	
	return _topics

def get_known_locations(life, chosen):
	_topics = []
	
	_topics.extend(get_known_camps(life, chosen, gist='talk_about_camp'))
	
	return _topics

def get_known_camps(life, chosen, gist='inquire_about_camp'):
	_topics = []
	
	#for ai in life['know']:
	for camp in life['known_camps'].values():
		_topics.append({'text': camp['name'],
			'gist': gist,
			'camp': camp['id'],
			'subtopics': get_questions_for_camp})
	
	return _topics

def get_questions_for_camp(life, chosen):
	_topics = []
	
	_topics.append({'text': 'Who founded %s?' % CAMPS[chosen['camp']]['name'],
		'gist': 'inquire_about_camp_founder',
		'camp': chosen['camp']})
	_topics.append({'text': 'What\'s the population of %s?' % CAMPS[chosen['camp']]['name'],
		'gist': 'inquire_about_camp_population',
		'camp': chosen['camp']})
	
	return _topics

def give_camp_founder(life, chosen):
	_topics = []
	
	_lie = True
	if chosen['camp'] in [c['id'] for c in alife.camps.get_founded_camps(life)]:
		_lie = False
	
	_topics.append({'text': 'I don\'t know.', 'gist': 'ignore_question'})
	
	_topics.append({'text': 'I am.',
		'gist': 'tell_about_camp_founder',
		'camp': chosen['camp'],
		'founder': life['id'],
		'like': 1,
		'lie': _lie,
		'from': life['id']})
	
	for ai in life['know']:
		_lie = True
		for memory in lfe.get_memory(life, matches={'text': 'heard about camp', 'camp': chosen['camp'], 'founder': '*'}):
			if memory['founder'] == ai:
				_lie = False
				break
		#if not CAMPS[chosen['camp']]['founder'] == ai:
		#	_lie = True
		
		_name = ' '.join(LIFE[ai]['name'])
		_topics.append({'text': _name,
			'message': '%s is.' % _name,
			'gist': 'tell_about_camp_founder',
			'camp': chosen['camp'],
			'founder': ai,
			'lie': _lie,
			'like': 1,
			'from': life['id']})
		_topics.append({'text': _name,
			'message': '%s is in charge of %s.' % (_name, CAMPS[chosen['camp']]['name']),
			'gist': 'tell_about_camp_founder',
			'camp': chosen['camp'],
			'founder': ai,
			'like': 1,
			'lie': _lie,
			'from': life['id']})
	
	return _topics

def get_questions_to_ask(life, chosen):
	_topics = []
	
	for memory in lfe.get_questions(life, target=chosen['target']):
		if not lfe.can_ask(life, chosen, memory):
			continue
		
		if memory['text'] == 'wants_founder_info':			
			if not lfe.get_memory(life, matches={'text': 'heard about camp', 'camp': memory['camp'], 'founder': '*'}):
				_topics.append({'text': 'Do you know who is in charge of camp %s?' % CAMPS[memory['camp']]['name'],
					'gist': 'who_founded_camp',
					'camp': memory['camp'],
					'memory': memory})
				_topics.append({'text': 'Who runs camp %s?' % CAMPS[memory['camp']]['name'],
					'gist': 'who_founded_camp',
					'camp': memory['camp'],
					'memory': memory})
				_topics.append({'text': 'Any idea who is in charge of camp %s?' % CAMPS[memory['camp']]['name'],
					'gist': 'who_founded_camp',
					'camp': memory['camp'],
					'memory': memory})
				memory['asked'][chosen['target']] = WORLD_INFO['ticks']
		#TODO: Possibly never triggered
		elif memory['text'] == 'help find founder':
			_topics.append({'text': 'Help %s locate the founder of %s.' % (' '.join(LIFE[memory['target']]['name']), CAMPS[memory['camp']]['name']),
				'gist': 'help_find_founder',
				'target': memory['target'],
				'camp': memory['camp'],
				'memory': memory})
			memory['asked'][chosen['target']] = WORLD_INFO['ticks']
	
	if not _topics:
		_topics.append({'text': 'Not really.', 'gist': 'end'})
		_topics.append({'text': 'No.', 'gist': 'end'})
		_topics.append({'text': 'Nope.', 'gist': 'end'})
	
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

def get_responses_about_self(life):
	_responses = []
	
	for camp in alife.camps.get_founded_camps(life):
		_responses.append({'text': 'I\'m the founder of camp %s.' % camp['name'],
			'gist': 'talk_about_camp',
			'camp': camp['id']})
	
	if not _responses:
		_responses.append({'text': 'I don\'t do much.', 'gist': 'nothing'})
	
	return _responses

def get_matching_likes(life, target, gist):
	_knows = alife.brain.knows_alife_by_id(life, target)
	_matching = []
	
	for key in _knows['likes']:
		if key.count('*') and gist.count(key[:len(key)-1]):
			_matching.append(key)
		elif key == gist:
			_matching.append(key)
	
	return _matching

def get_freshness_of_gist(life, target, gist):
	_knows = alife.brain.knows_alife_by_id(life, target)
	_freshness = 0
	
	for key in get_matching_likes(life, target, gist):
		_freshness += _knows['likes'][key][0]
	return _freshness

def modify_trust(life, target, _chosen):
	_knows = alife.brain.knows_alife_by_id(life, target)
	
	if 'like' in _chosen:
		_like = _chosen['like']
		
		for key in get_matching_likes(life, target, _chosen['gist']):
			_like *= _knows['likes'][key][0]
			_knows['likes'][key][0] *= _knows['likes'][key][1]
		
		_knows['trust'] += _like
	elif 'dislike' in _chosen:
		_dislike = _chosen['like']
		_knows['trust'] -= _chosen['dislike']

def alife_choose_response(life, target, dialog, responses):
	_knows = alife.brain.knows_alife_by_id(life, target['id'])
	_score = alife.judgement.judge(life, _knows)
	_choices = [r for r in responses if numbers.clip(_score, -1, 1) >= r['impact']]
	
	for _choice in _choices[:]:
		if 'lie' in _choice:
			if _choice['lie'] and numbers.clip(_knows['trust'], -1, 1)>=0:
				_choices.remove(_choice)
	
	if _choices:
		_chosen = random.choice(_choices)		
		add_message(life, dialog, _chosen)
		
		if _chosen['gist'] == 'ignore_question':
			dialog['question']['ignore'].append(life['id'])
		
		process_response(target, life, dialog, _chosen)
		modify_trust(life, target['id'], _chosen)
		modify_trust(target, life['id'], _chosen)
	else:
		reset_dialog(dialog)
		logging.error('Dialog didn\'t return anything.')

def process_response(life, target, dialog, chosen):
	if chosen['gist'] == 'end':
		reset_dialog(dialog)
		return True
	
	if 'from' in chosen:
		if chosen['from'] == life['id']:
			_receiver = target['id']
		else:
			_receiver = life['id']	
	_responses = []
	
	#TODO: Unused
	if chosen['gist'].count('positive'):
		_impact = 1
	elif chosen['gist'].count('negative'):
		_impact = -1
	else:
		_impact = 0
	
	if chosen['gist'] == 'how_are_you':
		if get_freshness_of_gist(life, target['id'], chosen['gist'])<0.5:
			_responses.append({'text': 'Why do you keep asking me that?', 'gist': 'irritated_neutral'})
			_responses.append({'text': 'Stop asking me that.', 'gist': 'irritated_negative'})
		else:
			_responses.append({'text': 'I\'m doing fine.', 'gist': 'status_response_positive', 'like': 1})
			_responses.append({'text': 'I\'m doing fine.', 'gist': 'status_response_neutral', 'like': 1})
			_responses.append({'text': 'I\'m doing fine, you?', 'gist': 'status_response_neutral_question', 'like': 1})
	elif chosen['gist'] == 'talk_about_self':
		_responses.extend(get_responses_about_self(life))
	elif chosen['gist'] == 'talk_about_camp':
		if lfe.get_memory(life, matches={'text': 'heard about camp', 'camp': chosen['camp']}):
			_responses.append({'text': 'I\'ve heard of it.', 'gist': 'heard_of_camp'})
			_responses.extend(get_questions_for_camp(life, chosen))
		else:
			_responses.append({'text': 'I\'ve never heard of it.', 'gist': 'never_heard_of_camp', 'camp': chosen['camp']})
	elif chosen['gist'].count('heard_of_camp'):
		if chosen['gist'].count('never'):
			if alife.camps.is_in_camp(life, CAMPS[chosen['camp']]):
				_responses.append({'text': 'You\'re in it right now!', 'gist': 'inform_of_camp', 'sender': life['id'], 'camp': chosen['camp'], 'founder': life['id']})
				_responses.append({'text': 'Well, this is it.', 'gist': 'inform_of_camp', 'sender': life['id'], 'camp': chosen['camp'], 'founder': life['id']})
			else:
				_responses.append({'text': 'Come visit sometime!', 'gist': 'inform_of_camp'})
	elif chosen['gist'].count('inform_of_camp'):
		alife.camps.discover_camp(life, CAMPS[chosen['camp']])
		
		lfe.memory(life, 'heard about camp',
			camp=chosen['camp'],
			target=chosen['sender'],
			founder=chosen['founder'])
	elif chosen['gist'] == 'who_founded_camp':
		_responses.extend(give_camp_founder(life, chosen))
	elif chosen['gist'].count('tell_about_camp_founder'):
		_responses.append({'text': 'Thanks!', 'gist': 'nothing', 'like': 1})
		_responses.append({'text': 'Good to know.', 'gist': 'nothing', 'like': 1})
		
		lfe.memory(LIFE[_receiver], 'heard about camp',
			camp=chosen['camp'],
			target=chosen['sender'],
			founder=chosen['founder'])
	elif chosen['gist'] == 'offering_help':
		_responses.extend(get_questions_to_ask(life, chosen))
	elif chosen['gist'].count('status_response'):
		if chosen['gist'].count('question'):
			_responses.append({'text': 'Same.', 'gist': 'status_response', 'like': 1})
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
	elif chosen['gist'] == 'inquire_about_nearby_locations':
		_responses.extend(get_known_locations(life, chosen))
	elif chosen['gist'].count('inquire_response'):
		#TODO: How about something similar to get_known_life()?
		#TODO: Or just a way to trigger a submenu response from a gist?
		if chosen['gist'].count('knows'):
			_responses.append({'text': 'Where was the last place you saw him?', 'gist': 'last_seen_target_at', 'target': chosen['target']})
	elif chosen['gist'] == 'last_seen_target_at':
		if lfe.can_see(life, LIFE[chosen['target']]['pos']):
			_responses.append({'text': 'He\'s right over there.', 'gist': 'saw_target_at', 'target': chosen['target']})
		elif _impact>=0:
			_responses.append({'text': 'Last place I saw him was...', 'gist': 'saw_target_at', 'target': chosen['target']})
		else:
			_responses.append({'text': 'Not telling you!', 'gist': 'saw_target_at'})
	else:
		logging.error('Gist \'%s\' did not generate any responses.' % chosen['gist'])
	
	if not 'player' in life and not _responses:
		_responses.append({'text': '', 'gist': 'end'})
	
	calculate_impacts(life, target, _responses)
	format_responses(life, target, _responses)
	
	if 'player' in life:
		if _responses and not _responses[0]['gist'] == 'end':
			dialog['topics'] = _responses
			dialog['index'] = 0
		else:
			reset_dialog(dialog)
			
		return True
	
	alife_choose_response(life, target, dialog, _responses)

def draw_dialog():
	if not lfe.has_dialog(SETTINGS['controlling']):
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

