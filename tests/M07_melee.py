import random
import copy


LIFE = {}

_LIFE = {'score': 0,
         'stance': 'standing',
         'next_stance': None,
         'stance_flags': {},
         'seen': ['1', '2'],
         'stats': {'melee': 5},
         'stance_ticks': 0,
         'stances': {'punching': {'level': 9, 'attack': {'force': 1}},
                     'deflect': {'level': 6, 'defend': {'force': 1}},
                     'standing': {'level': 5, 'move': 1.0},
                     'off_balance': {'level': 6, 'stunned': True, 'repeat': 'knocked_over'},
                     'crouching': {'level': 4, 'exposed_limbs': ['head', 'neck', 'chest'], 'move': 0.5},
                     'sweep_kick': {'level': 2, 'attack': {'force': 3}},
                     'stomp': {'level': 4, 'attack': {'force': 7}, 'target_limbs': ['head', 'neck', 'chest']},
                     'crawling': {'level': 2, 'exposed_limbs': ['head', 'neck', 'chest'], 'move': 0.3},
                     'knocked_over': {'level': 1, 'stunned': True}}}
p1 = copy.deepcopy(_LIFE)
p2 = copy.deepcopy(_LIFE)

p1['name'] = 'p1'
p1['id'] = '1'
p2['name'] = 'p2'
p2['id'] = '2'

LIFE['1'] = p1
LIFE['2'] = p2


def get_stance(life, stance):
	return life['stances'][stance]

def get_current_stance(life):
	return get_stance(life, life['stance'])

def _get_quickest(life, thing, target_id=None, penalty=0, limit=5):
	_best_stance = {'stances': [], 'level': -1}
	
	for stance_name in life['stances']:
		_stance = get_stance(life, stance_name)
		
		if not thing in _stance:
			continue
		
		_delay = abs((get_current_stance(life)['level']-penalty)-_stance['level'])
		
		if 'target_limbs' in _stance and target_id:
			_target_stance = get_current_stance(LIFE[target_id])
			
			_continue = False
			if 'exposed_limbs' in _target_stance:
				for target_limb in _stance['target_limbs']:
					#TODO: ENABLE THIS
					#if not target_limb in LIFE[target_id]['body']:
					#	continue
					
					if target_limb in _target_stance['exposed_limbs']:
						_delay -= 1
					else:
						_continue = True
						
						break
			else:
				continue
			
			if _continue:
				continue
		
		if _delay>limit:
			continue
		
		if not _best_stance['stances'] or _delay <= _best_stance['level']:
			if _best_stance['level'] == _delay:
				_best_stance['stances'].append(stance_name)
			else:
				_best_stance['stances'] = [stance_name]
				_best_stance['level'] = _delay
	
	if not _best_stance['stances']:
		return None
	
	return random.choice(_best_stance['stances'])

def get_quickest_move(life, limit=5):
	return _get_quickest(life, 'move', limit=limit)

def get_quickest_attack(life, target_id, limit=5):
	return _get_quickest(life, 'attack', target_id=target_id, limit=limit)

def get_quickest_defend(life, limit=3):
	return _get_quickest(life, 'defend', limit=limit)

def get_quickest_stunned(life, penalty=0, limit=10):
	return _get_quickest(life, 'stunned', penalty=penalty, limit=limit)

def enter_stance(life, stance, forced=False, **kwargs):
	_time = abs(get_current_stance(life)['level']-get_stance(life, stance)['level'])
	
	life['stance_ticks'] = _time
	life['next_stance'] = stance
	life['stance_flags'].update(kwargs)
	
	if forced:
		life['stance_flags']['forced'] = True
	
	print(life['name'], '->', stance, _time)

def stun(life, force=0):
	_current_stance = get_current_stance(life)
	
	if 'repeat' in _current_stance:
		_next_stance = 'knocked_over'
	else:
		_next_stance = get_quickest_stunned(life, penalty=force)
	
	return enter_stance(life, _next_stance, forced=True)

def attack(life, target_id, stance):
	print(life['name'], 'hit', LIFE[target_id]['name']+':', stance)
	
	_attack = get_stance(life, stance)['attack']
	
	if 'force' in _attack:		
		_stance = get_current_stance(LIFE[target_id])
	
		if not 'defend' in _stance:
			life['score'] += 1
			stun(LIFE[target_id], force=_attack['force'])
		else:
			print(LIFE[target_id]['name'], 'blocked', life['name'])
			stun(life)

def think(life):
	_targets = []
	_incoming = []
	
	for life_id in life['seen']:
		#TODO: DISTANCE CHECK
		if life['id'] == life_id:
			continue
		
		_target = LIFE[life_id]
		_current_target_stance = get_current_stance(_target)
		
		if _target['next_stance']:
			_next_target_stance = get_stance(_target, _target['next_stance'])
		else:
			_next_target_stance = None
		
		if _next_target_stance and 'attack' in _next_target_stance:
			_incoming.append({'target_id': life_id, 'time': _target['stance_ticks']})
		elif not 'defend' in _current_target_stance or not random.randint(0, life['stats']['melee']):
			if 'defend' in _current_target_stance:
				print(life['name'], 'tries to break', LIFE[life_id]['name']) 
			
			_targets.append({'target_id': life_id})
	
	if 'player' in life:
		#TODO: Player stuff
		pass
	else:
		for incoming_attack in _incoming:
			if 'forced' in life['stance_flags']:
				break
			
			if incoming_attack['time'] < life['stance_ticks'] and random.randint(0, life['stats']['melee']):
				_has_counter_attack = get_quickest_attack(life, incoming_attack['target_id'], limit=incoming_attack['time'])
				
				if _has_counter_attack:
					print(life['name'], 'is countering', LIFE[incoming_attack['target_id']]['name'])
					return enter_stance(life, _has_counter_attack, target_id=incoming_attack['target_id'])
			else:
				_has_defend = get_quickest_defend(life, limit=incoming_attack['time'])
				
				if _has_defend:
					if not 'defend' in get_current_stance(life) and not (life['next_stance'] and 'defend' in get_stance(life, life['next_stance'])):
						print(life['name'], 'is defending against', LIFE[incoming_attack['target_id']]['name'])
						return enter_stance(life, _has_defend, target_id=incoming_attack['target_id'])
		
		if life['next_stance']:
			#print life['name'], '...', life['next_stance'], life['stance_ticks']
			
			life['stance_ticks'] -= 1
			
			if life['stance_ticks']>0:
				return
			
			life['stance_ticks'] = 0
			life['stance'] = life['next_stance']
			life['next_stance'] = None
			
			print(life['name'], '=', life['stance'], life['stance_flags'])
			
			_stance = get_current_stance(life)
			_flags = life['stance_flags'].copy()
			life['stance_flags'] = {}
			
			if not 'attack' in _stance:
				return True
			
			_target = LIFE[_flags['target_id']]
			
			attack(life, _flags['target_id'], life['stance'])
			
		else:
			_stance = get_current_stance(life)
			
			if 'defend' in _stance and random.randint(0, life['stats']['melee']):
				print(life['name'], 'holds')
				return True
			
			#Stand back up
			if not 'move' in _stance:
				return enter_stance(life, get_quickest_move(life))
				
			for target in _targets:
				return enter_stance(life, get_quickest_attack(life, target['target_id']), target_id=target['target_id'])

for i in range(24):
	think(p1)
	think(p2)

print(p1['score'])
print(p2['score'])