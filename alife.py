############
# ALife v2 ########################
# Created by Luke Martin (flags)  #
###################################
# Started: 12:10 AM, 1/16/2013    #
# Ended: Probably not for a while #
###################################

from globals import *
import life as lfe
import pathfinding
import logging
import numbers
import time

def look(life):
	life['seen'] = []
	
	for ai in LIFE:
		if ai['id'] == life['id']:
			continue
		
		if numbers.distance(life['pos'],ai['pos']) > 30:
			#TODO: "see" via other means?
			continue
		
		if not lfe.can_see(life,ai['pos']):
			continue
		
		life['seen'].append(str(ai['id']))
		
		#TODO: Don't pass entire life, just id
		if str(ai['id']) in life['know']:
			continue
			
		logging.info('%s learned about %s.' % (life['name'][0],ai['name'][0]))
		
		life['know'][str(ai['id'])] = {'life': ai,'score': 0,'snapshot': {}}
	
	#logging.debug('\tTargets: %s' % (len(life['seen'])))

def hear(life):
	for event in life['heard']:
		print event

def update_self_snapshot(life,snapshot):
	life['snapshot'] = snapshot

def update_snapshot_of_target(life,target,snapshot):
	life['know'][str(target['id'])]['snapshot'].update(snapshot)
	
	logging.debug('%s updated their snapshot of %s.' % (life['name'][0],target['name'][0]))

def create_snapshot(life):
	_snapshot = {'condition': 0,
		'appearance': 0,
		'visible_items': []}

	for limb in life['body']:
		_snapshot['condition'] += lfe.get_limb_condition(life,limb)

	for item in lfe.get_all_visible_items(life):
		#snapshot['appearance'] += get_quality(item)
		_snapshot['visible_items'].append(str(item))
	
	return _snapshot

def process_snapshot(life,target):
	if life['know'][str(target['id'])]['snapshot'] == target['snapshot']:
		return False
	
	_ss = target['snapshot'].copy()
	
	update_snapshot_of_target(life,target,_ss)
	
	return True

def judge(life,target):
	_like = 0
	_dislike = 0
	
	for limb in [target['body'][limb] for limb in target['body']]:
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
	_self_armed = lfe.get_held_items(life,matches=[{'type': 'gun'}])
	_target_armed = lfe.get_held_items(target,matches=[{'type': 'gun'}])
	
	if _self_armed and _target_armed:
		#TODO: This.
		pass
	elif not _self_armed and _target_armed:
		_dislike += 50
	elif _self_armed and not _target_armed:
		_like += 50
	
	#TODO: Add modifier depending on type of weapon
	#TODO: Consider if the AI has heard the target run out of ammo
	#TODO: Added "scared by", so a fear of guns would subtract from
	
	return _like-_dislike

#TODO: Move to `life.py`?
def calculate_situation_danger(pos,**kvargs):
	#TODO: Doesn't really make sense...
	#if not lfe.can_see(kvargs['target']['life'],pos):
	#	return 0
	
	_distance = numbers.distance(pos,kvargs['target']['life']['pos'])
	
	#TODO: (WEAPON_ACCURACY_TO_POSITION/BASE_WEAPON_ACCURACY)
	_distance_mod = 100/100
	 
	return kvargs['target']['score']*(_distance*_distance_mod)

def combat(life,target):
	#_escape = numbers.create_dijkstra_map(target['life']['pos'],
	#	life['map'],
	#	calculate=calculate_situation_danger,
	#	life=life,
	#	target=target)
	
	#SETTINGS['heatmap'] = _escape
	
	#life['path'] = pathfinding.path_from_dijkstra(life['pos'],_escape)
	#numbers.draw_dijkstra(_escape)
	
	lfe.clear_actions(life)
	#lfe.add_action(life,{'action': 'move','to': life['path'][len(life['path'])-1]},200)
	lfe.add_action(life,{'action': 'move','to': [25,25]},200)

def understand(life):
	_target = {'who': None,'score': -10000}
	
	for entry in life['seen']:
		target = life['know'][entry]
		
		_score = target['score']
		
		_stime = time.time()
		if process_snapshot(life,target['life']):
			_score = judge(life,target['life'])
			
			logging.info('%s judged %s with score %s.' % (life['name'][0],target['life']['name'][0],_score))
		
		if _score > _target['score']:
			_target['who'] = target
			_target['score'] = _score
	
	if not _target['who']:
		#TODO: No active target, reroute to non-engagement logic
		return False
	
	#TODO: Life should use all stats instead of the judge function
	if _target['score'] <= judge(life,life):
		combat(life,_target['who'])

def think(life):
	#logging.debug('*THINKING*')
	#logging.debug('Look:')
	look(life)
	
	#logging.debug('Understand:')
	understand(life)
