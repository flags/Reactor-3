#NOTE: This was written outside the context of Reactor 3. It might look a bit weird...

from globals import *

import life as lfe

import alife

import random

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
	
	for _target in targets:
		target = LIFE[_target]
		if target == p:
			continue
		
		_next_stance = target['next_stance']['stance']
		if _next_stance and _next_stance in p['moves'] and not p['stance'] in p['moves'][_next_stance]['counters']:
			assume_stance(p, p['moves'][_next_stance]['counters'][0], towards=_target)
			return False
		elif not _next_stance or not target['stance'] in p['moves']:
			assume_stance(p, random.choice(p['moves'].keys()), towards=_target)
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
	for life_id in people:
		_life = LIFE[life_id]
		if not _life['stance'] in _life['moves']:
			continue
		
		if _life['next_stance']['towards']:
			_target = LIFE[_life['next_stance']['towards']]
			
			if _life['stance'] in _life['moves'] and _target['stance'] in _life['moves'][_life['stance']]['counters']:
				print '%s counters %s\'s %s!' % (_target['name'], _life['name'], _life['stance'])
				
				force_stance(_life, 'off-balance')
			else:
				if _target['stance'] in 'off-balance':
					force_stance(_target, 'prone')
				
				lfe.memory(_life, 'shot', target=_target['id'])
				lfe.memory(_target, 'shot_by', target=_life['id'], danger=3, trust=-10)
				alife.judgement.judge_life(_target, _life['id'])
				
				print '%s\'s %s hits %s!' % (_life['name'], _life['stance'], _target['name'])
			
			_life['next_stance']['towards'] = None
		else:
			print '%s\'s %s does nothing!' % (_life['name'], _life['stance'])
		
		#TODO: React...
		#life['stance'] = 'stand'

def fight(life, target):
	examine_possible_moves(life, [target])

def process_fights():
	_fighters = []
	for life in LIFE.values():
		if life['next_stance']['stance']:
			_fighters.append(life['id'])
			
			if life['next_stance']['towards']:
				_fighters.append(life['next_stance']['towards'])
	
	for _fighter in _fighters:
		examine_possible_moves(LIFE[_fighter], _fighters)

		tick(LIFE[_fighter])
	
	perform_moves(_fighters)
	
	return _fighters