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
import random
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
	
	if not _best_wep:
		return False
	
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

def is_weapon_equipped(life):
	_weapon = lfe.get_held_items(life,matches=[{'type': 'gun'}])
	
	if not _weapon:
		return False
	
	return lfe.get_inventory_item(life,_weapon[0])

def has_weapon(life):
	return lfe.get_all_inventory_items(life,matches=[{'type': 'gun'}])

def has_usable_weapon(life):
	for weapon in lfe.get_all_inventory_items(life,matches=[{'type': 'gun'}]):
		if lfe.get_all_inventory_items(life, matches=[{'type': weapon['feed'],'ammotype': weapon['ammotype']}]):
			return True
	
	return False

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
			#print 'No feed for weapon.',life['name']
			return False
		else:
			_best_wep['feed'] = _best_feed['feed']
	
	if not _best_wep['weapon']:
		return False
	
	return _best_wep

def update_self_snapshot(life,snapshot):
	life['snapshot'] = snapshot

def update_snapshot_of_target(life,target,snapshot):
	life['know'][str(target['id'])]['snapshot'].update(snapshot)
	
	logging.debug('%s updated their snapshot of %s.' % (life['name'][0],target['name'][0]))

def create_snapshot(life):
	_snapshot = {'condition': 0,
		'appearance': 0,
		'visible_items': [],
		'generated': time.time()}

	for limb in life['body']:
		_snapshot['condition'] += lfe.get_limb_condition(life,limb)

	for item in lfe.get_all_visible_items(life):
		_snapshot['visible_items'].append(str(item))
	
	return _snapshot

def process_snapshot(life,target):
	if life['know'][str(target['id'])]['snapshot'] == target['snapshot']:
		return False
	
	_ss = target['snapshot'].copy()
	
	update_snapshot_of_target(life,target,_ss)
	
	return True

def combat(life,target,source_map):
	_pos_for_combat = position_for_combat(life,target,target['last_seen_at'],source_map)
	
	if not target['escaped'] and not _pos_for_combat:
		return False
	elif _pos_for_combat:
		lfe.clear_actions(life,matches=[{'action': 'move'}])
	
	if not lfe.can_see(life,target['life']['pos']):
		if not target['escaped'] and not travel_to_target(life,target,target['last_seen_at'],source_map):
			lfe.memory(life,'lost sight of %s' % (' '.join(target['life']['name'])),target=target['life']['id'])
			target['escaped'] = True
		elif target['escaped']:
			search_for_target(life,target,source_map)
		
		return False
	
	if not len(lfe.find_action(life,matches=[{'action': 'shoot'}])):
		lfe.add_action(life,{'action': 'shoot','target': target['life']['pos'][:]},50,delay=15)

def score_search(life,target,pos):
	return -numbers.distance(life['pos'],pos)

def score_shootcover(life,target,pos):
	return numbers.distance(life['pos'],pos)

def score_escape(life,target,pos):
	_score = -numbers.distance(target['pos'],pos)
	
	if not lfe.can_see(target,pos):
		_score -= 25
	
	return _score

def score_find_target(life,target,pos):
	return -numbers.distance(life['pos'],pos)

def score_hide(life,target,pos):
	_score = numbers.distance(life['pos'],pos)
	
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
	
	#print 'Searching'
	
	if _cover:
		lfe.clear_actions(life)
		lfe.add_action(life,{'action': 'move','to': _cover['pos']},200)
		return False
	
	return True

def escape(life,target,source_map):
	_escape = generate_los(life,target,target['life']['pos'],source_map,score_escape)
	
	if _escape:
		lfe.clear_actions(life)
		lfe.add_action(life,{'action': 'move','to': _escape['pos']},200)
		return False
	
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

def generate_los(life,target,at,source_map,score_callback,invert=False,ignore_starting=False):
	#Step 1: Locate cover
	_cover = {'pos': None,'score':9000}
	
	#TODO: Unchecked Cython flag
	_a = time.time()
	_x = numbers.clip(at[0]-(MAP_WINDOW_SIZE[0]/2),0,MAP_SIZE[0])
	_y = numbers.clip(at[1]-(MAP_WINDOW_SIZE[1]/2),0,MAP_SIZE[1])
	_top_left = (_x,_y,at[2])
	target_los = render_los.render_los(source_map,at,top_left=_top_left,no_edge=False)
	
	for pos in render_los.draw_circle(life['pos'][0],life['pos'][1],30):
		x = pos[0]-_top_left[0]
		y = pos[1]-_top_left[1]
		
		if pos[0]<0 or pos[1]<0 or pos[0]>=MAP_SIZE[0] or pos[1]>=MAP_SIZE[0]:
			continue
		
		if x<0 or y<0 or x>=target_los.shape[1] or y>=target_los.shape[0]:
			continue
		
		if life['pos'][0]-_top_left[0]>=target_los.shape[0] or life['pos'][1]-_top_left[1]>=target_los.shape[1]:
			continue
		
		if target_los[life['pos'][1]-_top_left[1],life['pos'][0]-_top_left[0]]==invert and not ignore_starting:
			_cover['pos'] = life['pos'][:]
			return False
		
		if source_map[pos[0]][pos[1]][at[2]+1] or source_map[pos[0]][pos[1]][at[2]+2]:
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

