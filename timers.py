from globals import WORLD_INFO, ITEMS, LIFE

import alife

def is_life(entity):
	_life = (not 'prefix' in entity)
	
	if _life:
		_id_key = 'id'
	else:
		_id_key = 'uid'
	
	return _life, _id_key

def create(entity, action, time):
	_life, _id_key = is_life(entity)
	
	_new_timer = {'action': action,
	          'time': WORLD_INFO['ticks']+time,
	          'owner': entity[_id_key],
	          'life': _life}
	
	_i = 0
	for timer in WORLD_INFO['timers']:
		if _new_timer['time'] > time['time']:
			WORLD_INFO['timers'].insert(_i, _new_timer)
			return True
		
		_i += 1
		
	WORLD_INFO['timers'].append(_new_timer)

def remove_by_owner(entity):
	_life, _id_key = is_life(entity)

	_remove = []
	for timer in WORLD_INFO['timers']:
		if timer['owner'] in LIFE:
			if LIFE[timer['owner']] == entity:
				_remove.append(timer)
		else:
			if ITEMS[timer['owner']] == entity:
				_remove.append(timer)
	
	while _remove:
		WORLD_INFO['timers'].remove(_remove.pop())

def tick():
	if not WORLD_INFO['timers']:
		return False
	
	while WORLD_INFO['ticks'] == WORLD_INFO['timers'][0]['time']:
		_event = WORLD_INFO['timers'][0]
		
		if _event['life']:
			_owner = LIFE[_event['owner']]
		else:
			_owner = ITEMS[_event['owner']]
		
		alife.action.execute_small_script(_owner, _event['action'])
		
		if _event in WORLD_INFO['timers']:
			WORLD_INFO['timers'].remove(_event)
		
		if not WORLD_INFO['timers']:
			break
		