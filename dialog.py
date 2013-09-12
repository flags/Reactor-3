from globals import *

import libtcodpy as tcod
import graphics as gfx
import life as lfe

import numbers
import logic
import alife

import logging
import random

def create_dialog_with(life, target, info, question=None):
	_messages = []
	
	if question:
		_topics = _get_questions_to_ask(life, target, question)
		_memories = []
	elif 'gist' in info:
		_topics, _memories = get_all_relevant_gist_responses(life, target, info['gist'])					
	else:
		_topics, _memories = get_all_relevant_target_topics(life, target)
		_t, _m = get_all_irrelevant_target_topics(life, target)
		_topics.extend(_t)
		_memories.extend(_m)
	
	if not _topics:
		return False
	
	calculate_impacts(life, target, _topics)
	
	#It happens... although hopefully this is handled by sounds
	if not alife.brain.knows_alife_by_id(life, target):
		alife.brain.meet_alife(life, LIFE[target])
	
	if not alife.brain.knows_alife(LIFE[target], life):
		alife.brain.meet_alife(LIFE[target], life)
	
	_dialog = {'enabled': True,
		'title': 'Talk',
		'creator': life['id'],
		'target': target,
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
	
	if 'impact' in chosen:
		_message = {'sender': life['id'], 'text': _text, 'impact': chosen['impact']}
	else:
		_message = {'sender': life['id'], 'text': _text, 'impact': 1}
		logging.warning('Known issue: No impact set for this phrase.')
	
	dialog['messages'].append(_message)
	
def show_messages(dialog):
	for mesg in dialog['messages']:
		print mesg

def calculate_impacts(life, target, topics):
	for topic in topics:
		if 'subtopic' in topic:
			continue
		
		if 'negative' in topic['gist'] or 'lie' in topic and topic['lie'] or 'dislike' in topic:
			topic['impact'] = -1
		elif 'positive' in topic['gist'] or 'like' in topic:
			topic['impact'] = 1
		else:
			topic['impact'] = 0

def reset_dialog(dialog, end=True, force=False):
	_ret = False

	if end:
		if not force and 'player' in LIFE[dialog['creator']] and dialog['starting_topics'] and not 'gist' in dialog['info'] and not dialog['title'] == 'Talk':
			dialog['topics'] = dialog['starting_topics']
			dialog['listener'] = dialog['target']
			dialog['speaker'] = dialog['creator']
			dialog['title'] = 'Talk'
			dialog['index'] = 0
			
			return True
		
		LIFE[dialog['creator']]['dialogs'].remove(dialog)
		
		if dialog in LIFE[dialog['target']]['dialogs']:
			LIFE[dialog['target']]['dialogs'].remove(dialog)	
	
	if dialog['previous_topics']:
		dialog['topics'] = dialog['previous_topics'].pop(0)
		dialog['previous_topics'] = []
		_ret = True
	else:
		if 'player' in LIFE[dialog['creator']] and dialog['starting_topics']:
			dialog['topics'] = dialog['starting_topics']
			dialog['speaker'] = dialog['creator']
			dialog['listener'] = dialog['target']
	
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
		dialog['title'] = 'Answer'
		add_message(life, dialog, _chosen)
		
		process_response(LIFE[dialog['listener']], LIFE[dialog['speaker']], dialog, _chosen)

def alife_response(life, dialog):
	_target = dialog['listener']
	_knows = alife.brain.knows_alife_by_id(life, _target)
	_score = alife.judgement.judge(life, _knows['life']['id'])
	_choices = [r for r in dialog['topics']]
		
	for _choice in _choices[:]:
		if 'lie' in _choice:
			if _choice['lie'] and alife.judgement.can_trust(life, target):
				_choices.remove(_choice)
	
	if not _choices:
		reset_dialog(dialog)
		logging.error('Dialog didn\'t return anything.')
		return False
	
	if alife.stats.is_compatible_with(life, _target):
		_target_impact = 1
	elif alife.judgement.can_trust(life, _target):
		_target_impact = 0
	else:
		_target_impact = -1
	
	_preferred_dialog_choices = []
	_acceptable_dialog_choices = []
	for choice in _choices:
		if choice['impact']==0 and (_target_impact==1 or _target_impact==-1):
			_acceptable_dialog_choices.append(choice)
		elif choice['impact'] == _target_impact:
			_preferred_dialog_choices.append(choice)
	
	if _preferred_dialog_choices:
		_chosen = random.choice(_preferred_dialog_choices)
	elif _acceptable_dialog_choices:
		_chosen = random.choice(_acceptable_dialog_choices)
	else:
		raise Exception('No valid dialog choices for target impact %s: %s' % (_target_impact, _choices))
	
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
		process_response(LIFE[_target], life, dialog, _chosen)

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
	elif gist == 'form_group':
		_topics.append({'text': 'What\'s this about the group?', 'gist': 'ask_about_group'})
	elif gist == 'introduction':
		_topics.append({'text': 'What do you do?', 'gist': 'talk_about_self', 'like': 1})
	elif gist == 'introduction_negative':
		_topics.append({'text': 'I\'m not interested in talking.', 'gist': 'introduction_ignore'})
		_topics.append({'text': 'Why don\'t you go bother someone else?', 'gist': 'introduction_negative', 'dislike': 1})
	elif gist == 'invite_to_group':
		_topics.append({'text': 'I\'m getting a squad together. Want in?', 'gist': 'invite_to_group', 'group': life['group']})
	elif gist == 'call_accepted':
		_topics.append({'text': 'What can I help you with?', 'gist': 'call_topics'})
	elif gist == 'encounter':
		_topics.append({'text': 'Leave! I\'m not looking for company!', 'gist': 'encounter-leave', 'dislike': 1, 'danger': 3})
		_topics.append({'text': 'What are you doing around here?', 'gist': 'encounter-question'})
	
	if _topics and _topics[0]['gist'] == 'end':
		_topics = []
	
	return _topics, _memories

def get_all_relevant_target_topics(life, target):
	_topics = []
	_memories = []
	
	_topics.append({'text': 'What do you do?', 'gist': 'talk_about_self', 'like': 1})
	_topics.append({'text': 'Start conflict', 'gist': 'ignore_question_negative', 'dislike': 1})
	_topics.append({'text': 'How are you?', 'gist': 'how_are_you', 'like': 1})
	_topics.append({'text': 'What\'s new?', 'gist': 'how_are_you'})
	_topics.append({'text': 'Can I help you with anything?', 'gist': 'offering_help'})
	_topics.append({'text': 'Do you have any jobs?', 'gist': 'ask_for_jobs'})
	
	if life['group']:
		if LIFE[target]['group'] == life['group']:
			if alife.groups.is_leader(life['group'], target):
				_topics.append({'text': 'Where\'s our camp?', 'message': 'Where is camp?', 'gist': 'inquire_about_group_camp', 'group': life['group']})
			
			if life['job']:
				_topics.append({'text': 'Recruit for job', 'message': 'I could use your help with this job.', 'gist': 'recruit_for_job', 'job': life['job']})
		else:
			_topics.append({'text': 'Recruit...', 'message': 'Are you looking for a squad?', 'gist': 'inquire_about_group_work', 'group': life['group']})
	
	_memories.extend([memory for memory in lfe.get_memory(life, matches={'target': target})])
	
	return _topics, _memories

def get_all_irrelevant_target_topics(life, target):
	_topics = []
	_memories = []
	
	#TODO: This spawns a menu for the player to choose the desired ALife
	_topics.append({'text': 'Do you know...', 'gist': 'inquire_about', 'subtopics': get_known_alife})
	_topics.append({'text': 'Ask about...', 'gist': 'inquire_about_self', 'target': target, 'subtopics': get_possible_alife_questions})
	_topics.append({'text': 'Request...', 'gist': 'request', 'target': target, 'subtopics': get_requests})
	
	for ai in life['know']:
		if lfe.get_memory(life, matches={'target': ai}):
			_topics.append({'text': 'Did you know...', 'gist': 'tell_about', 'subtopics': tell_about_alife_select})
			break
	
	_memories.extend([memory for memory in lfe.get_memory(life, matches={'target': target})])
	
	return _topics, _memories

def get_possible_alife_questions(life, chosen):
	_topics = []
	
	_topics.append({'text': 'Groups...',
	                'gist': 'inquire_about',
	                'subtopics': get_known_groups})
	#_topics.append({'text': 'Camps...',
	#	'gist': 'inquire_about',
	#	'subtopics': get_known_camps})
	#_topics.append({'text': 'What\'s nearby?',
	#	'gist': 'inquire_about_nearby_locations'})
	
	return _topics

def get_requests(life, chosen):
	_topics = []
	
	_topics.append({'text': 'Do you have any food?', 'gist': 'request_item', 'item': {'type': 'food'}})
	_topics.append({'text': 'Do you have anything to drink?', 'gist': 'request_item', 'item': {'type': 'drink'}})
	
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

def get_known_groups(life, chosen):
	_topics = []
	
	for group in life['known_groups']:
		_topics.append({'text': group,
		                'gist': 'ask_about_group',
		                'group': group,
		                'subtopics': get_questions_for_group})
	
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

def get_questions_for_group(life, chosen):
	_topics = []
	
	_topics.append({'text': 'Who is in charge of group %s?' % chosen['group'],
		'gist': 'ask_about_group_founder',
		'group': chosen['group']})
	
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

def _get_questions_to_ask(life, target, memory):
	_topics = []
	
	if not lfe.can_ask(life, target, memory['id']):
		return []
	
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
			
			if target:
				memory['asked'][target] = WORLD_INFO['ticks']
	#TODO: Possibly never triggered
	elif memory['text'] == 'help find founder':
		_topics.append({'text': 'Help %s locate the founder of %s.' % (' '.join(LIFE[memory['target']]['name']), CAMPS[memory['camp']]['name']),
	          'gist': 'help_find_founder',
	          'target': memory['target'],
	          'camp': memory['camp'],
	          'memory': memory})
		
		if target:
			memory['asked'][target] = WORLD_INFO['ticks']
	elif memory['text'] == 'where_is_target':
		_topics.append({'text': 'Do you know where %s is?' % ' '.join(LIFE[memory['target']]['name']),
	          'gist': 'last_seen_target_at',
	          'target': memory['target'],
	          'memory': memory})
		
		if target:
			memory['asked'][target] = WORLD_INFO['ticks']
	elif memory['text'] == 'wants item':
		#TODO: Better description
		_topics.append({'text': 'Do you have anything like this?',
	          'gist': 'request_item',
	          'item': memory['item']})
		
		if target:
			memory['asked'][target] = WORLD_INFO['ticks']
	elif memory['text'] == 'ask_to_join_camp':
		_topics.append({'text': 'Is it okay if I join this camp?',
	          'gist': 'ask_to_join_camp',
	          'camp': memory['camp'],
	          'memory': memory})
		
		if target:
			memory['asked'][target] = WORLD_INFO['ticks']
	elif memory['text'] == 'opinion_of_target':
		_topics.append({'text': 'What is your relationship with %s?' % ' '.join(LIFE[memory['who']]['name']),
	          'gist': 'opinion_of_target',
	          'who': memory['who'],
	          'memory': memory})
		
		if target:
			memory['asked'][target] = WORLD_INFO['ticks']	
	
	return _topics

def get_questions_to_ask(life, chosen):
	_topics = []
	_target = None
	_escape = False
	
	if 'target' in chosen:
		_target = chosen['target']
	else:
		_target = None
	
	for memory in lfe.get_questions(life, target=_target):
		_topics.extend(_get_questions_to_ask(life, _target, memory))
	
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
	#if life['camp'] in [c['id'] for c in alife.camps.get_founded_camps(life)]:
	#	for job in alife.camps.get_camp_jobs(life['camp']):			
	#		_topics.append({'text': job['description'],
	#			'gist': 'offer_job',
	#			'job': job})
	
	if not _topics:
		if life['known_camps']:
			_topics.append({'text': 'I don\'t have any jobs.', 'gist': 'no_jobs'})
		else:
			_topics.append({'text': 'I\'m still looking for a place to camp.', 'gist': 'no_jobs'})
	
	return _topics

def get_responses_about_self(life):
	_responses = []
	
	_leader = alife.groups.is_leader_of_any_group(life)
	if _leader:
		_responses.append({'text': 'I\'m in charge of a group.', 'gist': 'tell_about_group', 'group': life['group']})
	
	if not _responses:
		if life['job']:
			_responses.append({'text': alife.jobs.get_job(life['job'])['description'], 'gist': 'nothing'})
		else:
			_responses.append({'text': 'I don\'t do much.', 'gist': 'nothing'})
	
	if 'player' in life:
		_responses.append({'text': 'I don\'t do much. What do you do?', 'gist': 'talk_about_self'})
	
	return _responses

def get_items_to_give(life, target, matches={}):
	_responses = []
	_matching = lfe.get_all_inventory_items(life, matches=[matches])
	
	for item in _matching:		
		_matches = alife.survival.is_in_need_matches(life, item)
		_break = False
		if not 'player' in life:
			for _match in _matches:
				if _match['num_above_needed']<=_match['min_matches']:
					_break = True
					break
		
		if _break:
			continue
		
		print 'ITEM!!!!'
		_responses.append({'text': 'Take this %s!' % item['name'],
		                   'gist': 'give_item_to',
		                   'target': target,
		                   'item': item['uid'],
		                   'like': 1})
	
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
		if not alife.judgement.can_trust(life, target):
			return False
		
		_like = chosen['like']
		
		for key in get_matching_likes(life, target, chosen['gist']):
			_like *= _knows['likes'][key][0]
			_knows['likes'][key][0] *= _knows['likes'][key][1]
		
		if not lfe.find_action(life, matches=[{'text': chosen['gist'], 'target': target}]):
			lfe.memory(life, chosen['gist'], trust=chosen['like'], target=target)
		
	elif 'dislike' in chosen:
		if not lfe.find_action(life, matches=[{'text': chosen['gist'], 'target': target}]):
			lfe.memory(life, chosen['gist'], trust=-chosen['dislike'], target=target)
	
	if 'danger' in chosen:
		lfe.memory(life, chosen['gist']+'_danger', danger=chosen['danger'], target=target)

def process_response(life, target, dialog, chosen):
	#LIFE = listener, the one processing these gists
	#TARGET = speaker
	if chosen['gist'] in ['end', 'nothing']:
		reset_dialog(dialog, end=True)
		return True
	
	_responses = []
	
	if chosen['gist'] == 'how_are_you':
		if get_freshness_of_gist(LIFE[dialog['listener']], dialog['speaker'], chosen['gist'])<0.5:
			_responses.append({'text': 'Why do you keep asking me that?', 'gist': 'irritated_neutral'})
			_responses.append({'text': 'Stop asking me that.', 'gist': 'irritated_negative'})
		else:
			_responses.append({'text': 'I\'m doing fine.', 'gist': 'status_response_positive', 'like': 1})
			_responses.append({'text': 'I\'m doing fine.', 'gist': 'status_response_neutral'})
			_responses.append({'text': 'I\'m doing fine, you?', 'gist': 'status_response_neutral_question', 'like': 1})
			_responses.append({'text': 'Why do you care?', 'gist': 'status_response_negative'})
		lfe.memory(LIFE[dialog['speaker']], 'met', target=dialog['listener'])
	elif chosen['gist'] == 'introduction_negative':
		if 'player' in life:
			gfx.message('%s ignores you.')
		
		lfe.memory(life, 'met', target=dialog['listener'])
		lfe.memory(target, 'met', target=dialog['listener'])
	elif chosen['gist'] == 'talk_about_self':
		if 'player' in life:
			_responses.extend(get_responses_about_self(life))
			_responses.append({'text': 'Why would I tell you?', 'gist': 'okay', 'dislike': 1})
		else:
			if alife.stats.is_compatible_with(target, life['id']):
				_responses.extend(get_responses_about_self(life))
			else:
				_responses.append({'text': 'Why would I tell you?', 'gist': 'okay', 'dislike': 1})
				_responses.append({'text': 'I think you\'re better off not knowing.', 'gist': 'okay'})
		
		lfe.memory(life, 'met', target=dialog['listener'])
		lfe.memory(target, 'met', target=dialog['listener'])
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
		_jobs = alife.groups.get_jobs(LIFE[dialog['listener']]['group'])
		
		if _jobs:
			_responses.append({'text': 'I could use your help...', 'gist': 'show_jobs', 'jobs': _jobs})
		else:
			_responses.append({'text': 'I don\'t have anything for you.', 'gist': 'nothing'})
	elif chosen['gist'] == 'show_jobs':
		for job in chosen['jobs']:
			_responses.append({'text': alife.jobs.get_job(job)['description'], 'gist': 'take_job', 'job': job, 'like': 1})
	elif chosen['gist'] == 'take_job':
		alife.jobs.add_job_candidate(chosen['job'], dialog['speaker'])
		reset_dialog(dialog, end=True, force=True)
		return True
	elif chosen['gist'] == 'offer_job':
		alife.jobs.add_job_candidate(chosen['job'], LIFE[dialog['speaker']])
		alife.jobs.process_job(chosen['job'])
	elif chosen['gist'] == 'no_jobs':
		_responses.append({'text': 'Okay.', 'gist': 'end'})
		
		lfe.memory(LIFE[dialog['listener']], 'no jobs',
			target=dialog['speaker'])
	elif chosen['gist'] == 'status_response_negative':
		_responses.append({'text': 'Okay.', 'gist': 'end'})
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
		elif alife.judgement.can_trust(life, chosen['target'])>=0:
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
		lfe.add_action(LIFE[dialog['speaker']], {'action': 'dropitem',
			'item': chosen['item']},
			200,
			delay=lfe.get_item_access_time(LIFE[dialog['speaker']], chosen['item']))
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
	elif chosen['gist'] == 'invite_to_group':
		if 'player' in LIFE[dialog['listener']]:
			_responses.append({'text': 'Sure, I\'ll join.', 'gist': 'join_group', 'group': chosen['group']})
			_responses.append({'text': 'No thanks.', 'gist': 'decline_invite_to_group',  'group': chosen['group'], 'dislike': 1})
			
			if LIFE[dialog['listener']]['group']:
				_responses.append({'text': 'I\'m already in one.', 'gist': 'decline_invite_to_group_in_group', 'group': chosen['group']})
		else:
			if alife.stats.desires_group(LIFE[dialog['listener']], chosen['group']):
				if alife.judgement.judge_group(LIFE[dialog['listener']], chosen['group'])>alife.stats.get_minimum_group_score(LIFE[dialog['listener']]):
					_responses.append({'text': 'Sure, I\'ll join.', 'gist': 'join_group', 'group': chosen['group']})
					lfe.memory(LIFE[dialog['listener']], 'accept invite to group', group=chosen['group'])
				else:
					_responses.append({'text': 'No thanks.', 'gist': 'decline_invite_to_group', 'dislike': 1, 'group': chosen['group']})
					lfe.memory(LIFE[dialog['listener']], 'decline invite to group (judgement)', group=chosen['group'])
			else:
				_responses.append({'text': 'I\'m already in one.', 'gist': 'decline_invite_to_group_in_group', 'group': chosen['group']})
				lfe.memory(LIFE[dialog['listener']], 'decline invite to group (no desire)', group=chosen['group'])

	elif chosen['gist'] == 'ask_to_join_group':
		_responses.append({'text': 'Will you join our squad?', 'gist': 'invite_to_group', 'like': 1, 'group': LIFE[dialog['listener']]['group']})
		
	elif chosen['gist'] == 'inquire_about_group_work':
		_responses.append({'text': 'What kind of work are we talking about?', 'gist': 'ask_about_group', 'like': 1, 'group': chosen['group']})

	elif chosen['gist'] == 'inquire_about_group_camp':
		_shelter = alife.groups.get_shelter(chosen['group'])
				
		if _shelter:
			_responses.append({'text': 'We\'re camping at %s,%s.' % (_shelter[0], _shelter[1]), 'gist': 'end', 'like': 1})
		else:
			_responses.append({'text': 'We don\'t have a space yet.', 'gist': 'end', 'like': 1})

	elif chosen['gist'] == 'ask_about_group':
		#TODO: Change LIKE to DISLIKE depending on views
		if LIFE[dialog['speaker']]['stats']['firearms'] >= 7:
			_responses.append({'text': 'We want to make an impact on the Zone.', 'gist': 'invite_to_group', 'group': LIFE[dialog['listener']]['group']})
			_responses.append({'text': 'We\'re just trying to survive peacefully.', 'gist': 'decline_invite_to_group_wrong_motive', 'dislike': 1, 'group': LIFE[dialog['listener']]['group']})
			_responses.append({'text': 'We\'re looking to make some money.', 'gist': 'invite_to_group', 'group': LIFE[dialog['listener']]['group']})
		else:
			_responses.append({'text': 'We want to make an impact on the Zone.', 'gist': 'decline_invite_to_group_wrong_motive', 'dislike': 1, 'group': LIFE[dialog['listener']]['group']})
			_responses.append({'text': 'We\'re just trying to survive peacefully.', 'gist': 'invite_to_group', 'group': LIFE[dialog['listener']]['group']})
			_responses.append({'text': 'We\'re looking to make some money.', 'gist': 'invite_to_group', 'group': LIFE[dialog['listener']]['group']})
		
			_responses.append({'text': 'No thanks.', 'gist': 'decline_invite_to_group_wrong_motive', 'group': LIFE[dialog['listener']]['group']})
	
	elif chosen['gist'] == 'ask_about_group_founder':
		if LIFE[dialog['listener']]['group'] == chosen['group']:
			if alife.groups.is_leader(chosen['group'], dialog['listener']):
				_responses.append({'text': 'I am.', 'gist': 'end'})
			else:
				_responses.append({'text': '%s is.' % ' '.join(LIFE[alife.groups.get_group(LIFE[dialog['listener']]['group'])['leader']]['name']), 'gist': 'end'})
		else:
			_responses.append({'text': 'I have no idea.', 'gist': 'end'})
	
	elif chosen['gist'] == 'decline_invite_to_group':
		_responses.append({'text': 'Can we make a deal?', 'gist': 'group_bribe_request', 'group': chosen['group']})
		_responses.append({'text': 'Understood.', 'gist': 'end', 'group': chosen['group']})
	
	elif chosen['gist'] == 'decline_invite_to_group_in_group':
		_responses.append({'text': 'Can we make a deal?', 'gist': 'group_bribe_request', 'group': chosen['group']})
		_responses.append({'text': 'Understood.', 'gist': 'end', 'group': chosen['group']})
		_responses.append({'text': 'Then why are you still here?', 'gist': 'negative', 'group': chosen['group'], 'dislike': 1, 'danger': 1})
	
	elif chosen['gist'] == 'decline_invite_to_group_wrong_motive':
		_responses.append({'text': 'I don\'t work for free.', 'gist': 'bribe_into_group', 'group': chosen['group']})
		_responses.append({'text': 'I\'ll pass.', 'gist': 'bribe_into_group_fail', 'group': chosen['group']})
		
	elif chosen['gist'] == 'bribe_into_group':
		_responses.append({'text': 'What can I do, then?', 'gist': 'group_bribe_request', 'group': chosen['group']})
	
	elif chosen['gist'] == 'bribe_into_group_fail':
		_responses.append({'text': 'Okay.', 'gist': 'end', 'group': chosen['group']})
		_responses.append({'text': 'Maybe you should reconsider.', 'gist': 'intimidate_into_group', 'group': chosen['group'], 'dislike': 1, 'danger': 1})

	elif chosen['gist'] == 'group_bribe_request':
		_responses.append({'text': 'Give me $1k and I\'ll join.', 'gist': 'accept_group_bribe_request', 'group': chosen['group']})

	elif chosen['gist'] == 'accept_group_bribe_request':
		_responses.append({'text': 'It\'s a deal.', 'gist': 'complete_group_bribe', 'group': chosen['group'], 'like': 1})
		_responses.append({'text': 'That works for me.', 'gist': 'complete_group_bribe', 'group': chosen['group']})
		_responses.append({'text': 'That\'s too much for me.', 'gist': 'end', 'group': chosen['group'], 'like': 1})
	
	elif chosen['gist'] == 'complete_group_bribe':
		_responses.append({'text': 'I\'m in.', 'gist': 'join_group', 'group': chosen['group']})
	
	elif chosen['gist'] == 'tell_about_group':
		alife.groups.discover_group(LIFE[dialog['listener']], chosen['group'])
		
		if not LIFE[dialog['speaker']]['group'] == LIFE[dialog['listener']]['group']:
			if 'player' in LIFE[dialog['listener']]:
				_responses.append({'text': 'I\'m interested.', 'gist': 'ask_about_group', 'group': chosen['group'], 'like': 1})
				_responses.append({'text': 'I\'m not interested.', 'gist': 'not_interested_in_group', 'group': chosen['group']})
			else:
				if alife.stats.desires_group(LIFE[dialog['listener']], LIFE[dialog['speaker']]['group']):
					_responses.append({'text': 'I\'m interested.', 'gist': 'ask_about_group', 'group': chosen['group'], 'like': 1})
				else:
					_responses.append({'text': 'I\'m not interested.', 'gist': 'not_interested_in_group', 'group': chosen['group']})
	
	elif chosen['gist'] == 'not_interested_in_group':
		_responses.append({'text': 'Okay.', 'gist': 'end'})
	
	elif chosen['gist'] == 'join_group':
		show_messages(dialog)
		
		alife.groups.add_member(chosen['group'], dialog['speaker'])
		lfe.memory(LIFE[dialog['speaker']], 'join_group', group=chosen['group'])
		
		_responses.append({'text': 'Welcome!', 'gist': 'end', 'like': 1, 'group': chosen['group']})
		_responses.append({'text': 'Welcome.', 'gist': 'end', 'group': chosen['group']})

	elif chosen['gist'] == 'join_camp':
		LIFE[dialog['speaker']]['camp'] = chosen['camp']
		lfe.memory(LIFE[dialog['speaker']], 'join_camp', camp=chosen['camp'])
	
	elif chosen['gist'] == 'denied_from_camp':
		lfe.memory(LIFE[dialog['listener']], 'denied from camp',
		    camp=chosen['camp'],
		    danger=3)
	
	elif chosen['gist'] == 'ask_to_join_camp':
		#TODO: Implement: denied from camp
		
		if alife.judgement.can_trust(LIFE[dialog['listener']], dialog['speaker']):
			_responses.append({'text': 'Sure.', 'gist': 'join_camp', 'camp': chosen['camp'], 'like': 1})
		else:
			_responses.append({'text': 'I\'ve only heard bad things about you.', 'gist': 'deny_from_camp', 'camp': chosen['camp'], 'dislike': 1})
		
		print 'YOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO' * 10
	
	elif chosen['gist'] == 'opinion_of_target':
		#TODO: This only works if this is asked as a question, NOT in dialog
		_know = alife.brain.knows_alife_by_id(LIFE[dialog['speaker']], dialog['question']['who'])
		
		if not alife.brain.knows_alife_by_id(LIFE[dialog['speaker']], chosen['who']):
			_responses.append({'text': 'I don\'t know them.', 'gist': 'talk_about_trust_dont_know', 'who': chosen['who']})
		elif alife.judgement.can_trust(LIFE[dialog['speaker']], chosen['who']):
			_responses.append({'text': 'I trusted them.', 'gist': 'talk_about_trust', 'who': chosen['who'], 'value': _know['trust']})
		else:
			_responses.append({'text': 'I trusted them.', 'gist': 'talk_about_trust_negative', 'who': chosen['who'], 'value': _know['trust']})
	
	elif chosen['gist'] == 'talk_about_trust':
		lfe.memory(LIFE[dialog['listener']], 'target trusts target',
			target=dialog['speaker'],
			who=chosen['who'],
			value=chosen['who'])
	
	elif chosen['gist'] == 'talk_about_trust_negative':
		lfe.memory(LIFE[dialog['listener']], 'target doesn\'t trust target',
			target=dialog['speaker'],
			who=chosen['who'],
			value=chosen['who'])
	
	elif chosen['gist'] == 'talk_about_trust_negative':
		lfe.memory(LIFE[dialog['listener']], 'target doesn\'t know target',
			target=dialog['speaker'],
			who=chosen['who'],
			value=chosen['who'])
		
		print 'DONT KNOW' * 100
	
	elif chosen['gist'] == 'recruit_for_job':
		if chosen['job'] in LIFE[dialog['listener']]['jobs']:
			_responses.append({'text': 'I already know about this job and I\'m not interested.', 'gist': 'end'})
		else:
			LIFE[dialog['listener']]['jobs'].append(chosen['job'])
			alife.judgement.judge_jobs(LIFE[dialog['listener']])
			
			if LIFE[dialog['listener']]['job'] == chosen['job']:
				_responses.append({'text': 'I\'m in!', 'gist': 'end'})
			else:
				_responses.append({'text': 'No thanks.', 'gist': 'end'})
	
	elif chosen['gist'] == 'encounter-question':
		#TODO: ALife logic
		if 'player' in life:
			_responses.append({'text': 'I\'m exploring.', 'gist': 'end'})
			_responses.append({'text': 'I don\'t have to explain myself.', 'gist': 'end', 'dislike': 1, 'danger': 2})
	
	elif chosen['gist'] == 'call_topics':
		_life = LIFE[dialog['listener']]
		if _life['job']:
			_responses.append({'text': 'I\'m calling about a job.',
			                   'gist': 'call_about_job',
			                   'job': _life['job']})
		
		_responses.append({'text': 'Goodbye.', 'gist': 'end'})
	
	elif chosen['gist'] == 'call_about_job':
		_life = LIFE[dialog['listener']]
		
		if alife.jobs.get_creator(chosen['job']) == dialog['listener']:
			_responses.append({'text': 'What do you need?', 'gist': 'call_job_info'})

	elif chosen['gist'] == 'call_job_info':
		_life = LIFE[dialog['listener']]
		
		_responses.append({'text': 'Where are you located?', 'gist': 'call_get_location'})

	elif chosen['gist'] == 'call_get_location':
		_life = LIFE[dialog['listener']]
		_responses.append({'text': 'I am near %s, %s.' % (_life['pos'][0], _life['pos'][1]), 'gist': 'okay'})

	elif chosen['gist'] == 'okay':
		_responses.append({'text': 'Okay.', 'gist': 'end'})

	#NOTE: NO DIALOG AFTER THIS POINT WILL WORK	
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
	
	modify_trust(life, target['id'], chosen)
	modify_trust(target, life['id'], chosen)
	lfe.create_and_update_self_snapshot(LIFE[dialog['speaker']])
	lfe.create_and_update_self_snapshot(LIFE[dialog['listener']])
	
	#if _responses:
	dialog['speaker'] = life['id']
	dialog['listener'] = target['id']
	
	if 'player' in LIFE[dialog['speaker']]:
		_single_responses = {}
		for _response in _responses:
			if not _response['text'] in _single_responses:
				_single_responses[_response['text']] = _response
				continue
			
			if random.randint(0, 1):
				_single_responses[_response['text']] = _response
			
		_responses = _single_responses.values()
		if _responses and _responses[0]['gist'] == 'restart':
			dialog['topics'] = dialog['starting_topics']
			dialog['index'] = 0
		elif _responses:# and not _responses[0]['gist'] in ['nothing', 'end']:
			dialog['topics'] = _responses
			dialog['index'] = 0
		else:
			reset_dialog(dialog)
			
		return True
	
	dialog['topics'] = _responses
	alife_response(life, dialog)

def draw_dialog():
	if not lfe.has_dialog(LIFE[SETTINGS['controlling']]):
		return False
	
	dialog = [d for d in LIFE[SETTINGS['controlling']]['dialogs'] if d['enabled']][0]
	
	if 'player' in LIFE[dialog['creator']]:
		_receiver = LIFE[dialog['target']]
	else:
		_receiver = LIFE[dialog['creator']]
	
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
	_trust = alife.judgement.get_trust(_receiver, SETTINGS['controlling'])
	
	if alife.judgement.can_trust(_receiver, SETTINGS['controlling']) and _trust:
		tcod.console_set_default_foreground(dialog['console'], tcod.green)
		_trust_string = 'Trusted (%s)' % _trust
	elif not _trust:
		tcod.console_set_default_foreground(dialog['console'], tcod.lighter_gray)
		_trust_string = 'Neutral (%s)' % _trust
	else:
		tcod.console_set_default_foreground(dialog['console'], tcod.red)
		_trust_string = 'Not trusted (%s)' % _trust
	
	tcod.console_print(dialog['console'], 42+len(' '.join(_receiver['name'])), _y, _trust_string)
	tcod.console_set_default_foreground(dialog['console'], tcod.white)
	
	for m in dialog['messages'][numbers.clip(abs(len(dialog['messages']))-MAX_MESSAGES_IN_DIALOG, 0, 99999):]:
		part = (' '.join(LIFE[m['sender']]['name']), m['text'])
		_x = 41
		
		_impact = m['impact']
		_i = 0
		for line in part:
			if _i:
				tcod.console_set_default_foreground(dialog['console'], tcod.white)
				tcod.console_set_default_background(dialog['console'], tcod.black)
			else:
				if _impact == 1:
					tcod.console_set_default_foreground(dialog['console'], tcod.black)
					tcod.console_set_default_background(dialog['console'], tcod.green)
					tcod.console_set_background_flag(dialog['console'], tcod.BKGND_SET)
				elif not _impact:
					tcod.console_set_default_foreground(dialog['console'], tcod.white)
					tcod.console_set_default_background(dialog['console'], tcod.darker_gray)
					tcod.console_set_background_flag(dialog['console'], tcod.BKGND_SET)
				else:
					tcod.console_set_default_foreground(dialog['console'], tcod.black)
					tcod.console_set_default_background(dialog['console'], tcod.red)
					tcod.console_set_background_flag(dialog['console'], tcod.BKGND_SET)
				
				_i += 1
			
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

