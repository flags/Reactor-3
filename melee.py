#NOTE: This was written outside the context of Reactor 3. It might look a bit weird...

from globals import *

import graphics as gfx
import life as lfe

import alife
import menus

import random

def get_stance_score(p, stance):
	_current_score = p['stances'][p['stance']]
	_next_score = p['stances'][stance]
	
	return abs(_current_score-_next_score)

def assume_stance(p, stance, towards=None):
	if p['next_stance']['stance'] == stance and p['next_stance']['towards'] == towards:
		if 'player' in p:
			gfx.message('You continue to %s.' % stance)
			return False
		
	if p['next_stance']['forced']:
		if not p['next_stance']['delay']:
			p['next_stance']['forced'] = False
		else:
			print p['name'], 'cannot move (forced)'
			return False

	p['next_stance']['delay'] = get_stance_score(p, stance)
	p['next_stance']['stance'] = stance
	p['next_stance']['towards'] = towards
	p['next_stance']['forced'] = False
	
	if 'player' in p:
		gfx.message('You start to %s.' % stance)
	elif 'player' in LIFE[towards]:
		gfx.message('%s begins to %s.' % (' '.join(p['name']), stance))
	print p['name'], 'begins', p['next_stance']['stance'], '(%s' % p['next_stance']['delay']+')'
	return True

def force_stance(p, target_id, stance):
	if not p['stance'] == stance:
		if 'player' in p:
			gfx.message('You are thrown %s!' % stance)
		elif 'player' in LIFE[target_id]:
			gfx.message('You throw %s into %s.' % (' '.join(p['name']), stance))
	
	p['next_stance']['delay'] = get_stance_score(p, stance)
	p['stance'] = stance
	
	#TODO: Randomly regain balance or fall over
	p['next_stance']['stance'] = 'standing'
	p['next_stance']['forced'] = True
	
	print p['name'], 'forced into', p['stance'], '(%s' % p['next_stance']['delay']+')'

def examine_possible_moves(p, targets):
	#TODO: Cancel move?
	_moves = {}
	
	#if p['next_stance']['stance']:
	#	return False
	
	for _target in targets:
		target = LIFE[_target]
		if target == p:
			continue
		
		if 'player' in p:
			_moves[_target] = {'moves': [], 'counters': []}
		
		_next_stance = p['next_stance']['stance']
		_next_target_stance = target['next_stance']['stance']
		_incoming_attack = False
		
		#Target is attacking
		if target['stance'] in target['moves']:
			_incoming_attack = target['stance']
		elif _next_target_stance in target['moves']:
			_incoming_attack = _next_target_stance
		
		if _incoming_attack:
			if not _next_stance in p['moves'][_incoming_attack]['counters']:
				if 'player' in p:
					_moves[_target]['counters'].extend(p['moves'][_incoming_attack]['counters'])
				elif p['moves'][_incoming_attack]['counters']:
					assume_stance(p, random.choice(p['moves'][_incoming_attack]['counters']), towards=_target)
					return False
			
			elif p['stance'] in p['moves'][_incoming_attack]['counters']:
				return True
		
		if 'player' in p:
			_moves[_target]['moves'].extend(p['moves'].keys())
		else:
			assume_stance(p, random.choice(p['moves'].keys()), towards=_target)
			return True
		
		#if _next_stance and _next_stance in p['moves'] and not p['stance'] in p['moves'][_next_stance]['counters']:
		#	assume_stance(p, p['moves'][_next_stance]['counters'][0], towards=_target)
		#	return False
		#elif (not _next_stance or not target['stance'] in p['moves']):
		#	assume_stance(p, random.choice(p['moves'].keys()), towards=_target)
		#	return True
	
	if _moves:
		_menu = []
		
		for target_id in _moves:
			if _moves[target_id]['moves']:
				_menu.append(menus.create_item('title', '%s (Attacks)' % ' '.join(LIFE[target_id]['name']), None))
				
				for move in _moves[target_id]['moves']:
					_menu.append(menus.create_item('single', move, None, move=move, target=target_id))
			
			if _moves[target_id]['counters']:
				_menu.append(menus.create_item('title', '%s (Counters)' % ' '.join(LIFE[target_id]['name']), None))
				
				for move in _moves[target_id]['counters']:
					_menu.append(menus.create_item('single', move, None, move=move, target=target_id))
		
		_m = menus.create_menu(menu=_menu,
		                       position=[1, 1],
		                       title='Advanced Movement',
		                       format_str='$k',
		                       on_select=lambda entry: assume_stance(LIFE[SETTINGS['controlling']],
		                                                             entry['move'],
		                                                             towards=entry['target']),
		                       close_on_select=True)
		menus.activate_menu(_m)

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

