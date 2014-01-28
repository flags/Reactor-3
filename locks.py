from globals import LOCKS


def create_lock(name, locked=False):
	if name in LOCKS:
		raise Exception('Lock with name \'%s\' already exists.' % name)
	
	LOCKS[name] = {'locked': locked, 'lock_reason': ''}
	
	return LOCKS[name]

def get_lock(lock_name):
	if not lock_name in LOCKS:
		raise Exception('Lock with name \'%s\' doest not exist.' % lock_name)
	
	return LOCKS[lock_name]

def is_locked(lock_name):
	return get_lock(lock_name)['locked']

def lock(lock_name, reason=''):
	get_lock(lock_name)['locked'] = True
	
	if reason:
		print '%s: %s' % (lock_name, reason)

def unlock(lock_name, reason=''):
	get_lock(lock_name)['locked'] = False
	
	if reason:
		print '%s: %s' % (lock_name, reason)
