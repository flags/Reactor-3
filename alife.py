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

def _weapon_equipped_and_ready(life):
	_wep = lfe.get_held_items(life,matches=[{'type': 'gun'}])
	
	if not _wep:
		return False
	
	#TODO: More than one weapon
	_wep = lfe.get_inventory_item(life,_wep[0])
	_feed = weapons.get_feed(_wep)
	
	if not _feed:
		return False
	
	if not _feed['rounds']:
		print 'feed in gun with no ammo'
		return False
	
	return True

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
		
		#TODO: We can't just return False. Handle dropping instead.
		return False
	
	if not lfe.get_held_items(life,matches=[{'id': feed['id']}]):
		_hold = lfe.add_action(life,{'action': 'removeandholditem',
			'item': feed['id']},
			200,
			delay=0)
	
	#logging.info('%s is refilling ammo.' % life['name'][0])

	#TODO: No check for ammo type.
	
	_loading_rounds = len(lfe.find_action(life,matches=[{'action': 'refillammo'}]))
	if _loading_rounds >= len(lfe.get_all_inventory_items(life,matches=[{'type': 'bullet', 'ammotype': feed['ammotype']}])):
		if not _loading_rounds:
			return True
		return False
	
	if len(lfe.find_action(life,matches=[{'action': 'refillammo'}])):
		return False
	
	_rounds = len(feed['rounds'])
	
	if _rounds>=feed['maxrounds']:
		print 'Full?'
		return True
	
	_ammo_count = len(lfe.get_all_inventory_items(life,matches=[{'type': 'bullet', 'ammotype': feed['ammotype']}]))
	_ammo_count += len(feed['rounds'])
	_rounds_to_load = numbers.clip(_ammo_count,0,feed['maxrounds'])
	for ammo in lfe.get_all_inventory_items(life,matches=[{'type': 'bullet', 'ammotype': feed['ammotype']}])[:_rounds_to_load]:		
		lfe.add_action(life,{'action': 'refillammo',
			'ammo': feed,
			'round': ammo},
			200,
			delay=5)
		
		_rounds += 1

def _equip_weapon(life):
	_best_wep = get_best_weapon(life)
	_weapon = _best_wep['weapon']
	
	#TODO: Need to refill ammo?
	if not weapons.get_feed(_weapon):
		_feed = _best_wep['feed']#_get_feed(life,_weapon)
		
		if _feed:
			#TODO: How much time should we spend loading rounds if we're in danger?
			if _refill_feed(life,_feed):
				lfe.add_action(life,{'action': 'reload',
					'weapon': _weapon,
					'ammo': _feed},
					200,
					delay=0)
		else:
			print 'No feed!'
			
			return False
		
		return False
	else:
		lfe.add_action(life,{'action': 'equipitem',
			'item': _weapon['id']},
			300,
			delay=0)
		
		print 'Loaded!'
		return True
	
	return True

def get_best_weapon(life):
	_weapons = lfe.get_all_inventory_items(life,matches=[{'type': 'gun'}])
	
	#TODO: See issue #64
	_best_wep = {'weapon': None,'rounds': 0}
	for _wep in _weapons:
		
		_feeds = lfe.get_all_inventory_items(life,
			matches=[{'type': _wep['feed'],'ammotype': _wep['ammotype']}])
		
		#TODO: Not *really* the best weapon, just already loaded
		if weapons.get_feed(_wep):
			_best_wep['weapon'] = _wep
			break

		#print _feeds
		_best_feed = {'feed': None, 'rounds': -1}
		for _feed in _feeds:
			
			#TODO: Check to make sure this isn't picking up the rounds already in the mag/clip
			_rounds = len(lfe.get_all_inventory_items(life,
				matches=[{'type': 'bullet', 'ammotype': _wep['ammotype']}]))
			_rounds += len(_feed['rounds'])
			
			if len(_feed['rounds']) > _best_feed['rounds']:
				_best_feed['rounds'] = len(_feed['rounds'])
				_best_feed['feed'] = _feed

			if _rounds > _best_wep['rounds']:
				_best_wep['weapon'] = _wep
				_best_wep['rounds'] = _rounds

		if not _best_feed['feed']:
			_best_wep['weapon'] = None
			print 'No feed for weapon.'
		else:
			_best_wep['feed'] = _best_feed['feed']
	
	if not _best_wep['weapon']:
		print 'No weapon!'
		return False
	
	return _best_wep

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
	#_self_armed = lfe.get_held_items(life,matches=[{'type': 'gun'}])
	_target_armed = lfe.get_held_items(target,matches=[{'type': 'gun'}])
	
	if _target_armed:
		_dislike += 30
	#if _self_armed and _target_armed:
	#	_dislike += 50
	#elif not _self_armed and _target_armed:
	#	_dislike += 50
	#elif _self_armed and not _target_armed:
	#	_like += 50
	
	#TODO: Add modifier depending on type of weapon
	#TODO: Consider if the AI has heard the target run out of ammo
	#TODO: Added "scared by", so a fear of guns would subtract from
	
	return _like-_dislike

