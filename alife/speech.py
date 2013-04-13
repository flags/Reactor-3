from globals import *

import life as lfe

import language

import logging
import random

def has_sent(life, target, gist):
	if gist in life['know'][target['id']]['sent']:
		return True
	
	return False

def has_received(life, target, gist):
	if gist in life['know'][target['id']]['received']:
		return True
	
	return False

def has_heard(life, target, gist):
	for heard in life['heard']:
		if heard['from']['id'] == target['id'] and heard['gist'] == gist:
			return True
	
	return False

def discussed(life, target, gist):
	if has_heard(life, target, gist):
		return True
	
	if has_sent(life, target, gist):
		return True
	
	return False

def send(life, target, gist):
	life['know'][target['id']]['sent'].append(gist)
	lfe.create_and_update_self_snapshot(target)
		
	return True

def receive(life, target, gist):
	life['know'][target['id']]['received'].append(gist)
	lfe.create_and_update_self_snapshot(target)
		
	return True

def announce(life, gist, public=False, **kvargs):
	"""Sends `gist` to any known ALife. If `public`, then send to everyone."""
	if public:
		_announce_to = [LIFE[i] for i in LIFE if not i == life['id']]
	else:
		_announce_to = [life['know'][i]['life'] for i in life['know'] if life['know'][i]['score']>0]
	
	for target in _announce_to:
		if not public and has_sent(life, target, gist):
			continue
	
		#logging.debug('\t%s got announce.' % ' '.join(target['name']))
		lfe.create_conversation(life, gist, matches=[{'id': target['id']}], **kvargs)
		
		if not public:
			send(life, target, gist)
	
	return True

def communicate(life, gist, msg=None, radio=False, matches=[], **kvargs):
	if 'target' in kvargs:
		logging.warning('Deprecated keyword in speech.communicate(): target')
	
	lfe.create_conversation(life, gist, msg=msg, radio=radio, matches=matches, **kvargs)
	lfe.create_and_update_self_snapshot(life)

def determine_interesting_event(life, target):
	_valid_phrases = []
	for memory in life['memory']:
		_memory_age = WORLD_INFO['ticks']-memory['time_created']
		
		if _memory_age >= 500:
			continue
		
		if memory['target'] == target['id']:
			continue
		
		_phrase = language.generate_memory_phrase(memory)
		
		if not _phrase:
			continue
		
		_valid_phrases.append(_phrase)
	
	if not _valid_phrases:
		return 'I don\'t have anything interesting to say.'
		
	return random.choice(_valid_phrases)
