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
import render_los
import weapons
import logging
import numbers
import maps
import time

def _weapon_equipped(life):
	return lfe.get_held_items(life,matches=[{'type': 'gun'}])

def _get_feed(life,weapon):
	_feeds = lfe.get_all_inventory_items(life,matches=[{'type': weapon['feed'],'ammotype': weapon['ammotype']}])
	
	_highest_feed = {'rounds': -1,'feed': None}
	for feed in [lfe.get_inventory_item(life,_feed['id']) for _feed in _feeds]:
		if feed['rounds']>_highest_feed['rounds']:
			_highest_feed['rounds'] = feed['rounds']
			_highest_feed['feed'] = feed
	
	return _highest_feed['feed']

def _refill_feed(life,feed):
	if not lfe.can_hold_item(life):
		logging.warning('No hands free to load ammo!')
		
		return False
	
	_hold = lfe.add_action(life,{'action': 'removeandholditem',
		'item': feed['id']},
		200,
		delay=0)
	
	#logging.info('%s is refilling ammo.' % life['name'][0])

	#TODO: This is a mess. Tear it apart if need be.
	_loading_rounds = len(lfe.find_action(life,matches=[{'action': 'refillammo'}]))
	
	if _loading_rounds >= len(lfe.get_all_inventory_items(life,matches=[{'type': 'bullet', 'ammotype': feed['ammotype']}])):
		return False
	
	_rounds = len(feed['rounds'])
	
	if _rounds>=feed['maxrounds']:
		print 'Full?'
		return True
	
	_left_to_load = len(lfe.get_all_inventory_items(life,matches=[{'type': 'bullet', 'ammotype': feed['ammotype']}]))+_loading_rounds+_rounds
	print 'ltl',_left_to_load
	for ammo in lfe.get_all_inventory_items(life,matches=[{'type': 'bullet', 'ammotype': feed['ammotype']}]):
		lfe.add_action(life,{'action': 'refillammo',
			'ammo': feed,
			'round': ammo},
			200,
			delay=20)
		
		_rounds += 1
		
		if _rounds>=feed['maxrounds']:
			break
	
	#print len(feed['rounds'])

def _equip_weapon(life):
	#TODO: Which one is the best one?
	_weapons = lfe.get_all_inventory_items(life,matches=[{'type': 'gun'}])
	
	#TODO: See issue #64
	_best_wep = {'weapon': None,'rounds': 0}
	for _wep in _weapons:
		
		_feeds = lfe.get_all_inventory_items(life,
			matches=[{'type': _wep['feed'],'ammotype': _wep['ammotype']}])
		
		if _feeds:
			_rounds = len(lfe.get_all_inventory_items(life,
				matches=[{'type': 'bullet', 'ammotype': _wep['ammotype']}]))
			
			if _rounds > _best_wep['rounds']:
				_best_wep['weapon'] = _wep
				_best_wep['rounds'] = _rounds
	
	if not _best_wep['weapon']:
		print 'No weapon!'
		return False
	
	_weapon = _best_wep['weapon']
	
	#TODO: Need to refill ammo?
	if not weapons.get_feed(_weapon):
		_feed = _get_feed(life,_weapon)
		
		if _feed:
			#TODO: How much time should we spend loading rounds if we're in danger?
			_avail_rounds = len(lfe.get_all_inventory_items(life,matches=[{'type': 'bullet', 'ammotype': _feed['ammotype']}]))
			if len(_feed['rounds']) < _avail_rounds:
				#print 'Need to fill ammo'
				_refill_feed(life,_feed)
			else:
				print 'Nothig else we can do?'
		else:
			print 'No feed!'
			
			return False
		
		return False
	else:
		print 'This gun is loaded'
		return True
	
	#TODO: Seems hacky
	_feed = _get_feed(life,_weapon)
	
	lfe.add_action(life,{'action': 'equipitem',
		'item': _weapon['id']},
		300,
		delay=0)
	
	life.add_action(PLAYER,{'action': 'reload',
		'weapon': _weapon['id'],
		'ammo': entry['ammo']},
		200,
		delay=20)
	
	return True

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
			life['know'][str(ai['id'])]['last_seen_time'] = 0
			life['know'][str(ai['id'])]['last_seen_at'] = ai['pos'][:]
			continue
			
		logging.info('%s learned about %s.' % (life['name'][0],ai['name'][0]))
		
		life['know'][str(ai['id'])] = {'life': ai,
			'score': 0,
			'last_seen_time': 0,
			'last_seen_at': ai['pos'][:],
			'snapshot': {}}
	
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
		_dislike += 50
	elif not _self_armed and _target_armed:
		_dislike += 50
	elif _self_armed and not _target_armed:
		_like += 50
	
	#TODO: Add modifier depending on type of weapon
	#TODO: Consider if the AI has heard the target run out of ammo
	#TODO: Added "scared by", so a fear of guns would subtract from
	
	return _like-_dislike

