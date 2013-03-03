import alife.combat as  combat

def judge_item(life, item):
	_score = 0
	
	_has_weapon = combat.is_weapon_equipped(life)
	
	if not _has_weapon and item['type'] == 'gun':
		_score += 30
	elif _has_weapon and item['type'] == _has_weapon['feed'] and item['ammotype'] == _has_weapon['ammotype']:
		_score += 20
	else:
		_score += 10
	
	return _score

def judge_self(life):
	_confidence = 0
	_limb_confidence = 0
	
	for limb in [life['body'][limb] for limb in life['body']]:
		#TODO: Mark as target?
		if not limb['bleeding']:
			_limb_confidence += 1
		
		if not limb['bruised']:
			_limb_confidence += 2
		
		if not limb['broken']:
			_limb_confidence += 3
	
	#TODO: There's a chance to fake confidence here
	#If we're holding a gun, that's all the other ALifes see
	#and they judge based on that (unless they've heard you run
	#out of ammo.)
	#For now we'll consider ammo just because we can...
	_self_armed = lfe.get_held_items(life,matches=[{'type': 'gun'}])
	
	if _self_armed:
		_weapon = lfe.get_inventory_item(life,_self_armed[0])
		_feed = weapons.get_feed(_weapon)
		
		if _feed and _feed['rounds']:
			_confidence += 30
		else:
			_confidence -= 30
	
	return _confidence+_limb_confidence

def judge(life, target):
	_like = 0
	_dislike = 0
	
	if target['life']['asleep']:
		return 0
	
	if 'surrender' in target['consider']:
		return 0
	
	for limb in [target['life']['body'][limb] for limb in target['life']['body']]:
		#TODO: Mark as target?
		if limb['bleeding']:
			_like += 1
		else:
			_dislike += 1
		
		if limb['bruised']:
			_like += 2
		else:
			_dislike += 2
		
		if limb['broken']:
			_like += 3
		else:
			_dislike += 3
	
	#Am I armed?
	#_self_armed = lfe.get_held_items(life,matches=[{'type': 'gun'}])
	_target_armed = combat.is_weapon_equipped(target['life'])#lfe.get_held_items(target['life'],matches=[{'type': 'gun'}])
	
	if _target_armed and weapons.get_feed(_target_armed):
		_dislike += 30
	#elif not _target_armed:
	#	_like += 20
	#	_dislike = 0
	
	#TODO: Add modifier depending on type of weapon
	#TODO: Consider if the AI has heard the target run out of ammo
	#TODO: Added "scared by", so a fear of guns would subtract from
	
	return _like-_dislike

def in_danger(life,target):
	if 'last_seen_time' in target and not target['last_seen_time']:
		#TODO: Courage here
		#print abs(target['danger_score']),judge_self(life),time.time()
		if abs(target['danger_score'])>=judge_self(life):
			return True
		else:
			return False
	
	if abs(target['score']) >= judge_self(life):
		return True
	else:
		return False
