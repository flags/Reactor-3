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
	if 'gist' in info:
		_topics, _memories = get_all_relevant_gist_responses(life, info['gist'])
	else:
		_topics, _memories = get_all_relevant_target_topics(life, target)
		_t, _m = get_all_irrelevant_target_topics(life, target)
		_topics.extend(_t)
		_memories.extend(_m)
		
		calculate_impacts(life, target, _topics)
	
	print _topics, _memories

def get_all_relevant_gist_responses(life, gist):
	#TODO: We'll definitely need to extend this for fuzzy searching	
	#return [memory for memory in lfe.get_memory(life, matches={'text': gist})]
	_topics = []
	_memories = []
	
	if gist in ['greeting']:
		_topics.append({'text': 'How are you?', 'gist': 'how_are_you'})
		_topics.append({'text': 'I don\'t have time to talk.', 'gist': 'ignore'})
		_topics.append({'text': 'Get out of my face!', 'gist': 'ignore_rude'})
	
	return _topics _memories

def get_all_relevant_target_topics(life, target):
	_topics = []
	_memories = []
	
	_topics.append({'text': 'How are you?', 'gist': 'how_are_you'})
	_topics.append({'text': 'What\'s new?', 'gist': 'how_are_you'})
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
