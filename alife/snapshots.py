import life as lfe

import logging
import time

def update_self_snapshot(life,snapshot):
	life['snapshot'] = snapshot

def update_snapshot_of_target(life,target,snapshot):
	life['know'][target['id']]['snapshot'].update(snapshot)
	
	logging.debug('%s updated their snapshot of %s.' % (' '.join(life['name']), ' '.join(target['name'])))

def create_snapshot(life):
	_snapshot = {'damage': lfe.get_damage(life),
		'appearance': 0,
		'visible_items': [],
		'generated': time.time()}

	for item in lfe.get_all_visible_items(life):
		_snapshot['visible_items'].append(str(item))
	
	return _snapshot

def process_snapshot(life,target):
	if life['know'][target['id']]['snapshot'] == target['snapshot']:
		return False
	
	_ss = target['snapshot'].copy()
	
	update_snapshot_of_target(life,target,_ss)
	
	return True

def check_snapshot(life,target):
	return life['know'][target['id']]['snapshot']
