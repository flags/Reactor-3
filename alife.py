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

def look(life):
	life['seen'] = []
	
	for ai in LIFE:
		if ai == life:
			continue
		
		if numbers.distance(life['pos'],ai['pos']) > 30:
			#TODO: "see" via other means?
			continue
		
		if not lfe.can_see(life,ai['pos']):
			continue
		
		life['seen'].append(str(life['id']))
		
		#TODO: Don't pass entire life, just id
		if str(life['id']) in life['know']:
			continue
			
		logging.info('%s learned about %s.' % (life['name'][0],ai['name'][0]))
		
		life['know'][str(life['id'])] = {'life': ai,'score': 0}
	
	logging.debug('\tTargets: %s' % (len(life['seen'])))

def hear(life):
	for event in life['heard']:
		print event

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
	logging.debug('%s judged %s with score %s.' % (life['name'][0],target['name'][0],_like-_dislike))
	
	return _like-_dislike

#TODO: Move to `life.py`?
def calculate_situation_danger(pos,**kvargs):
	_distance = numbers.distance(pos,kvargs['target']['life']['pos'])+1
	
	#TODO: (WEAPON_ACCURACY_TO_POSITION/BASE_WEAPON_ACCURACY)
	_distance_mod = 100/100
	
	return _distance#kvargs['target']['score']*(_distance*_distance_mod)

def combat(life,target):
	#logging.info('Combat!')
	_escape = numbers.create_dijkstra_map(target['life']['pos'],
		life['map'],
		calculate=calculate_situation_danger,
		life=life,
		target=target)
	
	#SETTINGS['heatmap'] = _escape
	
	life['path'] = pathfinding.path_from_dijkstra(life['pos'],_escape)
	#numbers.draw_dijkstra(_escape)
	
	lfe.clear_actions(life)
	lfe.add_action(life,{'action': 'move','to': life['path'][len(life['path'])-1]},200)

def understand(life):
	_target = {'who': None,'score': -10000}
	
	for entry in life['seen']:
		target = life['know'][entry]
		
		_score = judge(life,target['life'])
		if not target['score'] == _score:
			logging.info('%s judged %s with score %s.' % (life['name'][0],target['life']['name'][0],_score))
		
		target['score'] = _score
		
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
	logging.debug('*THINKING*')
	logging.debug('Look:')
	look(life)
	
	logging.debug('Understand:')
	understand(life)