def react_to_attack(life, target_id, stance):
	_target = LIFE[target_id]
	_attack = _target['moves'][stance]
	
	if life['stance'] <= _attack['effective_stance']:
		_force = life['stances'][life['stance']]-_attack['effective_stance']
	else:
		_force = 0
	
	if _force >= life['stances'][life['stance']]:
		force_stance(life, target_id, 'crawling')
	elif life['stances'][life['stance']]<=life['stances']['crouching']:
		force_stance(life, target_id, 'off-balance')

def perform_moves(people):
	for life_id in people:
		_life = LIFE[life_id]
		if not _life['stance'] in _life['moves'] or not _life['next_stance']['towards']:
			continue
		
		if _life['next_stance']['towards']:
			_target = LIFE[_life['next_stance']['towards']]
			
			if _life['stance'] in _life['moves'] and _target['stance'] in _life['moves'][_life['stance']]['counters']:
				if 'player' in _target:
					gfx.message('You counter %s\'s %s.' % (' '.join(_life['name']), _target['stance']), style='player_combat_good')
				elif 'player' in _life:
					gfx.message('%s counters your %s.' % (' '.join(_target['name']), _life['stance']), style='player_combat_bad')
				
				print '%s counters %s\'s %s!' % (_target['name'], _life['name'], _life['stance'])
				
				#react_to_attack(_life, _target['id'], _target['stance'])
			else:
				lfe.memory(_life, 'shot', target=_target['id'])
				lfe.memory(_target, 'shot_by', target=_life['id'], danger=3, trust=-10)
				alife.judgement.judge_life(_target, _life['id'])
				
				if 'player' in _life:
					gfx.message('You %s %s.' % (_life['stance'], ' '.join(_target['name'])), style='player_combat_good')
				elif 'player' in _target:
					gfx.message('%s lands a %s.' % (' '.join(_life['name']), _life['stance']), style='player_combat_bad')
				
				print '%s\'s %s hits %s!' % (_life['name'], _life['stance'], _target['name'])
				react_to_attack(_target, _life['id'], _life['stance'])
			
			_life['next_stance']['towards'] = None
		
		#TODO: Useful, just not here.
		#else:
		#	if 'player' in _life:
		#		gfx.message('You miss %s.' % ' '.join(_target['name']), style='player_combat_bad')
		#	elif 'player' in _target:
		#		gfx.message('%s misses you.' % ' '.join(_life['name']), style='player_combat_bad')
		#	
		#	print '%s\'s %s does nothing!' % (_life['name'], _life['stance'])
		
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
	
	if not _fighters:
		WORLD_INFO['sub_ticks'] = WORLD_INFO['max_sub_ticks']
		return False
	
	if WORLD_INFO['sub_ticks']:
		WORLD_INFO['sub_ticks'] -= 1
	else:
		WORLD_INFO['sub_ticks'] = WORLD_INFO['max_sub_ticks']
		return False
	
	for _fighter in _fighters:
		examine_possible_moves(LIFE[_fighter], _fighters)

		tick(LIFE[_fighter])
	
	perform_moves(_fighters)
	
	return _fighters