def remember_item(life,item):
	if not item['uid'] in life['know_items']:
		life['know_items'][item['uid']] = {'item': item,
			'score': judge_item(life,item),
			'last_seen_at': item['pos'][:],
			'flags': []}
		
		return True
	
	return False

def flag_item(life,item,flag):
	if not flag in life['know_items'][item['uid']]['flags']:
		life['know_items'][item['uid']]['flags'].append(flag)
		logging.debug('%s flagged item %s with %s' % (' '.join(life['name']),item['uid'],flag))
		
		return True
	
	return False

def find_known_items(life,matches=[],visible=True):
	_match = []
	
	for item in [life['know_items'][item] for item in life['know_items']]:
		if visible and not lfe.can_see(life,item['item']['pos']):
			continue
		
		if 'parent' in item['item'] or 'id' in item['item']:
			continue
		
		if 'demand_drop' in item['flags']:
			continue
		
		_break = False
		for match in matches:
			for key in match:
				if not item['item'].has_key(key) or not item['item'][key] == match[key]:
					_break = True
					break
			
			if _break:
				break
		
		_match.append(item)
	
	return _match

def collect_nearby_wanted_items(life):
	_highest = {'item': None,'score': 0}
	_nearby = find_known_items(life,matches=[{'type': 'gun'}],visible=True)
	
	for item in _nearby:
		if item['score'] > _highest['score']:
			_highest['score'] = item['score']
			_highest['item'] = item['item']
	
	if not _highest['item']:
		return True
	
	_empty_hand = lfe.get_open_hands(life)
	
	if not _empty_hand:
		print 'No open hands, managing....'
		
		return False
	
	if life['pos'] == _highest['item']['pos']:
		lfe.clear_actions(life)
		
		for action in lfe.find_action(life,matches=[{'action': 'pickupholditem'}]):
			#print action
			#print 'I was picking up something else...',_highest['item']['name']
			#print life['actions']
			return False
		
		lfe.add_action(life,{'action': 'pickupholditem',
			'item': _highest['item'],
			'hand': random.choice(_empty_hand)},
			200,
			delay=40)
	else:
		lfe.clear_actions(life)
		lfe.add_action(life,{'action': 'move','to': _highest['item']['pos'][:2]},200)
	
	return False

def handle_hide(life,target,source_map):
	_weapon = get_best_weapon(life)	
	_feed = None
	
	if _weapon:
		_feed = weapons.get_feed(_weapon['weapon'])		
	
	#TODO: Can we merge this into get_best_weapon()?
	_has_loaded_ammo = False
	if _feed:
		if _feed['rounds']:
			_has_loaded_ammo = True
	
	if _weapon and _weapon['weapon'] and (_weapon['rounds'] or _has_loaded_ammo):
		return hide(life,target,source_map)
	elif not _weapon and find_known_items(life,matches=[{'type': 'weapon'}],visible=True):
		return collect_nearby_wanted_items(life)
	else:
		return escape(life,target,source_map)

def handle_potential_combat_encounter(life,target,source_map):
	if not is_weapon_equipped(target['life']) and lfe.can_see(life,target['life']['pos']):
		communicate(life,'comply',target=target['life'])
		lfe.clear_actions(life)
		
		return True
	
	if is_weapon_equipped(life):
		combat(life,target,source_map)
	else:
		handle_hide_and_decide(life,target,source_map)

def handle_hide_and_decide(life,target,source_map):
	if handle_hide(life,target,source_map):		
		#TODO: Just need a general function to make sure we have a weapon
		if has_weapon(life):
			if consider(life,target['life'],'shouted_at'):
				if 'shown_scared' in target['consider']:
					lfe.say(life,'I\'m coming for you!')
					communicate(life,'confidence',target=target['life'])
					target['consider'].remove('shown_scared')
				else:
					lfe.say(life,'I\'m coming for you!')
					communicate(life,'intimidate',target=target['life'])
			
			#If we're not ready, prepare for combat
			if not _weapon_equipped_and_ready(life):
				if not 'equipping' in life:
					if _equip_weapon(life):
						life['equipping'] = True
			else:
				#TODO: ALife is hiding now...'
				pass
		else:
			if consider(life,target['life'],'shown_scared'):
				lfe.say(life,'@n panics!',action=True)
			
			#collect_nearby_wanted_items(life)

