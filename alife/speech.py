import life as lfe

def has_considered(life,target,what):
	if what in life['know'][str(target['id'])]['consider']:
		return True
	
	return False

def consider(life,target,what):
	if not what in life['know'][str(target['id'])]['consider']:
		life['know'][str(target['id'])]['consider'].append(what)
		lfe.create_and_update_self_snapshot(target)
		
		return True
	
	return False

def unconsider(life,target,what):
	if what in life['know'][str(target['id'])]['consider']:
		life['know'][str(target['id'])]['consider'].remove(what)
		lfe.create_and_update_self_snapshot(target)
		
		return True
	
	return False

def communicate(life,gist,**kvargs):
	lfe.create_conversation(life,gist,**kvargs)

