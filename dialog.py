#A note before we start...
#It's impossible to summarize conversations into a single word,
#so we'll be passing around dictionaries that contain details
#of it so we can perform fuzzy matches across memories when
#finding responses.

from globals import *

import life as lfe
import libtcodpy as tcod

import numbers
import logic
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
	
	if not alife.brain.knows_alife_by_id(life, target):
		alife.brain.meet_alife(life, target)
	
	if not alife.brain.knows_alife(LIFE[target], life):
		alife.brain.meet_alife(LIFE[target], life)
	
	_dialog = {'enabled': True,
		'title': '',
		'sender': life['id'],
		'receiver': target,
		'speaker': life['id'],
		'listener': target,
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
	#print '%s: %s' % (' '.join(life['name']), _text)

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
			
			logging.warning('\'%s\' was not found in GIST_MAP.' % topic['gist'])
			topic['impact'] = 0
			continue
		
		topic['impact'] = GIST_MAP[topic['gist']]

def reset_dialog(dialog, end=True):
	_ret = False
	if dialog['previous_topics']:
		dialog['topics'] = dialog['previous_topics'].pop(0)
		dialog['previous_topics'] = []
		_ret = True
	else:
		if 'player' in LIFE[dialog['sender']] and dialog['starting_topics']:
			dialog['topics'] = dialog['starting_topics']
			dialog['speaker'] = dialog['sender']
		elif end:
			LIFE[dialog['sender']]['dialogs'].remove(dialog)
			
			if dialog in LIFE[dialog['receiver']]['dialogs']:
				LIFE[dialog['receiver']]['dialogs'].remove(dialog)
	
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

def alife_response(life, dialog):
	#List of topics should be fairly relevant if the ALife created the dialog properly.
	#TODO: Score these
	_chosen = random.choice(dialog['topics'])
	
	if 'memory' in _chosen and 'question' in _chosen['memory'] and _chosen['memory']['question']:
		dialog['question'] = _chosen['memory']
	
	if _chosen['gist'] == 'ignore_question':
		dialog['question']['ignore'].append(life['id'])
	
	#TODO: Too tired :-)
	if 'subtopics' in _chosen:
		dialog['previous_topics'].append(dialog['topics'])
		dialog['title'] = _chosen['text']
		dialog['topics'] = _chosen['subtopics'](life, _chosen)
		dialog['index'] = 0
	else:
		add_message(life, dialog, _chosen)
		process_response(LIFE[dialog['receiver']], life, dialog, _chosen)
		#modify_trust(LIFE[dialog['sender']], dialog['receiver'], _chosen)
		#modify_trust(LIFE[dialog['receiver']], dialog['sender'], _chosen)

def tick(life, dialog):
	if not dialog['speaker'] == life['id']:
		return False
	
	alife_response(life, dialog)

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
	elif gist == 'jobs':
		_topics.append({'text': 'Do you have any jobs?', 'gist': 'ask_for_jobs'})
	elif gist == 'introduction':
		_topics.append({'text': 'What do you do?', 'gist': 'talk_about_self'})
	
	if _topics and _topics[0]['gist'] == 'end':
		_topics = []
	
	return _topics, _memories

def get_all_relevant_target_topics(life, target):
	_topics = []
	_memories = []
	
	_topics.append({'text': 'What do you do?', 'gist': 'talk_about_self'})
	_topics.append({'text': 'Start conflict', 'gist': 'ignore_question_negative', 'dislike': 1})
	_topics.append({'text': 'How are you?', 'gist': 'how_are_you', 'like': 1})
	_topics.append({'text': 'What\'s new?', 'gist': 'how_are_you'})
	_topics.append({'text': 'Can I help you with anything?', 'gist': 'offering_help'})
	_topics.append({'text': 'Do you have any jobs?', 'gist': 'ask_for_jobs'})
	
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
	#_topics.append({'text': 'You think I\'d tell you that?', 'gist': 'ignore_question_negative'})
	
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
	_target = None
	_escape = False
	
	if 'target' in chosen:
		_target = chosen['target']
	
	for memory in lfe.get_questions(life, target=_target):
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
				
				if 'target' in chosen:
					memory['asked'][chosen['target']] = WORLD_INFO['ticks']
		#TODO: Possibly never triggered
		elif memory['text'] == 'help find founder':
			_topics.append({'text': 'Help %s locate the founder of %s.' % (' '.join(LIFE[memory['target']]['name']), CAMPS[memory['camp']]['name']),
				'gist': 'help_find_founder',
				'target': memory['target'],
				'camp': memory['camp'],
				'memory': memory})
			
			if 'target' in chosen:
				memory['asked'][chosen['target']] = WORLD_INFO['ticks']
		elif memory['text'] == 'where_is_target':
			_topics.append({'text': 'Do you know where %s is?' % ' '.join(LIFE[memory['target']]['name']),
				'gist': 'last_seen_target_at',
				'target': memory['target'],
				'memory': memory})
			
			if 'target' in chosen:
				memory['asked'][chosen['target']] = WORLD_INFO['ticks']
		elif memory['text'] == 'wants item':
			#TODO: Better description
			_topics.append({'text': 'Do you have anything like this?',
				'gist': 'request_item',
				'item': memory['item']})
			
			if 'target' in chosen:
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

def get_jobs(life, chosen):
	_topics = []
	
	if life['camp'] in [c['id'] for c in alife.camps.get_founded_camps(life)]:
		for job in alife.camps.get_camp_jobs(life['camp']):			
			_topics.append({'text': job['description'],
				'gist': 'offer_job',
				'job': job})
	
	if not _topics:
		_topics.append({'text': 'I don\'t have any jobs.', 'gist': 'no_jobs'})
	
	return _topics

def get_responses_about_self(life):
	_responses = []
	
	for camp in alife.camps.get_founded_camps(life):
		_responses.append({'text': 'I\'m the founder of camp %s.' % camp['name'],
			'gist': 'talk_about_camp',
			'camp': camp['id']})
	
	if not _responses:
		if life['job']:
			_responses.append({'text': life['job']['description'], 'gist': 'nothing'})
		else:
			_responses.append({'text': 'I don\'t do much.', 'gist': 'nothing'})
	
	return _responses

def get_items_to_give(life, target, matches={}):
	_responses = []
	_matching = lfe.get_all_inventory_items(life, matches=[matches])
	
	for item in _matching:
		#TODO: Don't break out of the loop just because we're dropping an item
		if lfe.find_action(life, matches=[{'action': 'dropitem'}]):
			break
		
		_matches = alife.survival.is_in_need_matches(life, item)
		_break = False
		if not 'player' in life:
			for _match in _matches:
				if _match['num_met']<=_match['min_matches']:
					_break = True
					break
		
		if _break:
			continue
		
		_responses.append({'text': 'Take this %s!' % item['name'], 'gist': 'give_item_to', 'target': target, 'item': item['id'], 'like': 1})
	
	#TODO: Potential conflict 
	_responses.append({'text': 'I don\'t have anything.', 'gist': 'nothing'})
	
	#TODO: More recent memories should be weighed higher
	for heard_about_item in lfe.get_memory(life, matches={'text': 'heard about an item'}):		
		if heard_about_item['target'] == target:
			continue
		
		#TODO: Even though the item doesn't exist, we still can't confirm if the item is gone or not
		if not heard_about_item['item'] in ITEMS:
			continue
		
		_item = ITEMS[heard_about_item['item']]
		#_break = False
		#for key in matches:
		#	if not key in _item or not _item[key] == matches[key]:
		#		_break = True
		#		break
		#
		#if _break:
		#	continue
		if not logic.matches(_item, matches):
			continue
		
		_ask_alife = LIFE[heard_about_item['target']]
		_responses.append({'text': 'Try asking %s.' % ' '.join(_ask_alife['name']), 'gist': 'ask_alife', 'target': _ask_alife['id'], 'like': 1})
	
	return _responses

def get_matching_likes(life, target, gist):
	_knows = alife.brain.knows_alife_by_id(life, target)
	_matching = []
	
	if not _knows:
		logging.error('%s does not know target.' % ' '.join(life['name']))
		return []
	
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

def modify_trust(life, target, chosen):
	_knows = alife.brain.knows_alife_by_id(life, target)
	
	if 'like' in chosen:
		_like = chosen['like']
		
		for key in get_matching_likes(life, target, chosen['gist']):
			_like *= _knows['likes'][key][0]
			_knows['likes'][key][0] *= _knows['likes'][key][1]
		
		if not lfe.find_action(life, matches=[{'text': chosen['gist'], 'target': target}]):
			lfe.memory(life, chosen['gist'], trust=chosen['like'], target=target)
		#_knows['trust'] += _like
	elif 'dislike' in chosen:
		if not lfe.find_action(life, matches=[{'text': chosen['gist'], 'target': target}]):
			lfe.memory(life, chosen['gist'], trust=-chosen['dislike'], target=target)

def alife_choose_response(life, target, dialog, responses):
	if not alife.brain.knows_alife(life, target):
		alife.brain.meet_alife(life, target)
	
	_knows = alife.brain.knows_alife(life, target)
	_score = alife.judgement.judge(life, _knows['life']['id'])
	_choices = [r for r in responses]# if numbers.clip(_score, -1, 1) >= r['impact']]
	
	for _choice in _choices[:]:
		if 'lie' in _choice:
			if _choice['lie'] and numbers.clip(alife.judgement.get_trust(life, target['id']), -1, 1)>=0:
				_choices.remove(_choice)
	
	if _choices:
		_chosen = random.choice(_choices)		
		add_message(life, dialog, _chosen)
		
		if _chosen['gist'] == 'ignore_question':
			if 'question' in dialog:
				dialog['question']['ignore'].append(life['id'])
		
		process_response(target, life, dialog, _chosen)
	else:
		reset_dialog(dialog)
		logging.error('Dialog didn\'t return anything.')

def process_response(life, target, dialog, chosen):
	if chosen['gist'] in ['end', 'nothing']:
		reset_dialog(dialog, end=True)
		return True
	
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
		lfe.memory(LIFE[dialog['speaker']], 'met', target=dialog['listener'])
	elif chosen['gist'] == 'talk_about_self':
		_responses.extend(get_responses_about_self(life))
		lfe.memory(LIFE[dialog['speaker']], 'met', target=dialog['listener'])
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
				#TODO: This right?
				_responses.append({'text': 'Come visit sometime!', 'gist': 'inform_of_camp', 'camp': chosen['camp'],  'founder': life['id']})
	elif chosen['gist'].count('inform_of_camp'):
		if chosen['camp']:
			alife.camps.discover_camp(life, CAMPS[chosen['camp']])
			
			lfe.memory(LIFE[dialog['listener']], 'heard about camp',
				camp=chosen['camp'],
				target=chosen['sender'],
				founder=chosen['founder'])
	elif chosen['gist'] == 'who_founded_camp':
		_responses.extend(give_camp_founder(life, chosen))
	elif chosen['gist'].count('tell_about_camp_founder'):
		_responses.append({'text': 'Thanks!', 'gist': 'nothing', 'like': 1})
		_responses.append({'text': 'Good to know.', 'gist': 'nothing', 'like': 1})
		
		lfe.memory(LIFE[dialog['listener']], 'heard about camp',
			camp=chosen['camp'],
			target=chosen['sender'],
			founder=chosen['founder'])
	elif chosen['gist'] == 'offering_help':
		_responses.extend(get_questions_to_ask(life, chosen))
	elif chosen['gist'] == 'ask_for_jobs':
		_responses.extend(get_jobs(life, chosen))
	elif chosen['gist'] == 'offer_job':
		alife.jobs.add_job_candidate(chosen['job'], LIFE[dialog['listener']])
		alife.jobs.process_job(chosen['job'])
	elif chosen['gist'] == 'no_jobs':
		_responses.append({'text': 'Okay.', 'gist': 'end'})
		
		lfe.memory(LIFE[dialog['listener']], 'no jobs',
			target=dialog['speaker'])
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
	elif chosen['gist'] == 'inquire_about_camp_founder':
		_responses.extend(give_camp_founder(life, chosen))
	elif chosen['gist'].count('inquire_response'):
		#TODO: How about something similar to get_known_life()?
		#TODO: Or just a way to trigger a submenu response from a gist?
		if chosen['gist'].count('knows'):
			_responses.append({'text': 'Where was the last place you saw him?', 'gist': 'last_seen_target_at', 'target': chosen['target']})
	elif chosen['gist'] == 'last_seen_target_at':
		if alife.sight.can_see_target(life, chosen['target']):
			_responses.append({'text': 'He\'s right over there.', 'gist': 'saw_target_at', 'target': chosen['target'], 'location': LIFE[chosen['target']]['pos'][:]})
		elif _impact>=0:
			_knows = alife.brain.knows_alife_by_id(life, chosen['target'])
			
			if _knows:
				_responses.append({'text': 'Last place I saw him was...', 'gist': 'saw_target_at', 'target': chosen['target'], 'location': _knows['last_seen_at'][:]})
			else:
				_responses.append({'text': 'I don\'t know.', 'gist': 'nothing'})
		else:
			#TODO: Potential conflict 
			_responses.append({'text': 'Not telling you!', 'gist': 'saw_target_at'})
	elif chosen['gist'] == 'saw_target_at':
		lfe.memory(LIFE[dialog['listener']], 'location_of_target',
			target=chosen['target'],
			location=chosen['location'])
	elif chosen['gist'] == 'request_item':
		_responses.extend(get_items_to_give(LIFE[dialog['listener']], dialog['speaker'], matches=chosen['item']))
	elif chosen['gist'] == 'give_item_to':
		#TODO: Write lfe.drop_item_for()
		lfe.add_action(life, {'action': 'dropitem',
			'item': chosen['item']},
			200,
			delay=lfe.get_item_access_time(life, chosen['item']))
	elif chosen['gist'] == 'ignore_question_negative':
		_knows = alife.brain.knows_alife_by_id(LIFE[dialog['listener']], dialog['speaker'])
		lfe.memory(LIFE[dialog['listener']], 'bad answer',
			target=dialog['speaker'],
		    danger=3)
		
		#TODO: Start dialog that can lead to more distrust
		#if _knows['trust']<=0:
		#	lfe.memory(LIFE[dialog['listener']], 'location_of_target',
		#		target=chosen['target'],
		#		location=chosen['location'])
		
	elif not chosen['gist'] in ['nothing', 'end', 'ignore_question']:
		logging.error('Gist \'%s\' did not generate any responses.' % chosen['gist'])
	
	if not 'player' in life and not _responses:
		_responses.append({'text': '', 'gist': 'end'})
	
	calculate_impacts(life, target, _responses)
	format_responses(life, target, _responses)
	
	#if 'like' in chosen and not lfe.find_action(LIFE[dialog['speaker']], matches=[{'text': chosen['gist'], 'target': dialog['listener']}]):
	#	lfe.memory(LIFE[dialog['speaker']], chosen['gist'], trust=chosen['like'], target=dialog['listener'])
	
	#if 'like' in chosen and not lfe.find_action(LIFE[dialog['listener']], matches=[{'text': chosen['gist'], 'target': dialog['speaker']}]):
	#	lfe.memory(LIFE[dialog['listener']], chosen['gist'], trust=chosen['like'], target=dialog['speaker'])
	
	modify_trust(LIFE[dialog['speaker']], dialog['listener'], chosen)
	modify_trust(LIFE[dialog['listener']], dialog['speaker'], chosen)
	lfe.create_and_update_self_snapshot(LIFE[dialog['speaker']])
	lfe.create_and_update_self_snapshot(LIFE[dialog['listener']])
	
	_speaker = dialog['speaker']
	_listener = dialog['listener']
	dialog['speaker'] = _listener
	dialog['listener'] = _speaker
	
	if 'player' in  life:
		_single_responses = {}
		for _response in _responses:
			if not _response['text'] in _single_responses:
				_single_responses[_response['text']] = _response
				continue
			
			if random.randint(0, 1):
				_single_responses[_response['text']] = _response
			
		_responses = _single_responses.values()
		if _responses and not _responses[0]['gist'] in ['nothing', 'end']:
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
		dialog['console'] = tcod.console_new(WINDOW_SIZE[0], 40)
	else:
		tcod.console_rect(dialog['console'], 0, 0, WINDOW_SIZE[0], 40, True, flag=tcod.BKGND_DEFAULT)

	#TODO: Too tired to do this... :-)
	_index = -1
	_y = 2
	
	if dialog['title']:
		tcod.console_print(dialog['console'],
			1,
			1,
			dialog['title'])
	
	tcod.console_set_default_background(dialog['console'], tcod.black)
	for d in dialog['topics']:
		line = d['text']
		_index += 1
		_x = 1
		
		if not 'impact' in d:
			tcod.console_set_default_foreground(dialog['console'], tcod.white)
		elif d['impact'] == 1:
			tcod.console_set_default_foreground(dialog['console'], tcod.green)
		elif not d['impact']:
			tcod.console_set_default_foreground(dialog['console'], tcod.white)
		else:
			tcod.console_set_default_foreground(dialog['console'], tcod.red)
		
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
				tcod.console_print(dialog['console'],
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
				tcod.console_set_default_foreground(dialog['console'], tcod.black)
				tcod.console_set_default_background(dialog['console'], tcod.green)
				tcod.console_set_background_flag(dialog['console'], tcod.BKGND_SET)
			elif not _impact:
				tcod.console_set_default_foreground(dialog['console'], tcod.white)
				tcod.console_set_default_background(dialog['console'], tcod.black)
				tcod.console_set_background_flag(dialog['console'], tcod.BKGND_SET)
			else:
				tcod.console_set_default_foreground(dialog['console'], tcod.black)
				tcod.console_set_default_background(dialog['console'], tcod.red)
				tcod.console_set_background_flag(dialog['console'], tcod.BKGND_SET)
			
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
					tcod.console_print(dialog['console'],
						_x+_i,
						_y,
						txt)
					
					_i += 1
					_y += 1
				
				_x += 1
				_y += 1
				
				break
	
	tcod.console_set_background_flag(dialog['console'], tcod.BKGND_NONE)

