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
         'stances': {'punching': {'level': 6, 'attack': {'force': 2}},
                     'deflect': {'level': 5, 'defend': {'force': .3}},
                     'standing': {'level': 5, 'move': 1.0},
                     'off_balance': {'level': 4, 'stunned': True},
                     'crouching': {'level': 4, 'exposed_limbs': ['head', 'neck', 'chest'], 'move': 0.5},
                     'sweep_kick': {'level': 3, 'attack': {'force': 5}},
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

def _get_quickest(life, thing, penalty=0, limit=5):
	_best_stance = {'stances': None, 'level': -1}
	
	for stance_name in life['stances']:
		_stance = get_stance(life, stance_name)
		
		if not thing in _stance:
			continue
		
		_delay = abs((get_current_stance(life)['level']-penalty)-_stance['level'])
		
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

def get_quickest_attack(life, limit=5):
	return _get_quickest(life, 'attack', limit=limit)

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
	
	print life['name'], 'is changing stance:', stance, life['stance_flags']

def stun(life, force=0):
	return enter_stance(life, get_quickest_stunned(life, penalty=force), forced=True)

def attack(life, target_id, stance):
	print life['name'], 'hit', LIFE[target_id]['name']+':', stance
	
	_attack = get_stance(life, stance)['attack']
	
	if 'force' in _attack:		
		_stance = get_current_stance(LIFE[target_id])
	
		if not 'defend' in _stance:
			life['score'] += 1
			stun(LIFE[target_id], force=_attack['force'])
		else:
			print LIFE[target_id]['name'], 'blocked', life['name']
			stun(life)

def think(life):
	_targets = []
	_incoming = []
	
	for life_id in life['seen']:
		#TODO: DISTANCE CHECK
		if life['id'] == life_id:
			continue
		
		_target = LIFE[life_id]
		_stance = get_current_stance(_target)
		
		if 'attack' in _stance:
			_incoming.append({'target_id': life_id, 'time': _target['stance_ticks']})
		elif not 'defend' in _stance or not random.randint(0, life['stats']['melee']):
			if 'defend' in _stance:
				print life['name'], 'tries to break', LIFE[life_id]['name'] 
			
			_targets.append({'target_id': life_id})
	
	if 'player' in life:
		#TODO: Player stuff
		pass
	else:
		for incoming_attack in _incoming:
			if 'forced' in life['stance_flags']:
				break
			
			if incoming_attack['time'] < life['stance_ticks'] and random.randint(0, life['stats']['melee']):
				_has_counter_attack = get_quickest_attack(life, limit=incoming_attack['time'])
				
				if _has_counter_attack:
					print life['name'], 'is countering', LIFE[incoming_attack['target_id']]['name']
					return enter_stance(life, _has_counter_attack, target_id=incoming_attack['target_id'])
			else:
				_has_defend = get_quickest_defend(life, limit=incoming_attack['time'])
				
				if _has_defend:
					print life['name'], 'is defending against', LIFE[incoming_attack['target_id']]['name']
					return enter_stance(life, _has_defend, target_id=incoming_attack['target_id'])
		
		if life['next_stance']:
			#print life['name'], life['next_stance'], life['stance_ticks']
			
			life['stance_ticks'] -= 1
			
			if life['stance_ticks']>0:
				return
			
			life['stance_ticks'] = 0
			life['stance'] = life['next_stance']
			life['next_stance'] = None
			
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
				print life['name'], 'holds'
				return True
			
			#Stand back up
			if not 'move' in _stance:
				return enter_stance(life, get_quickest_move(life))
				
			for target in _targets:
				return enter_stance(life, get_quickest_attack(life), target_id=target['target_id'])

for i in range(24):
	think(p1)
	think(p2)

print p1['score']
print p2['score']