def handle_lost_los(life):
	if life['in_combat']:
		#TODO: Do something here...
		pass
	
	#TODO: Take the original score and subtract/add stuff from there...
	_nearest_target = {'target': None,'score': 0}
	for entry in life['know']:
		_target = life['know'][entry]
		_score = judge(life,_target)
		
		if _target['escaped']:
			_score += (_target['last_seen_time']/2)
		
		if _score < _nearest_target['score']:
			_nearest_target['target'] = _target
			_nearest_target['score'] = _score
	
	return _nearest_target

def in_danger(life,target):
	if 'last_seen_time' in target and not target['last_seen_time']:
		#TODO: Courage here
		#in danger!
		#print abs(target['danger_score']),judge_self(life),time.time()
		if abs(target['danger_score'])>=judge_self(life):
			return True
		else:
			return False
	
	if abs(target['score']) >= judge_self(life):
		return True
	else:
		return False

def check_snapshot(life,target):
	return life['know'][str(target['id'])]['snapshot']

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
	
	if target['life']['asleep']:
		return 0
	
	if 'surrender' in target['consider']:
		return 0
	
	for limb in [target['life']['body'][limb] for limb in target['life']['body']]:
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
	_target_armed = is_weapon_equipped(target['life'])#lfe.get_held_items(target['life'],matches=[{'type': 'gun'}])
	
	if _target_armed and weapons.get_feed(_target_armed):
		_dislike += 30
	
	#TODO: Add modifier depending on type of weapon
	#TODO: Consider if the AI has heard the target run out of ammo
	#TODO: Added "scared by", so a fear of guns would subtract from
	
	return _like-_dislike

def judge_item(life,item):
	_score = 0
	
	_has_weapon = is_weapon_equipped(life)
	
	if not _has_weapon and item['type'] == 'gun':
		_score += 30
	elif _has_weapon and item['type'] == _has_weapon['feed'] and item['ammotype'] == _has_weapon['ammotype']:
		_score += 20
	else:
		#elif _has_weapon:
		_score += 10
	
	return _score

def event_delay(event,time):
	if event['age'] < time:
		event['age'] += 1
		
		return True
	
	return False

def has_considered(life,target,what):
	if what in life['know'][str(target['id'])]['consider']:
		return True
	
	return False

def consider(life,target,what):
	if not what in life['know'][str(target['id'])]['consider']:
		life['know'][str(target['id'])]['consider'].append(what)
		
		return True
	
	return False

def unconsider(life,target,what):
	if what in life['know'][str(target['id'])]['consider']:
		life['know'][str(target['id'])]['consider'].remove(what)
		
		return True
	
	return False

def communicate(life,gist,**kvargs):
	lfe.create_conversation(life,gist,**kvargs)

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
			life['know'][str(ai['id'])]['escaped'] = False
			
			continue
			
		logging.info('%s learned about %s.' % (' '.join(life['name']),' '.join(ai['name'])))
		
		life['know'][str(ai['id'])] = {'life': ai,
			'score': 0,
			'last_seen_time': 0,
			'last_seen_at': ai['pos'][:],
			'escaped': False,
			'snapshot': {},
			'consider': []}
	
	for item in [ITEMS[item] for item in ITEMS]:
		if item.has_key('id'):
			continue
		
		if item.has_key('parent'):
			continue
		
		_can_see = lfe.can_see(life,item['pos'])
		
		if _can_see:
			remember_item(life,item)
		
		if _can_see:
			life['know_items'][item['uid']]['last_seen_time'] = 0
			life['know_items'][item['uid']]['score'] = judge_item(life,item)
		elif str(item['uid']) in life['know_items']:
			life['know_items'][item['uid']]['last_seen_time'] += 1