def combat(life,target,source_map):
	if not position_for_combat(life,target,source_map):
		print 'Traveling'
		return False
	
	#print 'combat'
	#_wep = lfe.get_held_items(life,matches=[{'type': 'gun'}])
	#_wep = lfe.get_inventory_item(life,_wep[0])
	#_feed = weapons.get_feed(_wep)
	
	#weapons.fire(life,target['life']['pos'])
	if not len(lfe.find_action(life,matches=[{'action': 'shoot', 'target': target['life']['pos']}])):
		lfe.clear_actions(life)
	lfe.add_action(life,{'action': 'shoot','target': target['life']['pos'][:]},50,delay=15)

def score_shootcover(life,target,pos):
	return numbers.distance(life['pos'],pos)

def score_escape(life,target,pos):
	#_score = -numbers.distance(life['pos'],pos)
	_score = -numbers.distance(target['pos'],pos)
	
	if not lfe.can_see(target,pos):
		_score -= 25
	
	return _score

def score_hide(life,target,pos):
	return numbers.distance(life['pos'],pos)

def position_for_combat(life,target,source_map):
	_cover = {'pos': None,'score': 9000}
	
	#What can the target see?
	#TODO: Unchecked Cython flag
	_attack_from = generate_los(life,target,source_map,score_shootcover,invert=True)
	
	if _attack_from:
		lfe.clear_actions(life)
		lfe.add_action(life,{'action': 'move','to': _attack_from['pos']},200)
		return False
	
	return True

def escape(life,target,source_map):
	#So we need to get away from the target...
	#The thing is that we really need to be considering everyone
	#rather than just the target. Hopefully the target finding function
	#will do that for us (we'll assume that it will for now.)
	
	#To get away, we need to make sure we actually can first.
	#Hard to understand, but let's break it down:
	#	If we're hiding in the first place, then it's okay
	#to kinda have this function do it's own little thing
	#and take control of the character...
	
	#We're most likely in sight of the target if this is running.
	
	#Step #1: Find our escape route.
	_escape = generate_los(life,target,source_map,score_escape)
	
	if _escape:
		lfe.clear_actions(life)
		lfe.add_action(life,{'action': 'move','to': _escape['pos']},200)
		return False
	
	if lfe.path_dest(life):
		return True
	
	return True

def hide(life,target,source_map):
	_cover = generate_los(life,target,source_map,score_hide)
	
	if _cover:
		lfe.clear_actions(life)
		lfe.add_action(life,{'action': 'move','to': _cover['pos']},200)
		return False
	
	return True

def handle_hide(life,target,source_map):
	_weapon = get_best_weapon(life)	
	_feed = weapons.get_feed(_weapon['weapon'])
	
	#TODO: Can we merge this into get_best_weapon()?
	_has_loaded_ammo = False
	if _feed:
		if _feed['rounds']:
			_has_loaded_ammo = True
	
	if _weapon['weapon'] and (_weapon['rounds'] or _has_loaded_ammo):
		return hide(life,target,source_map)
	else:
		return escape(life,target,source_map)

