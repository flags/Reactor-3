import life as lfe

import logging

def has_asked(life, target, gist):
	if gist in life['know'][target['id']]['asked']:
		return True
	
	return False

def has_answered(life, target, gist):
	if gist in life['know'][target['id']]['answered']:
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
	
	if has_answered(life, target, gist):
		return True
	
	return False

def ask(life, target, gist):
	life['know'][target['id']]['asked'].append(gist)
	lfe.create_and_update_self_snapshot(target)
		
	return True

def answer(life, target, gist):
	life['know'][target['id']]['answered'].append(gist)
	lfe.create_and_update_self_snapshot(target)
		
	return True

def announce(life, gist, **kvargs):
	logging.debug('%s called announce: %s' % (' '.join(life['name']), gist))
	
	for target in [life['know'][i]['life'] for i in life['know'] if life['know'][i]['score']>0]:
		if has_asked(life, target, gist):
			continue
	
		logging.debug('\t%s got announce.' % ' '.join(target['name']))
		lfe.create_conversation(life, gist, matches=[{'id': target['id']}], **kvargs)
		ask(life, target, gist)
	
	return True

def communicate(life, gist, msg=None, radio=False, matches=[], **kvargs):
	lfe.create_conversation(life, gist, msg=msg, radio=radio, matches=matches, **kvargs)
	lfe.create_and_update_self_snapshot(life)

