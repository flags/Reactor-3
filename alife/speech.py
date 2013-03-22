from globals import *

import life as lfe

import logging

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
		if heard['from'] == target and heard['gist'] == gist:
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
	logging.debug('%s called announce: %s' % (' '.join(life['name']), gist))
	
	if public:
		_announce_to = [LIFE[i] for i in LIFE if not i == life['id']]
	else:
		_announce_to = [life['know'][i]['life'] for i in life['know'] if life['know'][i]['score']>0]
	
	for target in _announce_to:
		if not public and has_asked(life, target, gist):
			continue
	
		logging.debug('\t%s got announce.' % ' '.join(target['name']))
		lfe.create_conversation(life, gist, matches=[{'id': target['id']}], **kvargs)
		
		if not public:
			send(life, target, gist)
	
	return True

def communicate(life, gist, msg=None, radio=False, matches=[], **kvargs):
	lfe.create_conversation(life, gist, msg=msg, radio=radio, matches=matches, **kvargs)
	lfe.create_and_update_self_snapshot(life)

