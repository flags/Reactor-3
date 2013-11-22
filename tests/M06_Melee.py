import random

COMBAT_MOVES = {'punch': {'counters': ['deflect', 'dodge']}}

CHAR = {'stance': 'stand',
        'next_stance': None,
		'stances': {'tackle': 7,
                    'leap': 6,
                    'roll': 5,
                    'prone': 5,
                    'duck': 4,
                    'kick': 2,
                    'punch': 2,
                    'dodge': 2,
                    'deflect': 1,
                    'parry': 0,
                    'grapple': 0,
                    'stand': 0,
                    'off-balance': -1,
                    'trip': -1}}

p1 = CHAR.copy()
p2 = CHAR.copy()

LIFE = [p1, p2]

p1['name'] = 'p1'
p1['next_stance'] = {'delay': 0, 'stance': None, 'towards': None, 'forced': False}
p2['name'] = 'p2'
p2['next_stance'] = {'delay': 0, 'stance': None, 'towards': None, 'forced': False}

def get_stance_score(p, stance):
	_current_score = p['stances'][p['stance']]
	_next_score = p['stances'][stance]
	
	return abs(_current_score-_next_score)

def assume_stance(p, stance, towards=None):
	if p['next_stance']['forced']:
		return False

	p['next_stance']['delay'] = get_stance_score(p, stance)
	p['next_stance']['stance'] = stance
	p['next_stance']['towards'] = towards
	p['next_stance']['forced'] = False
	
	print p['name'], 'begins', p['next_stance']['stance'], '(%s' % p['next_stance']['delay']+')'
	return True

def force_stance(p, stance):
	p['next_stance']['delay'] = get_stance_score(p, stance)
	p['stance'] = stance
	
	#TODO: Randomly regain balance or fall over
	p['next_stance']['stance'] = 'stand'
	
	p['next_stance']['forced'] = True
	
	print p['name'], 'forced into', p['stance'], '(%s' % p['next_stance']['delay']+')'

def examine_possible_moves(p, targets):
	#TODO: Cancel move?
	if p['next_stance']['stance']:
		return False
	
	for target in targets:
		if target == p:
			continue
		
		_next_stance = target['next_stance']['stance']
		if _next_stance and _next_stance in COMBAT_MOVES and not p['stance'] in COMBAT_MOVES[_next_stance]['counters']:
			assume_stance(p, COMBAT_MOVES[_next_stance]['counters'][0], towards=target)
			return False
		elif not _next_stance or not target['stance'] in COMBAT_MOVES:
			assume_stance(p, random.choice(COMBAT_MOVES.keys()), towards=target)
			return True

def tick(p):
	if p['next_stance']['delay']:
		p['next_stance']['delay'] -= 1
		
		if p['next_stance']['delay']:
			print p['name'], 'waiting:', p['next_stance']['stance'], '(%s' % p['next_stance']['delay']+')'
			return False
	
	if p['next_stance']['stance']:
		print p['name'], p['stance'], '->', p['next_stance']['stance']
		
		p['stance'] = p['next_stance']['stance']
		p['next_stance']['stance'] = None
	
	return True

def perform_moves(people):
	for life in people:
		if not life['stance'] in COMBAT_MOVES:
			continue
		
		if life['next_stance']['towards']:
			_target = life['next_stance']['towards']
			
			if life['stance'] in COMBAT_MOVES and _target['stance'] in COMBAT_MOVES[life['stance']]['counters']:
				print '%s counters %s\'s %s!' % (_target['name'], life['name'], life['stance'])
				
				force_stance(life, 'off-balance')
			else:
				if _target['stance'] in 'off-balance':
					force_stance(_target, 'prone')
				
				print '%s\'s %s hits %s!' % (life['name'], life['stance'], _target['name'])
			
			life['next_stance']['towards'] = None
		else:
			print '%s\'s %s does nothing!' % (life['name'], life['stance'])
		
		#TODO: React...
		#life['stance'] = 'stand'

assume_stance(p1, 'punch', towards=p2)

t = 7
while t:
	examine_possible_moves(p1, LIFE)
	examine_possible_moves(p2, LIFE)
	
	tick(p1)
	tick(p2)
	
	perform_moves([p1, p2])
	t -= 1