def generate_los(life,target,source_map,score_callback,invert=False):
	#Step 1: Locate cover
	_cover = {'pos': None,'score':9000}
	
	#TODO: Unchecked Cython flag
	_a = time.time()
	_x = numbers.clip(target['life']['pos'][0]-(MAP_WINDOW_SIZE[0]/2),0,MAP_SIZE[0])
	_y = numbers.clip(target['life']['pos'][1]-(MAP_WINDOW_SIZE[1]/2),0,MAP_SIZE[1])
	_top_left = (_x,_y,target['life']['pos'][2])
	target_los = render_los.render_los(source_map,target['life']['pos'],top_left=_top_left,no_edge=False)
	
	for pos in render_los.draw_circle(life['pos'][0],life['pos'][1],30):
		x = pos[0]-_top_left[0]
		y = pos[1]-_top_left[1]
		
		if pos[0]<0 or pos[1]<0 or pos[0]>=MAP_SIZE[0] or pos[1]>=MAP_SIZE[0]:
			continue
		
		if x<0 or y<0 or x>=target_los.shape[1] or y>=target_los.shape[0]:
			continue
		
		if life['pos'][0]-_top_left[0]>=target_los.shape[0] or life['pos'][1]-_top_left[1]>=target_los.shape[1]:
			continue
		
		if target_los[life['pos'][1]-_top_left[1],life['pos'][0]-_top_left[0]]==invert:
			_cover['pos'] = life['pos'][:]
			return False
		
		if source_map[pos[0]][pos[1]][target['life']['pos'][2]+1] or source_map[pos[0]][pos[1]][target['life']['pos'][2]+2]:
			continue
		
		if target_los[y,x] == invert:
			#TODO: Additional scores, like distance from target
			_score = score_callback(life,target['life'],pos)
			
			if _score<_cover['score']:
				_cover['score'] = _score
				_cover['pos'] = list(pos)
	
	if not _cover['pos']:
		print 'Nowhere to hide'
		return False
	
	return _cover

def handle_lost_los(life):
	if life['in_combat']:
		#TODO: Do something here...
		pass
	
	#TODO: Take the original score and subtract/add stuff from there...
	_nearest_target = {'target': None,'score': 9000}
	for entry in life['know']:
		_target = life['know'][entry]
		#TODO: Kinda messing up this system a bit but it'll work for now.
		_score = judge(life,_target['life'])#_target['score']
		#_score -= _target['last_seen_time']
		#print _score
		#_score -= numbers.distance(life['pos'],_target['last_seen_at'])
		
		#print _target['last_seen_time']
		
		#if _target['last_seen_time'] >= 350:
		#	continue
		
		if _score < _nearest_target['score']:
			_nearest_target['target'] = _target
			_nearest_target['score'] = _score
	
	return _nearest_target

def in_danger(life,target):
	if 'not_seen' in target:
		#TODO: Courage here
		#print abs(target['danger_score']),judge_self(life),time.time()
		if abs(target['danger_score'])>=judge_self(life):
			return True
		else:
			return False
	
	#print abs(target['score']),judge_self(life)
	if abs(target['score']) >= judge_self(life):
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
			
			logging.info('%s judged %s with score %s.' % (life['name'][0],target['life']['name'][0],_score))
		
		if _score > _target['score']:
			_target['who'] = target
			_target['score'] = _score
	
	for _not_seen in _known_targets_not_seen:
		#TODO: 25?
		if life['know'][_not_seen]['last_seen_time']<350:
			life['know'][_not_seen]['last_seen_time'] += 1	
	
	if not _target['who']:
		#TODO: No visible target, doesn't mean they're not there
		_lost_target = handle_lost_los(life)
		
		if _lost_target['target']:
			_target['who'] = _lost_target['target']
			_target['score'] = _lost_target['target']['score']
			_target['danger_score'] = _lost_target['score']
			_target['not_seen'] = True
		else:
			#TODO: Some kind of cooldown here...
			print 'No lost targets'
	
	if _target['who']:
		if in_danger(life,_target):
			if handle_hide(life,_target['who'],source_map):
				#If we're not ready, prepare for combat
				if not _weapon_equipped_and_ready(life):
					if not 'equipping' in life:
						if _equip_weapon(life):
							life['equipping'] = True
				else:
					#TODO: ALife is hiding now...'
					pass
					
		else:
			combat(life,_target['who'],source_map)
		#life['in_combat'] = False
	else:
		#TODO: Idle?
		print 'Away from trouble.'
	
	#print _target['who'].keys()
	
	#TODO: Life should use all stats instead of the judge function
	#print abs(_target['score']),abs(judge(life,life))

def think(life,source_map):
	#logging.debug('*THINKING*')
	#logging.debug('Look:')
	look(life)
	
	#logging.debug('Understand:')
	understand(life,source_map)
