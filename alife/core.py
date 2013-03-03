import life as lfe

import alife.sight as sight
import alife.survival as survival

def flag(life,flag):
	life['flags'][flag] = True

def unflag(life,flag):
	life['flags'][flag] = False

def get_flag(life,flag):
	if not flag in life['flags']:
		return False
	
	return life['flags'][flag]

def understand(life,source_map):
	_target = {'who': None,'score': -10000}
	_neutral_targets = []
	
	_known_targets_not_seen = life['know'].keys()
	
	if get_flag(life, 'surrendered'):
		return False
	
	if lfe.get_total_pain(life) > life['pain_tolerance']/2:
		communicate(life,'surrender')
	
	for entry in life['seen']:
		_known_targets_not_seen.remove(entry)
		target = life['know'][entry]
		_score = target['score']
		
		if target['life']['asleep']:
			continue
		
		if process_snapshot(life,target['life']):
			_score = judge(life,target)
			target['score'] = _score
			
			logging.info('%s judged %s with score %s.' % (' '.join(life['name']),' '.join(target['life']['name']),_score))
		
		if _score <= 0 and _score > _target['score']:
			_target['who'] = target
			_target['score'] = _score
		elif _score>0:
			_neutral_targets.append(target)
	
	for _not_seen in _known_targets_not_seen:
		#TODO: 350?
		if life['know'][_not_seen]['last_seen_time']<350:
			life['know'][_not_seen]['last_seen_time'] += 1	
	
	if not _target['who']:
		#TODO: No visible target, doesn't mean they're not there
		_lost_target = sight.handle_lost_los(life)
		
		if _lost_target['target']:
			_target['who'] = _lost_target['target']
			_target['score'] = _lost_target['target']['score']
			_target['danger_score'] = _lost_target['score']
			_target['last_seen_time'] = _lost_target['target']['last_seen_time']
		#else:
		#	#TODO: Some kind of cooldown here...
		#	print 'No lost targets'
	
	if _target['who']:
		if in_danger(life,_target):
			handle_hide_and_decide(life,_target['who'],source_map)
		else:
			if has_considered(life,_target['who']['life'],'surrendered') and not has_considered(life,_target['who']['life'],'resist'):
				if consider(life,_target['who']['life'],'asked_to_comply'):
					_visible_items = lfe.get_all_visible_items(_target['who']['life'])
					
					if _visible_items:
						_item_to_drop = _visible_items[0]
						communicate(life,'demand_drop_item',item=_item_to_drop,target=_target['who']['life'])
						
						lfe.say(life,'Drop that %s!' % lfe.get_inventory_item(_target['who']['life'],_item_to_drop)['name'])
						lfe.clear_actions(life,matches=[{'action': 'shoot'}])
					else:
						logging.warning('No items visible on target!')
				
				if has_considered(life,_target['who']['life'],'compliant'):
					if not lfe.get_held_items(_target['who']['life'],matches=[{'type': 'gun'}]):
						lfe.say(life,'Now get out of here!')
						communicate(life,'free_to_go',target=_target['who']['life'])
						unconsider(life,_target['who']['life'],'surrender')
				
			else:
				handle_potential_combat_encounter(life,_target['who'],source_map)
		
	else:
		for neutral_target in _neutral_targets:
			if has_considered(life, neutral_target['life'], 'greeting'):
				continue

			communicate(life, 'greeting', target=neutral_target['life'])

		survival.survive(life)