def position_for_combat(life,target,source_map):
	_cover = {'pos': None,'score':9000}
	
	#What can the target see?
	#TODO: Unchecked Cython flag
	_a = time.time()
	_top_left = (target['life']['pos'][0]-(MAP_WINDOW_SIZE[0]/2),
		target['life']['pos'][1]-(MAP_WINDOW_SIZE[1]/2))
	target_los = render_los.render_los(source_map,target['life']['pos'],top_left=_top_left)
	
	for pos in render_los.draw_circle(life['pos'][0],life['pos'][1],30):
		x = pos[0]-_top_left[0]
		y = pos[1]-_top_left[1]
		
		if target_los[life['pos'][1]-_top_left[1],life['pos'][0]-_top_left[0]]:
			_cover['pos'] = life['pos']
			return True
		
		if pos[0]<0 or pos[1]<0 or (pos[0],pos[1]) == (target['life']['pos'][0],target['life']['pos'][1]):
			continue
		
		if pos[0]>=MAP_SIZE[0]-1 or pos[1]>=MAP_SIZE[1]-1:
			continue
		
		if x<0 or y<0 or x>=target_los.shape[1] or y>=target_los.shape[0]:
			continue
		
		if source_map[pos[0]][pos[1]][target['life']['pos'][2]+1]:
			continue
		
		if target_los[y,x]:
			#TODO: Additional scores, like distance from target
			_score = numbers.distance(life['pos'],pos)
			
			if _score<_cover['score']:
				_cover['score'] = _score
				_cover['pos'] = list(pos)
	
	#print 'engage time',time.time()-_a
	
	if not _cover['pos']:
		print 'Nowhere to engage'
		return False
	
	lfe.clear_actions(life)
	lfe.add_action(life,{'action': 'move','to': _cover['pos']},200)
	
	return False

def combat(life,target,source_map):
	if not position_for_combat(life,target,source_map):
		print 'Traveling'
		return False
	
	#TODO: Shoot function...
	weapons.fire(life,target['life']['pos'])

def flee(life,target,source_map):
	#For the purposes of this test, we'll be assuming the ALife is fleeing from
	#the target.
	#Step 1: Locate cover
	_cover = {'pos': None,'score':9000}
	
	#What can the target see?
	#TODO: Unchecked Cython flag
	_a = time.time()
	_top_left = (target['life']['pos'][0]-(MAP_WINDOW_SIZE[0]/2),
		target['life']['pos'][1]-(MAP_WINDOW_SIZE[1]/2))
	target_los = render_los.render_los(source_map,target['life']['pos'],top_left=_top_left)
	
	for pos in render_los.draw_circle(life['pos'][0],life['pos'][1],30):
		x = pos[0]-_top_left[0]
		y = pos[1]-_top_left[1]
		
		if not target_los[life['pos'][1]-_top_left[1],life['pos'][0]-_top_left[0]]:
			_cover['pos'] = life['pos'][:]
			return True
		
		if pos[0]<0 or pos[1]<0 or (pos[0],pos[1]) == (target['life']['pos'][0],target['life']['pos'][1]):
			continue
		
		if pos[0]>=MAP_SIZE[0]-1 or pos[1]>=MAP_SIZE[1]-1:
			continue
		
		if x<0 or y<0 or x>=target_los.shape[1] or y>=target_los.shape[0]:
			continue
		
		if source_map[pos[0]][pos[1]][target['life']['pos'][2]+1]:# and source_map[pos[0]][pos[1]][target['life']['pos'][2]+2]:
			continue
		
		if not target_los[y,x]:
			#TODO: Additional scores, like distance from target
			_score = numbers.distance(life['pos'],pos)
			
			if _score<_cover['score']:
				_cover['score'] = _score
				_cover['pos'] = list(pos)
	
	#print 'hide time',time.time()-_a
	
	if not _cover['pos']:
		print 'Nowhere to hide'
		return False
	
	lfe.clear_actions(life)
	lfe.add_action(life,{'action': 'move','to': _cover['pos']},200)
	
	return False

