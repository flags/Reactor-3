import life as lfe

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
	
	#if has_asked(life, target, gist):
	#	return True
	
	return False

def ask(life, target, gist):
	life['know'][target['id']]['asked'].append(gist)
	#lfe.create_and_update_self_snapshot(target)
		
	return True

def answer(life, target, gist):
	life['know'][target['id']]['answered'].append(gist)
	#lfe.create_and_update_self_snapshot(target)
		
	return True

#def unconsider(life,target,what):
#	if what in life['know'][target['id']]['consider']:
#		life['know'][target['id']]['consider'].remove(what)
#		lfe.create_and_update_self_snapshot(target)
#		
#		return True
#	
#	return False

def communicate(life, gist, msg=None, radio=False, matches=[], **kvargs):
	lfe.create_conversation(life, gist, msg=msg, radio=radio, matches=matches, **kvargs)
	lfe.create_and_update_self_snapshot(life)