def listen(life):
	for event in life['heard'][:]:
		if not str(event['from']['id']) in life['know']:
			logging.warning('%s does not know %s!' % (' '.join(event['from']['name']),' '.join(life['name'])))
		
		if event['gist'] == 'surrender':
			if consider(life,event['from'],'surrender'):
				logging.debug('%s realizes %s has surrendered.' % (' '.join(life['name']),' '.join(event['from']['name'])))
				
				communicate(life,'stand_still',target=event['from'])
		
		elif event['gist'] == 'free_to_go':
			if life == event['target']:
				lfe.create_and_update_self_snapshot(event['from'])
				unconsider(life,event['from'],'surrender')
		
		elif event['gist'] == 'comply':
			#TODO: Judge who this is coming from...
			if life == event['target']:
				communicate(life,'surrender')
		
		elif event['gist'] == 'demand_drop_item':
			if life == event['target']:
				if event['age'] < 40:
					event['age'] += 1
					communicate(life,'compliant',target=event['from'])
					
					continue
				
				_inventory_item = lfe.get_inventory_item(life,event['item'])
				
				flag_item(life,_inventory_item,'demand_drop')
				lfe.say(life,'@n begins to drop their %s.' % _inventory_item['name'],action=True)
				
				lfe.add_action(life,{'action': 'dropitem',
					'item': event['item']},
					401,
					delay=20)
		
		elif event['gist'] == 'stand_still':
			if life == event['target']:
				lfe.add_action(life,{'action': 'block'},400)
		
		elif event['gist'] == 'compliant':
			if life == event['target']:
				consider(life,event['from'],'compliant')
		
		elif event['gist'] == 'intimidate':
			if event_delay(event,60):
				continue
			
			#Here we go...
			#This is the first *real* chance to make the ALife
			#just that much more complex...
			#We can make them lie about their current situation
			#to intimiate the person right back
			
			if life == event['target']:
				#We'll lie
				lfe.say(life,'I\'ll shoot if you come any closer.')
				communicate(life,'intimidate_with_weapon',target=event['from'])
		
		elif event['gist'] == 'intimidate_with_weapon':
			if event_delay(event,60):
				continue
			
			#TODO: We should also use sounds (reloading, etc) to confirm
			#if the ALife is telling the truth.
			if life == event['target']:
				_lying = True
				
				for item in [lfe.get_inventory_item(event['from'],item) for item in check_snapshot(life,event['from'])['visible_items']]:
					if item['type'] == 'gun':
						_lying = False
				
				if _lying:
					lfe.say(life,'I know you don\'t have a gun.')
					#communicate(life,
		
		elif event['gist'] == 'confidence':
			logging.debug('%s realizes %s is no longer afraid!' % (' '.join(life['name']),' '.join(event['from']['name'])))
		
		life['heard'].remove(event)

def understand(life,source_map):
	_target = {'who': None,'score': -10000}
	
	_known_targets_not_seen = life['know'].keys()
	
	if lfe.get_total_pain(life) > life['pain_tolerance']/2:
		communicate(life,'surrender')
	
	for entry in life['seen']:
		_known_targets_not_seen.remove(entry)
		
		target = life['know'][entry]
		
		_score = target['score']
		
		if target['life']['asleep']:
			continue
		
		_stime = time.time()
		if process_snapshot(life,target['life']):
			_score = judge(life,target)
			target['score'] = _score
			
			logging.info('%s judged %s with score %s.' % (' '.join(life['name']),' '.join(target['life']['name']),_score))
		
		if _score <= 0 and _score > _target['score']:
			_target['who'] = target
			_target['score'] = _score
		elif _score>0:
			#print 'Friendly!'
			pass
	
	for _not_seen in _known_targets_not_seen:
		#TODO: 350?
		if life['know'][_not_seen]['last_seen_time']<350:
			life['know'][_not_seen]['last_seen_time'] += 1	
	
	if not _target['who']:
		#TODO: No visible target, doesn't mean they're not there
		_lost_target = handle_lost_los(life)
		
		if _lost_target['target']:
			_target['who'] = _lost_target['target']
			_target['score'] = _lost_target['target']['score']
			_target['danger_score'] = _lost_target['score']
			_target['last_seen_time'] = _lost_target['target']['last_seen_time']
		#else:
		#	#TODO: Some kind of cooldown here...
		#	print 'No lost targets'
	
	if _target['who']:
		if in_danger(life,_target):
			handle_hide_and_decide(life,_target['who'],source_map)
		else:
			if has_considered(life,_target['who']['life'],'surrender'):
				if consider(life,_target['who']['life'],'asked_to_comply'):
					_visible_items = lfe.get_all_visible_items(_target['who']['life'])
					
					if _visible_items:
						_item_to_drop = _visible_items[0]
						communicate(life,'demand_drop_item',item=_item_to_drop,target=_target['who']['life'])
						
						lfe.say(life,'Drop that %s!' % lfe.get_inventory_item(_target['who']['life'],_item_to_drop)['name'])
						lfe.clear_actions(life,matches=[{'action': 'shoot'}])
					else:
						logging.warning('No items visible on target!')
				
				if has_considered(life,_target['who']['life'],'compliant'):
					if not lfe.get_held_items(_target['who']['life'],matches=[{'type': 'gun'}]):
						lfe.say(life,'Now get out of here!')
						communicate(life,'free_to_go',target=_target['who']['life'])
						unconsider(life,_target['who']['life'],'surrender')
				
			else:
				handle_potential_combat_encounter(life,_target['who'],source_map)
		
	else:
		pass
		#TODO: Idle?
		#print 'Away from trouble.'
		#lfe.clear_actions(life,matches=[{'action': 'shoot'}])

def think(life,source_map):
	look(life)
	listen(life)
	understand(life,source_map)
