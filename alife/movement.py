import life as lfe
import numbers

def score_search(life,target,pos):
	return -numbers.distance(life['pos'],pos)

def score_shootcover(life,target,pos):
	return numbers.distance(life['pos'],pos)

def score_escape(life,target,pos):
	_score = numbers.distance(life['pos'],pos)
	_score += (30-numbers.distance(target['pos'],pos))
	
	if not lfe.can_see(target,pos):
		_score -= numbers.distance(target['pos'],pos)
	
	if not lfe.can_see(life,pos):
		_score = 90000
	
	return _score

def score_find_target(life,target,pos):
	return -numbers.distance(life['pos'],pos)

def score_hide(life,target,pos):
	_score = numbers.distance(life['pos'],pos)
	#_score += (30-numbers.distance(target['pos'],pos))
	print 'hide'
	
	return _score

def position_for_combat(life,target,position,source_map):
	_cover = {'pos': None,'score': 9000}
	
	#print 'Finding position for combat'
	
	#TODO: Eventually this should be written into the pathfinding logic
	if lfe.can_see(life,target['life']['pos']):
		lfe.clear_actions(life)
		return True
	
	#What can the target see?
	#TODO: Unchecked Cython flag
	_attack_from = generate_los(life,target,position,source_map,score_shootcover,invert=True)
	
	if _attack_from:
		lfe.clear_actions(life)
		lfe.add_action(life,{'action': 'move','to': _attack_from['pos']},200)
		return False
	
	return True

def travel_to_target(life,target,pos,source_map):
	#print 'Traveling'
	
	if not tuple(life['pos']) == tuple(pos):
		lfe.clear_actions(life)
		lfe.add_action(life,{'action': 'move','to': (pos[0],pos[1])},200)
		return True
	
	return False

def search_for_target(life,target,source_map):
	_cover = generate_los(life,target,target['last_seen_at'],source_map,score_search,ignore_starting=True)
	
	if _cover:
		lfe.clear_actions(life)
		lfe.add_action(life,{'action': 'move','to': _cover['pos']},200)
		return False
	
	return True

def explore(life,source_map):
	#This is a bit different than the logic used for the other pathfinding functions
	pass

def escape(life,target,source_map):
	_escape = generate_los(life,target,target['life']['pos'],source_map,score_escape)
	
	if _escape:
		lfe.clear_actions(life)
		lfe.add_action(life,{'action': 'move','to': _escape['pos']},200)
		return False
	else:
		if not has_considered(life, target['life'], 'surrendered'):
			communicate(life, 'surrender', target=target['life'])
			#print 'surrender'
	
	if lfe.path_dest(life):
		return True
	
	return True

def hide(life,target,source_map):
	_cover = generate_los(life,target,target['life']['pos'],source_map,score_hide)
	
	if _cover:
		lfe.clear_actions(life)
		lfe.add_action(life,{'action': 'move','to': _cover['pos']},200)		
		return False
	
	return True