def handle_lost_los(life):
	if life['in_combat']:
		#TODO: Do something here...
		pass
	
	#TODO: Take the original score and subtract/add stuff from there...
	_nearest_target = {'target': None,'score': 9000}
	for entry in life['know']:
		_target = life['know'][entry]
		#TODO: Kinda messing up this system a bit but it'll work for now.
		_score = _target['score']
		#_score += _target['last_seen_time']
		#_score -= numbers.distance(life['pos'],_target['last_seen_at'])
		
		if _score < _nearest_target['score']:
			_nearest_target['target'] = _target
			_nearest_target['score'] = _score
	
	return _nearest_target

def in_danger(life,target):
	if 'not_seen' in target:
		#We can take our time depending on distance
		#TODO: Courage here
		if target['danger_score']<=50:
			return True
		else:
			return False
	
	#print abs(target['score']),abs(judge(life,life))
	if abs(target['score']) >= abs(judge(life,life)):
		return True
	else:
		return False

def understand(life,source_map):
	_target = {'who': None,'score': -10000}
	
	_known_targets_not_seen = life['know'].keys()
	
	for entry in life['seen']:
		_known_targets_not_seen.remove(entry)
		
		target = life['know'][entry]
		
		_score = target['score']
		
		_stime = time.time()
		if process_snapshot(life,target['life']):
			_score = judge(life,target['life'])
			target['score'] = _score
			#print target['score']
			
			logging.info('%s judged %s with score %s.' % (life['name'][0],target['life']['name'][0],_score))
		
		if _score > _target['score']:
			_target['who'] = target
			_target['score'] = _score
	
	for _not_seen in _known_targets_not_seen:
		if life['know'][_not_seen]['last_seen_time']<100:
			life['know'][_not_seen]['last_seen_time'] += 1
	
	#if life['in_combat']:
	#	if _weapon_equipped(life):
	#		#if _weapon_check(life):
	#		combat(life,life['in_combat']['who'],source_map)
	#	else:
	#		if 'equipping' in life:
	#			return False
	#
	#		if _equip_weapon(life):
	#			life['equipping'] = True
	
	
	if not _target['who']:
		#TODO: No visible target, doesn't mean they're not there
		_lost_target = handle_lost_los(life)
		
		if not _lost_target:
			#TODO: Some kind of cooldown here...
			print 'No lost targets'
		
		_target['who'] = _lost_target['target']
		_target['score'] = _lost_target['target']['score']
		_target['danger_score'] = _lost_target['score']
		_target['not_seen'] = True
	
	if _target['who']:
		if in_danger(life,_target):
			if flee(life,_target['who'],source_map):
				#If we're not ready, prepare for combat
				if not _weapon_equipped(life):
					if not 'equipping' in life:
						if _equip_weapon(life):
							life['equipping'] = True
		else:
			combat(life,_target['who'],source_map)
		#life['in_combat'] = False
	else:
		#TODO: Idle?
		print 'Away from trouble.'
	
	#else:
	#	if life['in_combat']:
	#		if _weapon_equipped(life):
	#			#if _weapon_check(life):
	#			combat(life,life['in_combat']['who'],source_map)
	#			
	#			return True
	
	#TODO: Life should use all stats instead of the judge function
	#print abs(_target['score']),abs(judge(life,life))

def think(life,source_map):
	#logging.debug('*THINKING*')
	#logging.debug('Look:')
	look(life)
	
	#logging.debug('Understand:')
	understand(life,source_map)
