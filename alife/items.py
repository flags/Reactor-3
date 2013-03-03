from globals import *

def remember_item(life,item):
	if not item['uid'] in life['know_items']:
		life['know_items'][item['uid']] = {'item': item,
			'score': judge_item(life,item),
			'last_seen_at': item['pos'][:],
			'flags': []}
		
		return True
	
	return False

def flag_item(life,item,flag):
	print ' '.join(life['name'])
	
	if not flag in life['know_items'][item['uid']]['flags']:
		life['know_items'][item['uid']]['flags'].append(flag)
		logging.debug('%s flagged item %s with %s' % (' '.join(life['name']),item['uid'],flag))
		
		return True
	
	return False

def find_known_items(life, matches=[], visible=True):
	_match = []
	
	for item in [life['know_items'][item] for item in life['know_items']]:
		if visible and not lfe.can_see(life,item['item']['pos']):
			continue
		
		if 'parent' in item['item'] or 'id' in item['item']:
			continue
		
		if 'demand_drop' in item['flags']:
			continue
		
		_break = False
		for match in matches:
			for key in match:
				if not item['item'].has_key(key) or not item['item'][key] == match[key]:
					_break = True
					break
			
			if _break:
				break
		
		if _break:
			continue
		
		_match.append(item)
	
	return _match

def collect_nearby_wanted_items(life, matches=[{'type': 'gun'}]):
	_highest = {'item': None,'score': 0}
	_nearby = find_known_items(life, matches=matches, visible=True)
	
	for item in _nearby:
		if item['score'] > _highest['score']:
			_highest['score'] = item['score']
			_highest['item'] = item['item']
	
	if not _highest['item']:
		return True
	
	_empty_hand = lfe.get_open_hands(life)
	
	if not _empty_hand:
		print 'No open hands, managing....'
		
		return False
	
	if life['pos'] == _highest['item']['pos']:
		lfe.clear_actions(life)
		
		for action in lfe.find_action(life, matches=[{'action': 'pickupholditem'}]):
			#print 'I was picking up something else...',_highest['item']['name']
			return False
		
		lfe.add_action(life,{'action': 'pickupholditem',
			'item': _highest['item'],
			'hand': random.choice(_empty_hand)},
			200,
			delay=40)
	else:
		lfe.clear_actions(life)
		lfe.add_action(life,{'action': 'move','to': _highest['item']['pos'][:2]},200)
	
	return False
