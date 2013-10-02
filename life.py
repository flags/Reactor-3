from globals import *
from alife import *

import graphics as gfx
import damage as dam
import pathfinding
import scripting
import language
import contexts
import drawing
import logging
import weapons
import numbers
import effects
import random
import damage
import timers
import logic
import zones
import alife
import items
import menus
import maps
import copy
import time
import json
import os

try:
	import render_los
	CYTHON_RENDER_LOS = True
except:
	CYTHON_RENDER_LOS = False

def load_life(life):
	with open(os.path.join(LIFE_DIR,life+'.json'),'r') as e:
		return json.loads(''.join(e.readlines()))

def calculate_base_stats(life):
	"""Calculates and returns intital stats for `life`."""
	stats = {'arms': None,
		'legs': None,
		'melee': None,
		'speed_max': LIFE_MAX_SPEED}
	
	_flags = life['flags'].split('|')
	
	for flag in _flags:		
		if flag.count('['):
			if not flag.count('[') == flag.count(']'):
				raise Exception('No matching brace in ALife type %s: %s' % (species_type, flag))
			
			stats[flag.lower().partition('[')[0]] = flag.partition('[')[2].partition(']')[0].split(',')
		
		elif flag == 'HUNGER':
			life['eaten'] = []	
	
	if not 'hands' in life:
		life['hands'] = []
	
	life['life_flags'] = life['flags']
	
	stats['base_speed'] = numbers.clip(LIFE_MAX_SPEED-len(stats['legs']), 0, LIFE_MAX_SPEED)
	stats['speed_max'] = stats['base_speed']
	
	for var in life['vars'].split('|'):
		key,val = var.split('=')
		
		try:
			life[key] = int(val)
			continue
		except:
			pass
		
		try:
			life[key] = life[val]
			continue
		except:
			pass
		
		try:
			life[key] = val
			continue
		except:
			pass
	
	return stats

def get_max_speed(life):
	"""Returns max speed based on items worn."""
	_speed = life['base_speed']
	_legs = get_legs(life)
	
	for limb in life['body']:
		if limb in _legs[:]:
			_legs.remove(limb)
			_limb = life['body'][limb]
			_speed += _limb['cut']
	
			for item in [get_inventory_item(life, i) for i in get_items_attached_to_limb(life, limb)]:
				if not 'mods' in item:
					continue
				
				if 'speed' in item['mods']:
					_speed -= item['mods']['speed']
	
	_speed += len(_legs)*2
	
	return numbers.clip(_speed, 0, 255)

def initiate_raw(life):
	life['raw'] = alife.rawparse.read(os.path.join(LIFE_DIR, life['raw_name']+'.dat'))

def initiate_needs(life):
	life['needs'] = []
	
	alife.survival.add_needed_item(life,
	                               {'type': 'drink'},
	                               satisfy_if=action.make_small_script(function='retrieve_from_memory',
	                                                                   args={'key': 'thirsty'}),
	                               satisfy_callback=action.make_small_script(function='consume'))
	alife.survival.add_needed_item(life,
	                               {'type': 'food'},
	                               satisfy_if=action.make_small_script(function='retrieve_from_memory',
	                                                                   args={'key': 'hungry'}),
	                               satisfy_callback=action.make_small_script(function='consume'))

def initiate_life(name):
	"""Loads (and returns) new life type into memory."""
	if name in LIFE_TYPES:
		logging.warning('Life type \'%s\' is already loaded. Reloading...' % name)
	
	life = load_life(name)
	life['raw_name'] = name
	#try:
	initiate_raw(life)
	#except:
	#	print 'FIXME: Exception on no .dat for life'
	
	if not 'icon' in life:
		logging.warning('No icon set for life type \'%s\'. Using default (%s).' % (name,DEFAULT_LIFE_ICON))
		_life['tile'] = DEFAULT_LIFE_ICON
	
	if not 'flags' in life:
		logging.error('No flags set for life type \'%s\'. Errors may occur.' % name)
	
	for key in life:
		if isinstance(life[key],unicode):
			life[key] = str(life[key])	
	
	life.update(calculate_base_stats(life))
	
	LIFE_TYPES[name] = life
	
	return life

def initiate_limbs(life):
	"""Creates skeleton of a character and all related variables. Returns nothing."""
	body = life['body']
	
	for limb in body:
		#Unicode fix:
		_val = body[limb].copy()
		del body[limb]
		body[str(limb)] = _val
		body[limb] = body[str(limb)]
		body[limb]['flags'] = body[limb]['flags'].split('|')
		body[limb]['holding'] = []
		body[limb]['cut'] = 0
		body[limb]['bleeding'] = 0
		body[limb]['bruised'] = False
		body[limb]['broken'] = False
		body[limb]['artery_ruptured'] = False
		body[limb]['pain'] = 0
		body[limb]['wounds'] = []
		
		if not 'parent' in body[limb]:
			continue
		
		if not 'children' in body[body[limb]['parent']]:
			body[body[limb]['parent']]['children'] = [str(limb)]
		else:
			body[body[limb]['parent']]['children'].append(str(limb))

def get_raw(life, section, identifier):
	if not alife.rawparse.raw_has_section(life, section):
		return []
	
	return life['raw']['sections'][section][identifier]

def execute_raw(life, section, identifier, break_on_true=False, break_on_false=True, **kwargs):
	""" break_on_false is defaulted to True because the majority of situations in which this
	function is used involves making sure all the required checks return True.
	
	break_on_true doesn't see much usage - it implies that if one statement returns true, then
	the rest do not need to be checked and True is returned.
	
	"""
	for rule in get_raw(life, section, identifier):
		if rule['string']:
			return rule['string'].lower()
		
		_func_args = {}
		for value in rule['values']:
			if 'key' in value:
				_func_args[value['key']] = value['value']
		
		if rule['no_args']:
			if _func_args:
				_func = rule['function'](**_func_args)
			else:
				_func = rule['function']()
		elif rule['self_call']:
			if _func_args:
				_func = rule['function'](life, **_func_args)
			else:
				_func = rule['function'](life)
		else:
			_func = rule['function'](life, **kwargs)
		
		if rule['true'] == '*' or _func == rule['true']:
			for value in rule['values']:
				if 'flag' in value:
					brain.knows_alife_by_id(life, kwargs['life_id'])[value['flag']] += value['value']
			
			if break_on_true:
				if _func:
					return _func
				
				return True
		elif break_on_false:
			return False
	
	if break_on_true:
		return False
	
	return True

def generate_likes(life):
	return copy.deepcopy(POSSIBLE_LIKES)

def get_limb(life, limb):
	"""Helper function. Finds and returns a limb."""
	return life['body'][limb]

def get_all_limbs(body):
	"""Deprecated helper function. Returns all limbs."""
	#logging.warning('Deprecated: life.get_all_limbs() will be removed in next version.')
	
	return body

def create_and_update_self_snapshot(life):
	_ss = snapshots.create_snapshot(life)
	snapshots.update_self_snapshot(life,_ss)
	
	#logging.debug('%s updated their snapshot.' % ' '.join(life['name']))

def create_life(type, position=(0,0,2), name=None, map=None):
	"""Initiates and returns a deepcopy of a life type."""
	if not type in LIFE_TYPES:
		raise Exception('Life type \'%s\' does not exist.' % type)
	
	#TODO: Any way to get rid of this call to `copy`?
	_life = copy.deepcopy(LIFE_TYPES[type])
	
	if not name and _life['name'] == '$FIRST_AND_LAST_NAME_FROM_SPECIES':
		_life['name'] = language.generate_first_and_last_name_from_species(_life['species'])
	elif name:
		_life['name'] = name
	
	_life['id'] = str(WORLD_INFO['lifeid'])
	
	_life['speed'] = _life['speed_max']
	_life['pos'] = list(position)
	_life['prev_pos'] = list(position)
	_life['realpos'] = list(position)
	_life['velocity'] = [0.0, 0.0, 0.0]
	
	LIFE_MAP[_life['pos'][0]][_life['pos'][1]].append(_life['id'])
	
	_life['animation'] = {}
	_life['path'] = []
	_life['path_state'] = None
	_life['actions'] = []
	_life['conversations'] = []
	_life['contexts'] = [] #TODO: Make this exclusive to the player
	_life['dialogs'] = []
	_life['encounters'] = []
	_life['heard'] = []
	_life['item_index'] = 0
	_life['inventory'] = []
	_life['flags'] = {}
	_life['state'] = 'idle'
	_life['state_tier'] = 9999
	_life['state_flags'] = {}
	_life['states'] = []
	_life['gravity'] = 0.05
	_life['targeting'] = None
	_life['pain_tolerance'] = 15
	_life['asleep'] = 0
	_life['blood'] = calculate_max_blood(_life)
	_life['consciousness'] = 100
	_life['dead'] = False
	_life['snapshot'] = {}
	_life['shoot_timer'] = 0
	_life['shoot_timer_max'] = 300
	_life['strafing'] = False
	_life['recoil'] = 0
	_life['stance'] = 'standing'
	_life['strafing'] = False
	_life['aim_at'] = _life['id']
	_life['discover_direction_history'] = []
	_life['discover_direction'] = 270
	_life['tickers'] = {}
	_life['think_rate_max'] = LIFE_THINK_RATE
	_life['think_rate'] = random.randint(0, _life['think_rate_max'])
	
	#Various icons...
	# expl = #chr(15)
	# up   = chr(24)
	# down = chr(25)
	
	#ALife
	_life['know'] = {}
	_life['know_items'] = {}
	_life['memory'] = []
	_life['known_chunks'] = {}
	_life['known_camps'] = {}
	_life['known_groups'] = []
	_life['camp'] = None
	_life['tempstor2'] = {}
	_life['job'] = None
	_life['jobs'] = []
	_life['task'] = None
	_life['completed_tasks'] = []
	_life['completed_jobs'] = []
	_life['rejected_jobs'] = []
	_life['group'] = None
	_life['likes'] = generate_likes(_life)
	_life['dislikes'] = {}
	_life['needs'] = []
	_life['goals'] = {}
	
	_life['stats'] = {}
	alife.stats.init(_life)
	
	initiate_needs(_life)
	
	#Stats
	_life['engage_distance'] = 15+random.randint(-5, 5)
	
	initiate_limbs(_life)
	WORLD_INFO['lifeid'] += 1
	LIFE[_life['id']] = _life
	
	return _life

def ticker(life, name, time, fire=False):
	if name in life['tickers']:
		if life['tickers'][name]:
			life['tickers'][name] -= 1
			return False
		else:
			del life['tickers'][name]
			return True
	else:
		life['tickers'][name] = time
		return fire

def focus_on(life):
	SETTINGS['following'] = life['id']
	
	gfx.camera_track(life['pos'])
	gfx.refresh_window()
	
	LOS_BUFFER[0] = maps._render_los(WORLD_INFO['map'],
	                                 LIFE[SETTINGS['following']]['pos'],
	                                 alife.sight.get_vision(LIFE[SETTINGS['following']])*2,
	                                 cython=True)

def sanitize_heard(life):
	del life['heard']

def sanitize_know(life):
	for entry in life['know'].values():
		entry['life'] = entry['life']['id']
		
		if alife.brain.alife_has_flag(life, entry['life'], 'search_map'):
			alife.brain.unflag_alife(life, entry['life'], 'search_map')

def prepare_for_save(life):
	_delete_keys = ['raw', 'actions', 'dialogs']
	_sanitize_keys = {'heard': sanitize_heard,
		'know': sanitize_know}
	
	for key in life.keys():#_delete_keys:
		if key in _sanitize_keys:
			_sanitize_keys[key](life)
		elif key in _delete_keys:
			del life[key]
	
	#print life.keys()
	#_save_string = json.dumps(life)

def post_save(life):
	'''This is for getting the entity back in working order after a save.'''
	life['heard'] = []
	life['actions'] = []
	life['path'] = []
	life['dialogs'] = []
	
	for entry in life['know'].values():
		entry['life'] = LIFE[entry['life']]
	
	#NOTE: This section is for updating life entities after keys have been added
	if not 'known_groups' in life:
		life['known_groups'] = []
	
	initiate_raw(life)

def load_all_life():
	for life in LIFE.values():
		post_save(life)

def save_all_life():
	for life in LIFE.values():
		prepare_for_save(life)
		
		for key in life.keys():
			try:
				json.dumps(life[key])
			except:
				logging.critical('Life key cannot be offloaded: %s' % key)
				raise Exception(key)
	
	_life = json.dumps(LIFE)
	
	for life in LIFE.values():
		post_save(life)
	
	return _life

def show_debug_info(life):
	print ' '.join(life['name'])
	print '*'*10
	print 'Dumping memory'
	print '*'*10
	for memory in life['memory']:
		print memory['target'], memory['text']

def get_engage_distance(life):
	return 0

def change_state(life, state, tier):
	if life['state'] == state:
		return False
	
	logging.debug('%s state change: %s (%s) -> %s (%s)' % (' '.join(life['name']), life['state'], life['state_tier'], state, tier))
	life['state'] = state
	life['state_flags'] = {}
	life['state_tier'] = tier
	
	life['states'].append(state)
	if len(life['states'])>SETTINGS['state history size']:
		life['states'].pop(0)

def set_animation(life, animation, speed=2, loops=0):
	life['animation'] = {'images': animation,
		'speed': speed,
		'speed_max': speed,
		'index': 0,
		'loops': loops}
	
	#logging.debug('%s set new animation (%s loops).' % (' '.join(life['name']), loops))

def tick_animation(life):
	if not life['animation']:
		return life['icon']
	
	if life['animation']['speed']:
		life['animation']['speed'] -= 1
	else:
		life['animation']['index'] += 1
		life['animation']['speed'] = life['animation']['speed_max']
		
		if life['animation']['index']>=len(life['animation']['images']):
			if life['animation']['loops']:
				life['animation']['loops'] -= 1
				life['animation']['index'] = 0
				life['animation']['speed'] = 0
			else:
				life['animation'] = {}
				return life['icon']
		
	return life['animation']['images'][life['animation']['index']]

def get_current_camp(life):
	return life['known_camps'][life['camp']]

def get_current_known_chunk(life):
	_chunk_id = get_current_chunk_id(life)
	
	if _chunk_id in life['known_chunks']:
		return life['known_chunks'][_chunk_id]
	
	return False

def get_current_known_chunk_id(life):
	_chunk_key = '%s,%s' % ((life['pos'][0]/WORLD_INFO['chunk_size'])*WORLD_INFO['chunk_size'], (life['pos'][1]/WORLD_INFO['chunk_size'])*WORLD_INFO['chunk_size'])
	
	if _chunk_key in life['known_chunks']:
		return _chunk_key
	
	return False

def get_current_chunk(life):
	_chunk_id = get_current_chunk_id(life)
	
	return maps.get_chunk(_chunk_id)

def get_current_chunk_id(life):
	return '%s,%s' % ((life['pos'][0]/WORLD_INFO['chunk_size'])*WORLD_INFO['chunk_size'], (life['pos'][1]/WORLD_INFO['chunk_size'])*WORLD_INFO['chunk_size'])

def get_known_life(life, id):
	if id in life['know']:
		return life['know'][id]
	
	return False

def create_conversation(life, gist, matches=[], radio=False, msg=None, **kvargs):
	#logging.debug('%s started new conversation (%s)' % (' '.join(life['name']), gist))
	
	_conversation = {'gist': gist,
		'from': life,
		'start_time': WORLD_INFO['ticks'],
		'timeout_callback': None,
		'id': time.time()}
	_conversation.update(kvargs)
	_for_player = False
	
	for ai in [LIFE[i] for i in LIFE]:
		#TODO: Do we really need to support more than one match?
		#TODO: can_hear
		if ai['id'] == life['id']:
			continue
		
		if not alife.stats.can_talk_to(life, ai['id']):
			continue
		
		if not alife.sight.can_see_position(ai, life['pos']):
			if not get_all_inventory_items(life, matches=[{'name': 'radio'}]):
				continue
		
		_does_match = True
		for match in matches:
			for key in match:
				if not key in ai or not ai[key] == match[key]:
					_does_match = False
					#logging.debug('\t%s did not meet matches for this conversation' % ' '.join(ai['name']))
					break
		
			if not _does_match:
				break
		
		if not _does_match:
			continue
		
		if 'player' in ai:
			_for_player = True
		
		hear(ai, _conversation)
	
	if msg:
		say(life, msg, context=_for_player)

def get_surrounding_unknown_chunks(life, distance=1):
	_current_chunk_id = get_current_chunk_id(life)
	_surrounding_chunks = []
	_start_x,_start_y = [int(value) for value in _current_chunk_id.split(',')]
	
	for y in range(-distance,distance+1):
		for x in range(-distance,distance+1):
			if not x and not y:
				continue
			
			_next_x = _start_x+(x*WORLD_INFO['chunk_size'])
			_next_y = _start_y+(y*WORLD_INFO['chunk_size'])
			
			if _next_x<0 or _next_x>=MAP_SIZE[0]:
				continue
				
			if _next_y<0 or _next_y>=MAP_SIZE[1]:
				continue
			
			_chunk_key = '%s,%s' % (_next_x, _next_y)
			
			if _chunk_key in life['known_chunks']:
				continue
			
			_surrounding_chunks.append(_chunk_key)
	
	return _surrounding_chunks

def hear(life, what):
	what['age'] = 0
	life['heard'].append(what)
	
	if 'player' in life:		
		_menu = []
		_context = contexts.create_context(life, what, timeout_callback=what['timeout_callback'])
		
		for reaction in _context['reactions']:
			if reaction['type'] == 'say':
				_menu.append(menus.create_item('single',
					reaction['type'],
					reaction['text'],
					target=what['from'],
					communicate=reaction['communicate'],
					life=life))
			elif reaction['type'] == 'action':
				if 'communicate' in reaction:
					_menu.append(menus.create_item('single',
						reaction['type'],
						reaction['text'],
						target=what['from'],
						action=reaction['action'],
						score=reaction['score'],
						delay=reaction['delay'],
						communicate=reaction['communicate'],
						life=life))
				else:
					_menu.append(menus.create_item('single',
						reaction['type'],
						reaction['text'],
						target=what['from'],
						action=reaction['action'],
						score=reaction['score'],
						delay=reaction['delay'],
						life=life))
			elif reaction['type'] == 'dialog':
				life['dialogs'].append(reaction)
		
		if _menu:
			_context['items'] = _menu
			life['contexts'].append(_context)
			life['shoot_timer'] = DEFAULT_CONTEXT_TIME
	
	#logging.debug('%s heard %s: %s' % (' '.join(life['name']), ' '.join(what['from']['name']) ,what['gist']))

def avoid_react(reaction):
	life = reaction['life']
	target = reaction['target']
	
	#TODO: Target
	add_action(life,
		{'action': 'communicate',
			'what': 'resist',
			'target': target},
		900,
		delay=0)

def react(reaction):
	life = reaction['life']
	type = reaction['key']
	text = reaction['values'][0]
	target = reaction['target']
	score = reaction.get('score', 0)

	if 'communicate' in reaction:
		for comm in reaction['communicate'].split('|'):
			add_action(life,
				{'action': 'communicate',
					'what': comm,
					'target': target},
				score-1,
				delay=0)

	if type == 'say':
		say(life, text)
	elif type == 'action':
		add_action(life,
			reaction['action'],
			reaction['score'],
			delay=reaction['delay'])

	menus.delete_menu(ACTIVE_MENU['menu'])

def say(life, text, action=False, volume=30, context=False):
	if action:
		set_animation(life, ['\\', '|', '/', '-'])
		text = text.replace('@n', language.get_introduction(life))
		_style = 'action'
	else:
		set_animation(life, ['!'], speed=8)
		text = '%s: %s' % (' '.join(life['name']),text)
		_style = 'speech'
	
	if SETTINGS['following']:
		if numbers.distance(LIFE[SETTINGS['following']]['pos'],life['pos'])<=volume:
			if context:
				_style = 'important'
			
			gfx.message(text, style=_style)
			
			if action:
				logic.show_event(text, life=life)

def memory(life, gist, *args, **kvargs):
	_entry = {'text': gist, 'id': WORLD_INFO['memoryid']}
	_entry['time_created'] = WORLD_INFO['ticks']
	WORLD_INFO['memoryid'] += 1
	
	for arg in args:
		_entry.update(arg)
	
	_entry.update(kvargs)
	
	if 'question' in _entry:
		_entry['answered'] = []
		_entry['asked'] = {}
		_entry['ignore'] = []
		#_entry['last_asked'] = -1000
	
	life['memory'].append(_entry)
	#logging.debug('%s added a new memory: %s' % (' '.join(life['name']), gist))
	
	if 'target' in kvargs:
		create_and_update_self_snapshot(LIFE[kvargs['target']])
	
	return _entry['id']

def has_dialog(life):
	for dialog in [d for d in life['dialogs'] if d['enabled']]:
		#if dialog['speaker'] == life['id']:
		return True
	
	return False

def has_group(life):
	return life['group']

def can_ask(life, target_id, question_id):
	question = get_memory_via_id(life, question_id)
	
	if not target_id:
		print 'cant ask because of wrong id'
		return False
	
	if target_id in question['asked'] and WORLD_INFO['ticks']-question['asked'][target_id] < 900:
		return False
	
	return True

def get_memory(life, matches={}):
	_memories = []
	
	for memory in life['memory']:
		_break = False
		for key in matches:
			if not key in memory or not (matches[key] == '*' or memory[key] == matches[key]):
				_break = True
				break
		
		if not _break:
			_memories.append(memory)
			
	return _memories

def get_memory_via_id(life, memory_id):
	for memory in life['memory']:
		if memory['id'] == memory_id:
			return memory
	
	raise Exception('Invalid memory passed to get_memory_via_id(): %s' % memory_id)

def delete_memory(life, matches={}):
	for _memory in get_memory(life, matches=matches):
		life['memory'].remove(_memory)
		logging.debug('%s deleted memory: %s' % (' '.join(life['name']), _memory['text']))

def create_question(life, gist, question, answer_match, match_gist_only=False, answer_all=False, interest=0):
	question['question'] = True
	if not isinstance(answer_match, list):
		answer_match = [answer_match]
	
	question['answer_match'] = answer_match
	_match = {'text': gist}
	
	if not match_gist_only:
		_match.update(question)
	
	if get_memory(life, matches=_match):
		return False
	
	if interest:
		if not 'target' in question:
			raise Exception('No target in question when `interest` > 0. Stopping (Programmer Error).')
		
		brain.add_impression(life, question['target'], 'talk', {'influence': alife.stats.get_influence_from(life, question['target'])})
	
	question['answer_all'] = answer_all
	_id = memory(life, gist, question)
	
	logging.debug('Creating question...')
	return _id

def get_questions(life, target=None, no_filter=False, skip_answered=True):
	_questions = []
	
	for question in get_memory(life, matches={'question': True}):
		if skip_answered and question['answered']:
			continue
		
		#TODO: no_filter kills the loop entirely?
		if not no_filter and target and target in question['ignore']:
			continue
		
		_questions.append(question)
	
	return _questions

def get_recent_memories(life,number):
	return life['memory'][len(life['memory'])-number:]

def create_recent_history(life,depth=10):
	_story = ''
	
	_line = '%s %s ' % (life['name'][0],life['name'][1])
	for entry in life['memory'][len(life['memory'])-depth:]:
		_line += '%s.' % entry['text']
	
	return _line	

def crouch(life):
	if life['stance'] == 'standing':
		_delay = 5
	elif life['stance'] == 'crawling':
		_delay = 15
	else:
		return False
	
	set_animation(life, ['n', '@'], speed=_delay/2)
	add_action(life,{'action': 'crouch'},
		200,
		delay=_delay)

def stand(life):
	if life['stance'] == 'crouching':
		_delay = 5
	elif life['stance'] == 'crawling':
		_delay = 15
	else:
		return False
	
	set_animation(life, ['^', '@'], speed=_delay/2)
	add_action(life,{'action': 'stand'},
		200,
		delay=_delay)

def crawl(life):
	if life['stance'] == 'standing':
		_delay = 15
	elif life['stance'] == 'crouching':
		_delay = 5
	else:
		return False
	
	set_animation(life, ['v', '@'], speed=_delay/2)
	add_action(life,{'action': 'crawl'},
		200,
		delay=_delay)

def stop(life):
	clear_actions(life)
	life['path'] = []

def path_dest(life):
	"""Returns the end of the current path."""
	if not life['path']:
		return None
	
	return tuple(life['path'][len(life['path'])-1])

def can_traverse(life, pos):
	if WORLD_INFO['map'][pos[0]][pos[1]][life['pos'][2]+1]:
		if WORLD_INFO['map'][pos[0]][pos[1]][life['pos'][2]+2]:
			return False
		
		return True
	
	if not WORLD_INFO['map'][pos[0]][pos[1]][life['pos'][2]]:
		if WORLD_INFO['map'][pos[0]][pos[1]][life['pos'][2]-1]:
			return True
	
	if WORLD_INFO['map'][pos[0]][pos[1]][life['pos'][2]]:
		return True
	
	return False

def can_walk_to(life, pos):
	if len(pos) == 3:
		pos = list(pos)
	else:
		pos = list(pos)
		pos.append(life['pos'][2])
		
	_z1 = zones.get_zone_at_coords(life['pos'])
	_z2 = zones.get_zone_at_coords(pos)
	
	if not _z2:
		#TODO: Don't use this, dingus! Wow!
		for z in [life['pos'][2]-1, life['pos'][2]+1]:
			_z2 = zones.get_zone_at_coords((pos[0], pos[1], z))
			
			if _z2:
				break
	
	if not _z2:
		return False
	
	return zones.can_path_to_zone(_z1, _z2)

def push(life, direction, speed, friction=0.05, _velocity=0):
	"""Sets new velocity for an entity. Returns nothing."""
	velocity = numbers.velocity(direction, speed)
	velocity[2] = _velocity
	
	life['friction'] = friction
	life['velocity'] = velocity
	life['realpos'] = life['pos'][:]
	life['path'] = []
	
	logging.debug('%s flies off in an arc! (%s)' % (' '.join(life['name']), life['velocity']))

def calculate_velocity(life):
	if not sum([abs(i) for i in life['velocity']]):
		return False
	
	_next_pos = (int(life['pos'][0]+life['velocity'][0]), int(life['pos'][1]+life['velocity'][1]))
	_last_pos = life['pos'][:]
	
	for pos in drawing.diag_line(life['pos'], _next_pos):
		life['velocity'][2] -= life['velocity'][2]*life['gravity']
		
		if items.collision_with_solid(life, (pos[0], pos[1], 0)):
			life['velocity'] = [0, 0, 0]
			return False
		
		life['pos'][0] = pos[0]
		life['pos'][1] = pos[1]
	
		_min_x_vel, _min_y_vel, _max_x_vel, _max_y_vel = items.get_min_max_velocity(life)
		
		if 0<life['velocity'][0]<1 or -1<life['velocity'][0]<0:
			life['velocity'][0] = 0
		
		if 0<life['velocity'][1]<1 or -1<life['velocity'][1]<0:
			life['velocity'][1] = 0
		
		life['velocity'][0] -= numbers.clip(life['velocity'][0]*0.2, _min_x_vel, _max_x_vel)
		life['velocity'][1] -= numbers.clip(life['velocity'][1]*0.2, _min_y_vel, _max_y_vel)
		
		if not sum([abs(i) for i in life['velocity']]):
			return False
	
		print life['velocity']
	
	return True

def walk_to(life, position):
	clear_actions(life)
	add_action(life,{'action': 'move',
          'to': position},
          200)

def walk(life, to=None, path=None):
	"""Performs a single walk tick. Waits or returns success of life.walk_path()."""
	if life['speed']>0:
		if life['stance'] == 'standing':
			life['speed'] -= 1
		elif life['stance'] == 'crouching':
			life['speed'] -= 0.5
		elif life['stance'] == 'crawling':
			life['speed'] -= 0.3
			
		return False
	elif life['speed']<=0:
		life['speed_max'] = get_max_speed(life)
		life['speed'] = life['speed_max']
		
		if life['recoil'] < get_max_speed(life):
			life['recoil'] = get_max_speed(life)
	
	_dest = path_dest(life)
	
	if path:
		life['path'] = path
		life['path_state'] = life['state']
	elif to and (not _dest or not (_dest[0],_dest[1]) == tuple(to)):
		_stime = time.time()
		
		_zone = can_walk_to(life, to)
		if _zone:
			life['path'] = pathfinding.create_path(life, life['pos'], to, _zone)
			life['path_state'] = life['state']
		#else:
		#	logging.warning('%s: Can\'t walk there.' % ' '.join(life['name']))
		#print 'total',time.time()-_stime
	
	life['prev_pos'] = life['pos'][:]
	return walk_path(life)

def walk_path(life):
	"""Walks and returns whether the path is finished or not."""
	if life['path']:
		_pos = list(life['path'].pop(0))
		_nfx = _pos[0]
		_nfy = _pos[1]
		
		if WORLD_INFO['map'][_nfx][_nfy][life['pos'][2]+1] and not WORLD_INFO['map'][_nfx][_nfy][life['pos'][2]+2]:
			life['pos'][2] += 1
		elif not WORLD_INFO['map'][_nfx][_nfy][life['pos'][2]] and WORLD_INFO['map'][_nfx][_nfy][life['pos'][2]-1]:
			life['pos'][2] -= 1
		
		if life['id'] in LIFE_MAP[life['pos'][0]][life['pos'][1]]:
			LIFE_MAP[life['pos'][0]][life['pos'][1]].remove(life['id'])
		
		_old_chunk = get_current_chunk_id(life)
		life['pos'][0] = _pos[0]
		life['pos'][1] = _pos[1]
		_new_chunk = get_current_chunk_id(life)
		
		if not _old_chunk == _new_chunk:
			maps.leave_chunk(_old_chunk, life['id'])
		
		maps.enter_chunk(_new_chunk, life['id'])
		
		life['realpos'] = life['pos'][:]
		LIFE_MAP[life['pos'][0]][life['pos'][1]].append(life['id'])
		
		#if SETTINGS['following'] == life['id']:
		#	#LOS_BUFFER[0] = maps._render_los(WORLD_INFO['map'], LIFE[SETTINGS['following']]['pos'], cython=True)
		#	gfx.redraw_los()
		
		if life['path']:
			return False
		else:
			return True
	else:
		#TODO: Collision with wall
		return True

def perform_collisions(life):
	"""Performs gravity. Returns True if falling."""
	if not WORLD_INFO['map'][life['pos'][0]][life['pos'][1]][life['pos'][2]]:
		if WORLD_INFO['map'][life['pos'][0]][life['pos'][1]][life['pos'][2]-1]:
			life['pos'][2] -= 1
			
			return True
		
		if not life['gravity']:
			life['falling_startzpos'] = life['pos'][2]
			
			if life.has_key('player'):
				gfx.message('You begin to fall...')
		
		life['gravity'] = WORLD_INFO['world gravity']
			
	#elif life['gravity']:
	#	life['gravity'] = 0
	#	
	#	_fall_dist = life['falling_startzpos']-life['pos'][2]
	#	
	#	if not damage_from_fall(life,_fall_dist) and life.has_key('player'):
	#		gfx.message('You land.')
	
	#if life['gravity']:
	#	life['realpos'][2] -= WORLD_INFO['world gravity']
	#	life['pos'][2] = int(life['realpos'][2])
	
	return False

def get_highest_action(life):
	"""Returns highest action in the queue."""	
	if life['actions'] and life['actions'][0]:
		return life['actions'][0]
	else:
		return None

def clear_actions_matching(life,matches):
	for match in matches[:]:
		for action in life['actions']:
			for key in match:
				if key in action['action'] and match[key] == action['action'][key]:
					life['actions'].remove(action)
					#print 'Removed matched item: ',action
					break

def clear_actions(life,matches=[]):
	"""Clears all actions and prints a cancellation message for the highest scoring action."""
	
	if matches:
		clear_actions_matching(life,matches)
		return True
	else:
		clear_actions_matching(life,matches=[{'action': 'move'}])
		clear_actions_matching(life,matches=[{'action': 'dijkstra_move'}])
		return True

def find_action(life,matches=[{}]):
	_matching_actions = []
	
	for action in [action['action'] for action in life['actions']]:
		_break = False
		
		for match in matches:
			for key in match:
				if not key in action or not action[key] == match[key]:
					_break = True
					break
			
			if _break:
				break
				
			_matching_actions.append(action)
	
	return _matching_actions

def delete_action(life,action):
	"""Deletes an action."""
	_action = {'action': action['action'],
		'score': action['score'],
		'delay': action['delay'],
		'delay_max': action['delay_max']}
	
	life['actions'].remove(_action)

def add_action(life,action,score,delay=0):
	"""Creates new action. Returns True on success."""
	_tmp_action = {'action': action,'score': score}
	
	if _tmp_action in life['actions']:
		return False
	
	_tmp_action['delay'] = delay
	_tmp_action['delay_max'] = delay
	
	if _tmp_action in life['actions']:
		return False
	
	_index = 0
	for queue_action in life['actions']:
		if score > queue_action['score']:
			break
		
		_index += 1
	
	life['actions'].insert(_index,_tmp_action)	
	
	return True

def perform_action(life):
	"""Executes logic based on top action. Returns True on success."""
	action = get_highest_action(life)
	
	if not action:
		return False
	
	_action = action.copy()
	
	#TODO: What's happening here?
	if not _action in life['actions']:
		return False

	if action['delay']:
		action['delay']-=1
		
		return False

	_score = _action['score']
	_delay = _action['delay']
	_action = _action['action']
	
	if _action['action'] == 'move':
		if tuple(_action['to']) == tuple(life['pos']) or walk(life, to=_action['to']):
			delete_action(life,action)
			
	elif _action['action'] == 'dijkstra_move':
		_path = []
		
		if not path_dest(life):
			if 'avoid_positions' in _action:
				_avoid_positions = _action['avoid_positions']
			else:
				_avoid_positions = []
			
			if 'avoid_chunks' in _action:
				_avoid_chunks = _action['avoid_chunks']
			else:
				_avoid_chunks = []
			
			if 'zones' in _action:
				_zones = _action['zones']
			else:
				_zones = [zones.get_zone_at_coords(life['pos'])]
			
			if 'debug' in _action and _action['debug']:
				SETTINGS['print dijkstra maps'] = True
			
			_path = zones.dijkstra_map(life['pos'],
			                           _action['goals'],
			                           _zones,
			                           rolldown=_action['rolldown'],
			                           max_chunk_distance=sight.get_vision(life)/WORLD_INFO['chunk_size'],
			                           avoid_positions=_avoid_positions,
			                           avoid_chunks=_avoid_chunks)
			
			if 'debug' in _action and _action['debug']:
				SETTINGS['print dijkstra maps'] = False
				print _path
		
		if walk(life, path=_path):
			delete_action(life,action)
	
	elif _action['action'] == 'stand':
		life['stance'] = 'standing'
		
		if 'player' in life:
			gfx.message('You stand up.')
		else:
			say(life,'@n stands up.',action=True)
		
		delete_action(life,action)
	
	elif _action['action'] == 'crouch':
		life['stance'] = 'crouching'
		
		if 'player' in life:
			gfx.message('You crouch down.')
		else:
			say(life,'@n crouches.',action=True)

		delete_action(life,action)
	
	elif _action['action'] == 'crawl':
		life['stance'] = 'crawling'
		
		if 'player' in life:
			gfx.message('You begin to crawl.')
		else:
			say(life,'@n starts to crawl.',action=True)
		
		delete_action(life,action)
	
	elif _action['action'] == 'pickupitem':
		direct_add_item_to_inventory(life,_action['item'],container=_action['container'])
		delete_action(life,action)
		
		set_animation(life, [',', 'x'], speed=6)
		
		if life.has_key('player'):
			if _action.has_key('container'):
				_item = items.get_item_from_uid(_action['item'])
				_container = items.get_item_from_uid(_action['container'])
				gfx.message('You store %s in %s.'
					% (items.get_name(_item), items.get_name(_container)))
	
	elif _action['action'] == 'dropitem':
		_name = items.get_name(get_inventory_item(life,_action['item']))
		
		if item_is_equipped(life,_action['item']):
			if 'player' in life:
				gfx.message('You take off %s.' % _name)
			else:
				say(life,'@n takes off %s.' % _name,action=True)
				
		_stored = item_is_stored(life,_action['item'])
		if _stored:
			_item = get_inventory_item(life,_action['item'])
			
			if life.has_key('player'):
				gfx.message('You remove %s from %s.' % (_name,_stored['name']))
			else:
				say(life,'@n takes off %s.' % _name,action=True)
		
		if life.has_key('player'):
			gfx.message('You drop %s.' % _name)
		else:
			say(life,'@n drops %s.' % _name,action=True)
		
		set_animation(life, ['o', ','], speed=6)
		drop_item(life, _action['item'])
		delete_action(life, action)
	
	elif _action['action'] == 'equipitem':
		_name = items.get_name(get_inventory_item(life,_action['item']))
		
		if not equip_item(life,_action['item']):
			delete_action(life,action)
			gfx.message('You can\'t wear %s.' % _name)
			
			return False
		
		_stored = item_is_stored(life, _action['item'])

		if _stored:
			if 'player' in life:
				gfx.message('You remove %s from your %s.' % (_name,_stored['name']))
			else:
				pass
		
		if 'player' in life:
			gfx.message('You put on %s.' % _name)
		else:
			say(life,'@n puts on %s.' % _name,action=True)
		
		set_animation(life, [';', '*'], speed=6)
		delete_action(life,action)
	
	elif _action['action'] == 'storeitem':
		_item_to_store_name = items.get_name(get_inventory_item(life,_action['item']))
		_item_to_store = get_inventory_item(life,_action['item'])
		_container_name = items.get_name(get_inventory_item(life,_action['container']))
		_container = get_inventory_item(life,_action['container'])
		
		remove_item_from_inventory(life,_action['item'])
		direct_add_item_to_inventory(life,_action['item'],container=_action['container'])
		
		if life.has_key('player'):
			gfx.message('You put %s into %s.' % (_item_to_store_name,_container_name))
		else:
			say(life,'@n stores %s in %s.' % (_item_to_store_name,_container_name),action=True)
		
		set_animation(life, [';', 'p'], speed=6)
		delete_action(life,action)
	
	elif _action['action'] == 'consumeitem':
		_item = get_inventory_item(life, _action['item'])
		consume_item(life, _action['item'])
		set_animation(life, [';', 'e'], speed=6)
		items.delete_item(_item)
		delete_action(life, action)
	
	elif _action['action'] == 'pickupequipitem':
		if not can_wear_item(life,_action['item']):
			if life.has_key('player'):
				gfx.message('You can\'t equip this item!')
			
			delete_action(life,action)
			
			return False
		
		item = items.get_item_from_uid(_action['item'])
		
		if life.has_key('player'):
			gfx.message('You equip %s from the ground.' % items.get_name(item))
		else:
			say(life,'@n puts on %s from the ground.' % _name,action=True)
			
		#TODO: Can we even equip this? Can we check here instead of later?
		_id = direct_add_item_to_inventory(life,_action['item'])
		equip_item(life,_id)
		set_animation(life, [',', '*'], speed=6)
		delete_action(life,action)
	
	elif _action['action'] == 'pickupholditem':
		_item = items.get_item_from_uid(_action['item'])
		_hand = get_limb(life, _action['hand'])
		
		if _hand['holding']:
			if life.has_key('player'):
				gfx.message('You\'re already holding something in your %s!' % _action['hand'])
		
			delete_action(life,action)
			
			return False
		
		_id = direct_add_item_to_inventory(life,_action['item'])
		_hand['holding'].append(_id)
		
		if 'player' in life:
			gfx.message('You hold %s in your %s.' % (items.get_name(_item) ,_action['hand']))
		else:
			say(life,'@n holds %s in their %s.' % (items.get_name(_item),_action['hand']),action=True)
		
		set_animation(life, [',', ';'], speed=6)
		delete_action(life,action)
	
	elif _action['action'] == 'removeandholditem':
		_hand = can_hold_item(life)
		
		if not _hand:
			if 'player' in life:
				gfx.message('You have no hands free to hold the %s.' % items.get_name(get_inventory_item(life,_action['item'])))
			
			delete_action(life, action)
			return False

		_dropped_item = remove_item_from_inventory(life,_action['item'])
		_id = direct_add_item_to_inventory(life, _dropped_item)
		_hand['holding'].append(_id)
		
		if 'player' in life:
			gfx.message('You hold %s.' % items.get_name(items.get_item_from_uid(_dropped_item)))
		
		set_animation(life, ['*', ';'], speed=6)
		delete_action(life,action)
	
	elif _action['action'] == 'holditemthrow':
		_dropped_item = drop_item(life,_action['item'])
		print _dropped_item
		_id = direct_add_item_to_inventory(life,_dropped_item)
		_action['hand']['holding'].append(_id)
		
		gfx.message('You aim %s.' % items.get_name(items.get_item_from_uid(_dropped_item)))
		life['targeting'] = life['pos'][:]
		
		delete_action(life,action)
		
	elif _action['action'] == 'reload':	
		_action['weapon'][_action['weapon']['feed']] = _action['ammo']['uid']
		_ammo = remove_item_from_inventory(life,_action['ammo']['uid'])
		_action['ammo']['parent'] = _action['weapon']['uid']
		
		if life.has_key('player'):
			gfx.message('You load a new %s into your %s.' % (_action['weapon']['feed'],_action['weapon']['name']))
		
		set_animation(life, [';', 'r'], speed=6)
		delete_action(life,action)
	
	elif _action['action'] == 'unload':
		_weapon = get_inventory_item(life, _action['weapon'])
		_ammo = items.get_item_from_uid(_weapon[_weapon['feed']])
		_hand = can_hold_item(life)
		
		if _hand:
			_id = direct_add_item_to_inventory(life, _ammo['uid'])
			del _ammo['parent']
			_hand['holding'].append(_id)
			_weapon[_weapon['feed']] = None
		else:
			if 'player' in life:
				gfx.message('You have no hands free to hold %s!' % items.get_name(_ammo))
				gfx.message('%s falls to the ground.' % items.get_name(_ammo))
			
			#TODO: Too hacky
			del _ammo['parent']
			_weapon[_weapon['feed']] = None
			_ammo['pos'] = life['pos'][:]
		
		set_animation(life, [';', 'u'], speed=6)
		delete_action(life,action)
	
	elif _action['action'] == 'refillammo':	
		_action['ammo']['rounds'].append(_action['round']['uid'])
		_action['round']['parent'] = _action['ammo']['uid']
		_round = remove_item_from_inventory(life, _action['round']['uid'])
		
		if life.has_key('player') and len(_action['ammo']['rounds'])>=_action['ammo']['maxrounds']:
			gfx.message('The magazine is full.')
		
		delete_action(life,action)
	
	elif _action['action'] == 'shoot':
		weapons.fire(life, _action['target'], limb=_action['limb'])
		
		#add_action(life,
		#	{'action': 'recoil'},
		#	5001,
		#	delay=weapons.get_recoil(life))
		
		delete_action(life,action)
	
	elif _action['action'] == 'bite':
		damage.bite(life, _action['target'], _action['limb'])
		
		delete_action(life,action)
	
	elif _action['action'] == 'block':
		delete_action(life,action)

	elif _action['action'] == 'communicate':
		speech.communicate(life, _action['what'], matches=[{'id': _action['target']['id']}])
		delete_action(life, action)

	elif _action['action'] == 'rest':
		delete_action(life, action)

	else:
		logging.warning('Unhandled action: %s' % _action['action'])
	
	return True

def kill(life, injury):
	if isinstance(injury, str) or isinstance(injury, unicode):
		life['cause_of_death'] = injury
		
		if 'player' in life:
			gfx.message('You die from %s.' % life['cause_of_death'])
		else:
			say(life, '@n dies from %s.' % life['cause_of_death'], action=True)
	else:
		life['cause_of_death'] = language.format_injury(injury)
		
		if 'player' in life:
			gfx.message('You die from %s.' % life['cause_of_death'])
		else:
			say(life, '@n dies from %s.' % life['cause_of_death'], action=True)
		
	logging.debug('%s dies: %s' % (life['name'][0], life['cause_of_death']))
		
	for ai in [LIFE[i] for i in LIFE if not i == life['id']]:
		if alife.sight.can_see_position(ai, life['pos']):
			memory(ai, 'death', target=life['id'])
	
	drop_all_items(life)
	life['dead'] = True
	timers.remove_by_owner(life)

def can_die_via_critical_injury(life):
	for limb in life['body']:
		_limb = life['body'][limb]
		if not 'CRUCIAL' in _limb['flags']:
			continue
		
		if _limb['pain']>=_limb['size']:
			return limb
	
	return False	

def hunger(life):
	if life['hunger']>0:
		life['hunger'] -= 1
	else:
		kill(life, 'starvation')
		return False

	return True

def thirst(life):
	if life['thirst']>0:
		life['thirst'] -= 1
	else:
		kill(life, 'dehydration')
		return False
	
	return True

def tick(life, source_map):
	"""Wrapper function. Performs all life-related logic. Returns nothing."""

	if life['dead']:
		return False
	
	if calculate_blood(life)<=0:
		kill(life,'bleedout')
				
		return False
	
	if 'HUNGER' in life['life_flags']:
		if not hunger(life):
			return False
		
		calculate_hunger(life)
		
	if 'THIRST' in life['life_flags']:
		if not thirst(life):
			return False
	
	life['recoil'] = numbers.clip(life['recoil']-alife.stats.get_recoil_recovery_rate(life), 0, 10)
	
	natural_healing(life)
	_bleeding_limbs = get_bleeding_limbs(life)
	if _bleeding_limbs:
		_bleed_score = sum([get_limb(life, l)['bleeding'] for l in _bleeding_limbs])*3
		
		if random.randint(0,50)<numbers.clip(_bleed_score, 0, 50):
			effects.create_splatter('blood', life['pos'])
	
	if life['asleep']:
		life['asleep'] -= 1
		
		if life['asleep']<=0:
			life['asleep'] = 0
			
			logging.debug('%s woke up.' % life['name'][0])
			
			if 'player' in life:
				gfx.message('You wake up.')
			else:
				say(life,'@n wakes up.',action=True)
		
		return False
	
	_crit_injury = can_die_via_critical_injury(life)
	if _crit_injury:
		kill(life, 'acute pain in the %s' % _crit_injury)
		
		return True
	
	if get_total_pain(life)>life['pain_tolerance']:		
		life['consciousness'] -= get_total_pain(life)-life['pain_tolerance']
		
		if life['consciousness'] <= 0:
			life['consciousness'] = 0
			
			if 'player' in life:
				gfx.message('The pain becomes too much.')
			
			pass_out(life)
			
			return False
	
	perform_collisions(life)
	
	_current_known_chunk_id = get_current_known_chunk_id(life)
	if _current_known_chunk_id:
		judgement.judge_chunk(life, _current_known_chunk_id, visited=True)
	else:
		judgement.judge_chunk(life, get_current_chunk_id(life), visited=True)
	
	if calculate_velocity(life):
		return False	
	
	if not 'player' in life:
		brain.think(life, source_map)
	else:
		brain.sight.look(life)
		alife.sound.listen(life)
		
		if life['job']:
			logging.warning('Should this be happening?')
			alife.jobs.work(life)
		
		for context in life['contexts'][:]:
			context['time'] -= 1
			
			if not context['time']:
				if context['timeout_callback']:
					context['timeout_callback'](context['from'])
				else:
					print 'No callback'
				
				life['contexts'].remove(context)
				logging.info('Context removed!')
	
	perform_action(life)

def attach_item_to_limb(body,id,limb):
	"""Attaches item to limb. Returns True."""
	body[limb]['holding'].append(id)
	logging.debug('%s attached to %s' % (id,limb))
	
	return True

def remove_item_from_limb(life,item,limb):
	"""Removes item from limb. Returns True."""
	life['body'][limb]['holding'].remove(item)
	create_and_update_self_snapshot(life)
	
	#logging.debug('%s removed from %s' % (item,limb))
	
	return True

def get_all_storage(life):
	"""Returns list of all containers in a character's inventory."""
	return [items.get_item_from_uid(item) for item in life['inventory'] if 'max_capacity' in items.get_item_from_uid(item)]

def get_all_visible_items(life):
	_ret = []
	
	[_ret.extend(limb['holding']) for limb in [life['body'][limb] for limb in life['body']] if limb['holding']]
	
	return _ret

def can_throw(life):
	"""Helper function for use where life.can_hold_item() is out of place. See referenced function."""
	return can_hold_item(life)

def throw_item(life, item_uid, target, speed):
	"""Removes item from inventory and sets its movement towards a target. Returns nothing."""
	_item = items.get_item_from_uid(remove_item_from_inventory(life, item_uid))
	
	direction = numbers.direction_to(life['pos'], target)
	items.move(_item, direction, speed)
	
	speech.announce(life, 'threw_an_item', public=True, item=item_uid, target=life['id'])
	
	if 'player' in life:
		gfx.message('You throw %s.' % items.get_name(_item))
	else:
		say('@n throws %s.' % items.get_name(_item))

def is_item_in_storage(life, item):
	"""Returns True if item is in storage, else False."""
	for container in get_all_storage(life):
		if item in container['storing']:
			return True
	
	return False

def can_put_item_in_storage(life,item_uid):
	"""Returns available storage container that can fit `item`. Returns False if none is found."""
	#TODO: Should return list of containers instead.
	#Whoa...
	item = items.get_item_from_uid(item_uid)
	
	for _item in [items.get_item_from_uid(_item) for _item in life['inventory']]:
		if _item['uid'] == item_uid:
			continue
		
		if items.can_store_item_in(item_uid, _item['uid']):
			return _item['uid']
	
	return False

def add_item_to_storage(life, item_uid, container=None):
	"""Adds item to free storage container.
	
	A specific container can be requested with the keyword argument `container`.
	
	"""
	_item = items.get_item_from_uid(item_uid)
	
	if not container:
		container = can_put_item_in_storage(life, item_uid)
	
	if not container:
		print 'cannot store',_item['name']
		return False
	
	#_container = items.get_item_from_uid(container)
	#_container['storing'].append(_item['uid'])
	#_container['capacity'] += _item['size']
	items.store_item_in(item_uid, container)
	
	brain.remember_item(life, _item)
	
	return True

def remove_item_in_storage(life, item_uid):
	"""Removes item from strorage. Returns storage container on success. Returns False on failure."""
	if 'stored_in' in items.get_item_from_uid(item_uid):
		items.remove_item_from_any_storage(item_uid)
	else:
		print 'incorrect: item not stored'
	
	#for _container in [items.get_item_from_uid(_container) for _container in life['inventory']]:
	#	if not 'max_capacity' in _container:
	#		continue
	#
	#	if id in _container['storing']:
	#		_container['storing'].remove(id)
	#		_container['capacity'] -= get_inventory_item(life,id)['size']
	#		logging.debug('Removed item #%s from %s' % (id,_container['name']))
	#		
	#		update_container_capacity(_container['uid'])
	#		return _container
	
	return False

def item_is_stored(life,id):
	"""Returns the container of an item. Returns False on failure."""
	for _container in [items.get_item_from_uid(_container) for _container in life['inventory']]:
		if not 'max_capacity' in _container:
			continue

		if id in _container['storing']:
			return _container
	
	return False

def item_is_worn(life, item_uid):
	item = ITEMS[item_uid]
	
	if not 'attaches_to' in item:
		return False
	
	if not 'owner' in item:
		return False
	
	for limb in item['attaches_to']:
		_limb = get_limb(life,limb)
		
		if item_uid in _limb['holding']:
			return limb
	
	return False

def can_wear_item(life, item_uid):
	"""Attaches item to limbs. Returns False on failure."""
	#TODO: Function name makes no sense.
	item = items.get_item_from_uid(item_uid)
	
	if not 'CAN_WEAR' in item['flags']:
		return False
	
	if item_is_worn(life, item_uid):
		return False
	
	for limb in item['attaches_to']:
		_limb = get_limb(life, limb)
		
		for _item in [items.get_item_from_uid(item_uid) for i in _limb['holding']]:
			if item_uid == _item['uid']:
				continue
			
			if not 'CANSTACK' in _item['flags']:
				logging.warning('%s will not let %s stack.' % (_item['name'],item['name']))
				return False

	return True

def get_inventory_item(life, item_id):
	"""Returns inventory item."""
	if not item_id in life['inventory'] and not item_is_stored(life, item_id):
		raise Exception('%s does not have item of id #%s'
			% (' '.join(life['name']), item_id))
	
	return items.get_item_from_uid(item_id)

def get_all_inventory_items(life,matches=None):
	"""Returns list of all inventory items.
	
	`matches` can be a list of dictionaries with criteria the item must meet. Only one needs to match.
	
	"""
	_items = []
	
	for item_id in life['inventory']:
		_item = items.get_item_from_uid(item_id)
		
		if find_action(life, matches=[{'item': item_id}]):
			continue
		
		if matches:
			if not perform_match(_item,matches):
				continue
		
		_items.append(_item)
		
	return _items

def get_all_unequipped_items(life, check_hands=True, matches=[], invert=False):
	_unequipped_items = []
	
	for entry in life['inventory']:
		item = get_inventory_item(life,entry)
		
		if matches:
			if not perform_match(item, matches):
				continue					
		
		if item_is_equipped(life,entry,check_hands=check_hands) == invert:
			_unequipped_items.append(entry)
	
	return _unequipped_items

def get_all_equipped_items(life, check_hands=True, matches=[]):
	return get_all_unequipped_items(life, check_hands=check_hands, matches=matches, invert=True)

def get_all_known_camps(life, matches={}):
	_camps = []
	
	for camp in life['known_camps'].values():
		for key in matches:
			if not key in camp or not camp[key] == matches[key]:
				break
			
			_camps.append(camp)
	
	return _camps

def _get_item_access_time(life, item):
	"""Returns the amount of time it takes to get an item from inventory."""
	#TODO: Where's it at on the body? How long does it take to get to it?
	if isinstance(item, dict):
		logging.debug('Getting access time for non-inventory item #%s' % item['uid'])
		
		#TODO: We kinda do this twice...
		_time = 0
		if 'max_capacity' in item:
			_time += item['capacity']
		
		if life['stance'] == 'standing':
			return item['size']+_time
		elif life['stance'] == 'crouching':
			return (item['size']+_time) * .8
		elif life['stance'] == 'crawling':
			return (item['size']+_time) * .6
	
	_item = get_inventory_item(life,item)
	
	if item_is_equipped(life,item):
		_time = _item['size']
		
		if 'max_capacity' in _item:
			_time += _item['capacity']
		
		return _time
	
	_stored = item_is_stored(life,item)
	if _stored:
		return get_item_access_time(life,_stored['uid'])+_item['size']
	
	return _item['size']

def get_item_access_time(life, item):
	#TODO: Don't breathe this!
	return numbers.clip(_get_item_access_time(life, item),1,999)/2

def direct_add_item_to_inventory(life, item_uid, container=None):
	"""Dangerous function. Adds item to inventory, bypassing all limitations normally applied. Returns inventory ID.
	
	A specific container can be requested with the keyword argument `container`.
	
	""" 
	#Warning: Only use this if you know what you're doing!
	if not isinstance(item_uid, str) and not isinstance(item_uid, unicode):
		raise Exception('Deprecated: String not passed as item UID')
	
	item = items.get_item_from_uid(item_uid)

	unlock_item(life, item_uid)
	life['item_index'] += 1
	item['parent_id'] = life['id']
	item['owner'] = life['id']
	
	if 'stored_in' in item:
		items.remove_item_from_any_storage(item_uid)
	
	life['inventory'].append(item_uid)
	
	if 'max_capacity' in item:
		logging.debug('Container found in direct_add')
		
		for uid in item['storing'][:]:
			logging.debug('\tAdding uid %s' % uid)
			
			life['inventory'].append(uid)
	
	#Warning: `container` refers directly to an item instead of an ID.
	if container:
		#Warning: No check is done to make sure the container isn't full!
		add_item_to_storage(life,item['uid'],container=container)
	
	return item_uid

def add_item_to_inventory(life, item_uid):
	"""Helper function. Adds item to inventory. Returns inventory ID."""
	if not isinstance(item_uid, str) and not isinstance(item_uid, unicode):
		raise Exception('Deprecated: String not passed as item UID')
	
	item = items.get_item_from_uid(item_uid)
	
	unlock_item(life, item_uid)
	item['parent_id'] = life['id']
	item['owner'] = life['id']
	
	if 'stored_in' in item:
		items.remove_item_from_any_storage(item_uid)
	
	if not add_item_to_storage(life, item_uid):
		if not can_wear_item(life, item_uid):
			return False
		else:
			life['inventory'].append(item_uid)
			equip_item(life,item_uid)
	else:
		life['inventory'].append(item_uid)
	
	if 'max_capacity' in item:
		for uid in item['storing'][:]:
			_item = items.get_item_from_uid(uid)
	
	logging.debug('%s got \'%s\'.' % (life['name'][0],item['name']))
	
	return item_uid

def remove_item_from_inventory(life, item_id):
	"""Removes item from inventory and all storage containers. Returns item."""
	item = get_inventory_item(life, item_id)
	
	_holding = is_holding(life, item_id)
	if _holding:
		_holding['holding'].remove(item_id)
		logging.debug('%s stops holding a %s' % (life['name'][0],item['name']))
		
	elif item_is_equipped(life, item_id):
		logging.debug('%s takes off a %s' % (life['name'][0],item['name']))
	
		if 'attaches_to' in item:
			for limb in item['attaches_to']:
				remove_item_from_limb(life,item['uid'],limb)
		
		item['pos'] = life['pos'][:]
	
	elif item_is_stored(life, item_id):
		item['pos'] = life['pos'][:]
		remove_item_in_storage(life, item_id)
	elif not item_is_stored(life, item_id):
		print 'item is NOT stored'
	
	if 'max_capacity' in item:
		logging.debug('Dropping container storing:')
		
		for _item in item['storing']:
			logging.debug('\tdropping %s' % _item)
			
			#item['storing'].remove(_item)
			#item['storing'].append(get_inventory_item(life,_item)['uid'])
			
			life['inventory'].remove(_item)
	
	life['speed_max'] = get_max_speed(life)
	
	if 'player' in life:
		menus.remove_item_from_menus({'id': item['uid']})
	
	logging.debug('Removed from inventory: %s' % item['name'])
	
	life['inventory'].remove(item['uid'])
	del item['parent_id']
	item['owner'] = None
	
	create_and_update_self_snapshot(life)
	
	return item_id

def is_consuming(life):
	return find_action(life, matches=[{'action': 'consumeitem'}])

def consume(life, item_id):
	if is_consuming(life):
		logging.warning('%s is already eating.' % ' '.join(life['name']))
		return False
	
	_item = items.get_item_from_uid(item_id)
	
	add_action(life, {'action': 'consumeitem',
		'item': item_id},
		200,
		delay=get_item_access_time(life, _item))
	
	return True

def can_consume(life, item_id):
	item = get_inventory_item(life, item_id)
	
	if item['type'] in ['food', 'drink']:
		return True
	
	return False

def consume_item(life, item_id):
	item = get_inventory_item(life, item_id)
	
	if not can_consume(life, item_id):
		return False
	
	life['eaten'].append(item)
	remove_item_from_inventory(life, item_id)
	alife.speech.announce(life, 'consume_item', public=True)
	logging.info('%s consumed %s.' % (' '.join(life['name']), items.get_name(item)))

	if 'player' in life:
		if item['type'] == 'food':
			gfx.message('You finsh eating.')
		else:
			gfx.message('You finsh drinking.')

def get_max_carry_size(life):
	_greatest = 0
	
	for storage in [s for s in get_all_storage(life)]:
		_capacity = storage['max_capacity']-storage['capacity']
		
		if _capacity > _greatest:
			_greatest = _capacity
	
	return _greatest

def can_carry_item(life, item_uid):
	if items.get_item_from_uid(item_uid)['size'] < get_max_carry_size(life):
		return True
	
	return False

def _equip_clothing(life,id):
	"""Private function. Equips clothing. See life.equip_item()."""
	item = get_inventory_item(life,id)
	
	if not can_wear_item(life, id):
		return False
	
	_limbs = get_all_limbs(life['body'])
	
	#TODO: Faster way to do this with sets
	for limb in item['attaches_to']:
		if not limb in _limbs:
			logging.warning('Limb not found: %s' % limb)
			return False
	
	remove_item_in_storage(life,id)
	
	logging.debug('%s puts on a %s.' % (life['name'][0],item['name']))
	
	if item['attaches_to']:			
		for limb in item['attaches_to']:
			attach_item_to_limb(life['body'],item['uid'],limb)
	
	return True

def _equip_item(life, item_id):
	"""Private function. Equips weapon. See life.equip_item()."""
	_limbs = get_all_limbs(life['body'])
	_hand = can_hold_item(life)
	item = get_inventory_item(life, item_id)
	
	if not _hand:
		if 'player' in life:
			gfx.message('You don\'t have a free hand!')
		return False
	
	remove_item_in_storage(life, item_id)
	_hand['holding'].append(item_id)
	
	logging.debug('%s equips a %s.' % (life['name'][0],item['name']))
	
	return True

def equip_item(life, item_id):
	"""Helper function. Equips item."""
	item = get_inventory_item(life, item_id)
	
	if 'CAN_WEAR' in item['flags']:
		if not _equip_clothing(life, item_id):
			return False
		
		_held = is_holding(life, item_id)
		if _held:			
			#TODO: Don't breathe this!
			_held['holding'].remove(item_id)
		
	elif 'CANNOT_HOLD' in item['flags']:
		logging.error('Cannot hold item type: %s' % item['type'])
	
	else:
		_equip_item(life, item_id)
		
		if 'ON_EQUIP' in item['flags']:
			scripting.execute(item['flags']['ON_EQUIP'], owner=life, item_uid=item['uid'])
	
	life['speed_max'] = get_max_speed(life)
	
	if life['speed'] > life['speed_max']:
		life['speed'] = life['speed_max']
	
	create_and_update_self_snapshot(life)
	
	return True

def drop_item(life, item_id):
	"""Helper function. Removes item from inventory and drops it. Returns item."""
	item = items.get_item_from_uid(remove_item_from_inventory(life, item_id))
	item['pos'] = life['pos'][:]
	items.add_to_chunk(item)
	
	#TODO: Don't do this here/should probably be a function anyway.
	for hand in life['hands']:
		_hand = get_limb(life, hand)
		
		if item_id in _hand['holding']:
			_hand['holding'].remove(item_id)
	
	return item['uid']

def drop_all_items(life):
	logging.debug('%s is dropping all items.' % ' '.join(life['name']))
	
	for item in [item['uid'] for item in [get_inventory_item(life, item) for item in life['inventory']] if not 'max_capacity' in item and not is_item_in_storage(life, item['uid'])]:
		drop_item(life, item)

def lock_item(life, item_uid):
	items.get_item_from_uid(item_uid)['lock'] = life

def unlock_item(life, item_uid):
	items.get_item_from_uid(item_uid)['lock'] = None

def pick_up_item_from_ground(life,uid):
	"""Helper function. Adds item via UID. Returns inventory ID. Raises exception otherwise."""
	#TODO: Misleading function name.
	_item = items.get_item_from_uid(uid)
	_id = add_item_to_inventory(life,_item)
	
	if _id:
		return _id

	raise Exception('Item \'%s\' does not exist at (%s,%s,%s).'
		% (item,life['pos'][0],life['pos'][1],life['pos'][2]))

def get_melee_limbs(life):
	if 'melee' in life:
		return life['melee']
	
	return False

def get_open_hands(life):
	"""Returns list of open hands."""
	_hands = []
	
	for hand in life['hands']:
		_hand = get_limb(life,hand)
		
		if not _hand['holding']:
			_hands.append(hand)
	
	return _hands

def can_hold_item(life):
	#TODO: Rename needed.
	"""Returns limb of empty hand. Returns False if none are empty."""
	for hand in life['hands']:
		_hand = get_limb(life,hand)
		
		if not _hand['holding']:
			return _hand
	
	return False

def is_holding(life, id):
	"""Returns the hand holding `item`. Returns False otherwise."""
	for hand in life['hands']:
		_limb = get_limb(life,hand)
		
		if id in _limb['holding']:
			return _limb
	
	return False

def perform_match(item, matches):
	for match in matches:
		_fail = False
		
		for key in match:
			if not key in item:
				_fail = True
				break
			
			if not match[key] == item[key]:
				_fail = True
				break
		
		if not _fail:
			return True
	
	return False

def get_legs(life):
	_legs = []
	
	for leg in life['legs']:
		_legs.extend(get_all_attached_limbs(life, leg))
	
	return _legs

def get_held_items(life, matches=None):
	"""Returns list of all held items."""
	_holding = []
	
	for hand in life['hands']:
		_limb = get_limb(life,hand)
		
		if _limb['holding']:
			_item = get_inventory_item(life,_limb['holding'][0])
			
			if matches:
				if not perform_match(_item,matches):
					continue
							
			_holding.append(_limb['holding'][0])
	
	return _holding

def get_items_attached_to_limb(life, limb):
	if not limb in life['body']:
		return False
	
	_limb = life['body'][limb]
	
	return _limb['holding']	

def item_is_equipped(life,id,check_hands=False):
	"""Returns limb where item is equipped. Returns False othewise.
	
	The `check_hands` keyword argument indicates whether hands will be checked (default False)
	
	"""
	for _limb in get_all_limbs(life['body']):
		if not check_hands and _limb in life['hands']:
			continue
		
		if id in get_limb(life,_limb)['holding']:
			return True
	
	return False

def get_all_life_at_position(life, position):
	_life = []
	
	for alife in [LIFE[i] for i in LIFE]:
		if not tuple(alife['pos'][:2]) == tuple(position[:2]):
			continue
		
		_life.append(alife['id'])
	
	return _life
	
def draw_life_icon(life, draw_alignment=False):
	_icon = [tick_animation(life), tcod.white, None]
	
	if life['dead']:
		_icon[1] = tcod.darkest_gray
		return _icon
	
	_bleed_rate = int(round(life['blood']))/float(calculate_max_blood(life))
	
	if time.time() % 0.5>=0.25 and life['state'] in STATE_ICONS:
		_icon[0] = STATE_ICONS[life['state']]
	elif _bleed_rate and _bleed_rate<=.85 and time.time()%_bleed_rate>=_bleed_rate/2.0:
		_icon[0] = chr(3)
	
	if not life['id'] == SETTINGS['controlling']:
		if draw_alignment:
			_knows = brain.knows_alife_by_id(LIFE[SETTINGS['controlling']], life['id'])
			
			if _knows:
				_color_map = tcod.color_gen_map([tcod.crimson, tcod.white, tcod.light_green], [0, 10, 20])
				_icon[2] = _color_map[(numbers.clip(judgement.get_trust(LIFE[SETTINGS['controlling']], life['id']), -10, 10))+10]
			
		_targets = judgement.get_combat_targets(life)
		if _targets and SETTINGS['controlling'] in _targets:
			_icon[1] = tcod.light_red
		elif not life['id'] == SETTINGS['controlling']:
			if life['group']:
				if alife.groups.is_member(life['group'], SETTINGS['controlling']):
					_icon[1] = tcod.light_green
				else:
					_icon[1] = tcod.lighter_crimson
			elif brain.knows_alife_by_id(LIFE[SETTINGS['controlling']], life['id']):
				_trust = judgement.get_trust(LIFE[SETTINGS['controlling']], life['id'])
				_icon[1] = tcod.color_lerp(tcod.lightest_green, tcod.dark_green, numbers.clip(_trust, 1, 10)/10.0)
	
	if life['dead']:
		_icon[1] = tcod.darkest_gray
	elif life['asleep']:
		if time.time()%1>=0.5:
			_icon[0] = 'S'
	
	return _icon

def draw_life():
	for life in [LIFE[i] for i in LIFE]:
		_icon,_fore_color,_back_color = draw_life_icon(life)
		
		if life['pos'][0] >= CAMERA_POS[0] and life['pos'][0] < CAMERA_POS[0]+MAP_WINDOW_SIZE[0]-1 and\
			life['pos'][1] >= CAMERA_POS[1] and life['pos'][1] < CAMERA_POS[1]+MAP_WINDOW_SIZE[1]-1:
			_x = life['pos'][0] - CAMERA_POS[0]
			_y = life['pos'][1] - CAMERA_POS[1]
			
			_p_x = life['prev_pos'][0] - CAMERA_POS[0]
			_p_y = life['prev_pos'][1] - CAMERA_POS[1]
			
			if 0<=_p_x<=MAP_WINDOW_SIZE[0] and 0<=_p_y<=MAP_WINDOW_SIZE[1]:
				if not life['pos'] == life['prev_pos'] and LOS_BUFFER[0][_p_y,_p_x]:
					gfx.refresh_window_position(_p_x, _p_y)
			
			if not LOS_BUFFER[0][_y,_x]:
				continue
			
			MAP_CHAR_BUFFER[1][_y,_x] = 0
			gfx.blit_char(_x,
				_y,
				_icon,
				_fore_color,
				_back_color,
				char_buffer=MAP_CHAR_BUFFER,
				rgb_fore_buffer=MAP_RGB_FORE_BUFFER,
				rgb_back_buffer=MAP_RGB_BACK_BUFFER)

def get_fancy_inventory_menu_items(life,show_equipped=True,show_containers=True,check_hands=False,matches=None):
	"""Returns list of menu items with "fancy formatting".
	
	`show_equipped` decides whether equipped items are shown (default True)
	`check_hands` decides whether held items are shown (default False)
	
	"""
	_inventory = []
	_inventory_items = 0
	_equipped_items = []
	_storage = {}
	
	#TODO: Time it would take to remove
	#_items.extend(life['inventory'].keys())
	for item_uid in life['inventory']:
		if show_equipped and item_is_equipped(life, item_uid):
			_equipped_items.append(item_uid)
		
		if show_containers:
			_item = get_inventory_item(life, item_uid)
			
			if 'storing' in _item:
				if _item['storing']:
					for stored_uid in _item['storing']:
						if item_uid in _storage:
							_storage[item_uid].append(stored_uid)
						else:
							_storage[item_uid] = [stored_uid]
				else:
					_storage[item_uid] = []
	
	if check_hands:
		for hand in life['hands']:
			for item_uid in life['body'][hand]['holding']:
				if matches:
					if not perform_match(ITEMS[item_uid], matches):
						continue
				
				_equipped_items.append(item_uid)
	
	#STORAGE
	#EQUIPPED
	if _storage:
		_inventory.append(menus.create_item('title', 'Storage', None))
	
		for storage_uid in _storage:
			storage_item = get_inventory_item(life, storage_uid)
		
			_menu_item = menus.create_item('single',
				                           storage_item['name'],
				                           '%s items' % len(storage_item['storing']),
				                           icon=storage_item['icon'],
				                           id=storage_uid,
				                           enabled=(len(storage_item['storing'])>0),
			                               color=(tcod.sepia, tcod.white))
			
			_inventory.append(_menu_item)
	
	if _equipped_items:
		_inventory.append(menus.create_item('title', 'Equipped', None))
	
		for item_uid in _equipped_items:
			item = get_inventory_item(life, item_uid)
		
			_menu_item = menus.create_item('single',
				                           '%s' % item['name'],
				                           item_is_worn(life, item_uid),
				                           icon=item['icon'],
				                           id=item_uid,
			                               is_item=True,
			                               color=(tcod.color_lerp(tcod.gray, item['color'][0], 0.30), tcod.white))
			
			_inventory.append(_menu_item)

	if not _equipped_items and not _storage:
		return []
	
	return _inventory

def draw_visual_inventory(life):
	_inventory = {}
	_limbs = get_all_limbs(life['body'])
	
	for limb in _limbs:
		if _limbs[limb]['holding']:
			_item = get_inventory_item(life,_limbs[limb]['holding'][0])
			console_set_default_foreground(0,white)
			console_print(0,MAP_WINDOW_SIZE[0]+1,_limbs.keys().index(limb)+1,'%s: %s' % (limb,_item['name']))
		else:
			console_set_default_foreground(0,Color(125,125,125))
			console_print(0,MAP_WINDOW_SIZE[0]+1,_limbs.keys().index(limb)+1,'%s: None' % limb)
	
	console_set_default_foreground(0,white)

#TODO: Since we are drawing in a blank area, we only need to do this once!
def draw_life_info():
	"""This code is garbage... I think it's one of the oldest parts of the game at this point (and it shows)
	
	Anyway, it'll be rewritten sooner or later :V
	"""
	life = LIFE[SETTINGS['following']]
	_info = []
	_name_mods = []
	_holding = get_held_items(life)
	_bleeding = get_bleeding_limbs(life)
	_broken = get_broken_limbs(life)
	_bruised = get_bruised_limbs(life)
	_cut = get_cut_limbs(life)
	
	if life['asleep']:
		_name_mods.append('(Asleep)')
	
	if not 'player' in life and life['state']:
		_name_mods.append('(%s)' % life['state'])
	
	_name_mods.append(life['stance'].title())
	_name_mods.append(get_current_chunk(life)['type'])
	_name_mods.append(str(get_current_chunk(life)['pos']))
	
	tcod.console_set_default_background(0, tcod.black)
	tcod.console_set_background_flag(0, tcod.BKGND_SET)
	
	tcod.console_set_default_foreground(0, BORDER_COLOR)
	tcod.console_print_frame(0,MAP_WINDOW_SIZE[0],0,60,WINDOW_SIZE[1]-MESSAGE_WINDOW_SIZE[1])
	
	tcod.console_set_default_foreground(0, tcod.white)
	tcod.console_print(0,MAP_WINDOW_SIZE[0]+1,0,'%s - %s' % (' '.join(life['name']),' - '.join(_name_mods)))
	
	if _holding:
		_held_item_names = [items.get_name(get_inventory_item(life,item)) for item in _holding]
		_held_string = language.prettify_string_array(_held_item_names,max_length=BLEEDING_STRING_MAX_LENGTH)
		_info.append({'text': 'Holding %s' % _held_string, 'color': tcod.white})
	else:
		_info.append({'text': 'You aren\'t holding anything.',
			'color': tcod.Color(125,125,125)})
	
	if _bleeding:
		_bleeding_string = language.prettify_string_array(_bleeding,max_length=BLEEDING_STRING_MAX_LENGTH)
		_info.append({'text': 'Bleeding: %s' % _bleeding_string, 'color': tcod.red})
	
	if _broken:
		_broken_string = language.prettify_string_array(_broken,max_length=BLEEDING_STRING_MAX_LENGTH)
		
		_info.append({'text': 'Broken: %s' % _broken_string,
			'color': tcod.red})
	
	if _cut:
		_cut_string = language.prettify_string_array(_cut,max_length=BLEEDING_STRING_MAX_LENGTH)
		
		_info.append({'text': 'Cut: %s' % _cut_string,
			'color': tcod.red})
	
	if _bruised:
		_bruised_string = language.prettify_string_array(_bruised,max_length=BLEEDING_STRING_MAX_LENGTH)
		
		_info.append({'text': 'Bruised: %s' % _bruised_string,
			'color': tcod.red})
	
	_i = 1
	for entry in _info:
		tcod.console_set_default_foreground(0,entry['color'])
		tcod.console_print(0,MAP_WINDOW_SIZE[0]+1,_i,entry['text'])
		
		_i += 1
	
	_blood_r = numbers.clip(300-int(life['blood']),0,255)
	_blood_g = numbers.clip(int(life['blood']),0,255)
	_blood_str = 'Blood: %s' % numbers.clip(int(life['blood']), 0, 999)
	_nutrition_str = language.prettify_string_array([get_hunger(life), get_thirst(life)], 30)
	_hunger_str = get_thirst(life)
	tcod.console_set_default_foreground(0, tcod.Color(_blood_r,_blood_g,0))
	tcod.console_print(0, MAP_WINDOW_SIZE[0]+1,len(_info)+1, _blood_str)
	tcod.console_print(0, MAP_WINDOW_SIZE[0]+len(_blood_str)+2, len(_info)+1, _nutrition_str)
	
	_longest_state = 7
	_visible_life = []
	for ai in [LIFE[i] for i in judgement.get_all_visible_life(life)]:
		if ai['dead']:
			_state = 'dead'
		else:
			_state = ai['state']
		
		_state_len = len(_state)
		
		if _state_len > _longest_state:
			_longest_state = _state_len
	
	_i = 5
	_xmod = _longest_state+3
	
	tcod.console_set_default_foreground(0, tcod.light_grey)
	tcod.console_print(0, MAP_WINDOW_SIZE[0]+1, len(_info)+3, '  State' + ' '*(_xmod-7) + 'Targets')
	
	for ai in [LIFE[i] for i in judgement.get_all_visible_life(life)]:
		_icon = draw_life_icon(ai)
		tcod.console_set_default_foreground(0, _icon[1])
		tcod.console_print(0, MAP_WINDOW_SIZE[0]+1, len(_info)+_i, _icon[0])

		if ai['dead']:
			_state = 'dead'
		else:
			_state = ai['state']
		
		if _state == 'combat':
			tcod.console_set_default_foreground(0, tcod.red)
		else:
			tcod.console_set_default_foreground(0, tcod.gray)
		
		tcod.console_print(0, MAP_WINDOW_SIZE[0]+3, len(_info)+_i, _state)
		
		tcod.console_set_default_foreground(0, tcod.white)
		#if ai in [context['from'] for context in LIFE[SETTINGS['controlling']]['contexts']]:
		#	if time.time()%1>=0.5:
		#		tcod.console_print(0, MAP_WINDOW_SIZE[0]+3, len(_info)+_i, 'T')
		
		if ai['dead']:
			tcod.console_print(0, MAP_WINDOW_SIZE[0]+1+_xmod, len(_info)+_i, '%s - Dead (%s)' % (' '.join(ai['name']), ai['cause_of_death']))
		elif ai['asleep']:
			tcod.console_print(0, MAP_WINDOW_SIZE[0]+1+_xmod, len(_info)+_i, '%s - Asleep' % ' '.join(ai['name']))
		else:
			tcod.console_print(0, MAP_WINDOW_SIZE[0]+1+_xmod, len(_info)+_i, ' '.join(ai['name']))
		_i += 1
	
	if LIFE[SETTINGS['controlling']]['recoil']:
		_y = MAP_WINDOW_SIZE[1]-SETTINGS['action queue size']
		tcod.console_set_default_foreground(0, tcod.yellow)
		tcod.console_print(0, MAP_WINDOW_SIZE[0]+1, _y, 'RECOIL (%s)' % LIFE[SETTINGS['controlling']]['recoil'])
	
	#Drawing the action queue
	_y_mod = 1
	_y_start = (MAP_WINDOW_SIZE[1]-1)-SETTINGS['action queue size']
	
	if len(life['actions']) > SETTINGS['action queue size']:
		_queued_actions = 'Queued Actions (+%s)' % (len(life['actions'])-SETTINGS['action queue size'])
	else:
		_queued_actions = 'Queued Actions'
	
	tcod.console_set_default_foreground(0, tcod.white)
	tcod.console_print(0, MAP_WINDOW_SIZE[0]+1, _y_start, _queued_actions)
	
	for action in life['actions'][:SETTINGS['action queue size']]:
		if not action['delay']:
			continue
				
		_name = action['action']['action']
		_bar_size = (action['delay']/float(action['delay_max']))*SETTINGS['progress bar max value']
		
		for i in range(SETTINGS['progress bar max value']):
			if i <= _bar_size:
				tcod.console_set_default_foreground(0, tcod.white)
			else:
				tcod.console_set_default_foreground(0, tcod.gray)
			
			if 1 <= i <= len(_name):
				tcod.console_set_default_foreground(0, tcod.green)
				tcod.console_print(0,MAP_WINDOW_SIZE[0]+2+i,_y_start+_y_mod,_name[i-1])
			else:
				tcod.console_print(0,MAP_WINDOW_SIZE[0]+2+i,_y_start+_y_mod,'|')
		
		tcod.console_set_default_foreground(0, tcod.white)
		tcod.console_print(0,MAP_WINDOW_SIZE[0]+1,_y_start+_y_mod,'[')
		tcod.console_print(0,MAP_WINDOW_SIZE[0]+SETTINGS['progress bar max value']+1,_y_start+_y_mod,']')
			
		_y_mod += 1

def is_target_of(life):
	_targets = []
	
	if not brain.get_flag(life, 'visible_chunks'):
		return False
	
	for chunk_key in brain.get_flag(life, 'visible_chunks'):
		for ai in  [LIFE[ai] for ai in maps.get_chunk(chunk_key)['life']]:
			if life['id'] == ai['id'] or ai['dead']:
				continue
			
			if not alife.sight.can_see_position(life, ai['pos']):
				continue
			
			_targets = judgement.get_combat_targets(ai)
			if _targets and life['id'] in [l for l in _targets]:
				_targets.append(ai)
				break
	
	return _targets

def is_in_shelter(life):
	if life['path']:
		return False
	
	_chunk_key = get_current_chunk_id(life)
	
	if chunks.get_flag(life, _chunk_key, 'shelter') and list(life['pos'][:2]) in chunks.get_flag(life, _chunk_key, 'shelter_cover'):
		return True
	
	return False

def collapse(life):
	if life['stance'] in ['standing','crouching']:
		life['stance'] = 'crawling'

def get_damage(life):
	_damage = 0
	for limb in life['body'].values():
		_damage += limb['cut']
		_damage += limb['bleeding']
	
	return _damage		

def pass_out(life,length=None):
	if not length:
		length = get_total_pain(life)*PASS_OUT_PAIN_MOD
	
	collapse(life)
	life['asleep'] = length
	
	if 'player' in life:
		gfx.message('You pass out!',style='damage')
	else:
		say(life, '@n passes out.', action=True)
	
	logging.debug('%s passed out.' % life['name'][0])

def get_total_pain(life):
	_pain = 0
	
	for limb in life['body']:
		_pain += limb_is_in_pain(life, limb)
	
	return _pain

def calculate_hunger(life):
	_remove = []
	for _food in life['eaten']:
		if _food['sustenance']:
			_food['sustenance'] -= 1
			
			if _food['type'] == 'food':
				life['hunger'] += _food['value']
			elif _food['type'] == 'drink':
				life['thirst'] += _food['value']
			else:
				logging.error('Item \'%(name)s\' of type \'%(type)s\' was eaten.' % _food)
				logging.debug('What in the world did you eat?')
			
			if 'modifiers' in _food:
				for _mod in _food['modifiers']:
					if not _mod in life:
						logging.error('Invalid modifier \'%s\' in \'%s\'.' % (_mod, _food['name']))
						continue
					
					life[_mod] += _food['modifiers'][_mod]
			
		else:
			_remove.append(_food)
	
	for _item in _remove:
		life['eaten'].remove(_item)
	
	if get_hunger(life) == 'Satiated':
		brain.unflag(life, 'hungry')
	else:
		brain.flag(life, 'hungry')
	
	if get_thirst(life) == 'Hydrated':
		brain.unflag(life, 'thirsty')
	else:
		brain.flag(life, 'thirsty')

def get_hunger_percentage(life):
	return life['hunger']/float(life['hunger_max'])

def get_thirst_percentage(life):
	return life['thirst']/float(life['thirst_max'])

def get_hunger(life):
	if not 'HUNGER' in life['life_flags']:
		return 'Not hungry'
	
	_hunger = get_hunger_percentage(life)
	
	if _hunger>.5:
		return 'Satiated'
	elif _hunger>=.3:
		return 'Hungry'
	else:
		return 'Starving'

def get_thirst(life):
	if not 'THIRST' in life['life_flags']:
		return 'Not thirsty'
	
	_thirst = get_thirst_percentage(life)
	
	if _thirst>.5:
		return 'Hydrated'
	elif _thirst>=.3:
		return 'Thirsty'
	else:
		return 'Dehydrated'

def calculate_blood(life):
	_blood = 0
	
	if life['blood']<=0:
		return 0
	
	for limb in life['body'].values():
		if limb['bleeding']>0:
			#print limb_is_cut
			limb['bleeding'] = .5*(limb['bleed_mod']*float(limb['cut']))
			limb['bleeding'] = numbers.clip(limb['bleeding'], 0, 255)
			_blood += limb['bleeding']
	
	life['blood'] -= _blood*LIFE_BLEED_RATE
	
	return life['blood']

def calculate_max_blood(life):
	return sum([l['size']*10 for l in life['body'].values()])

def get_bleeding_limbs(life):
	"""Returns list of bleeding limbs."""
	_bleeding = []
	
	for limb in life['body']:
		if life['body'][limb]['bleeding']:
			_bleeding.append(limb)
	
	return _bleeding

def get_broken_limbs(life):
	"""Returns list of broken limbs."""
	_broken = []
	
	for limb in life['body']:
		if life['body'][limb]['broken']:
			_broken.append(limb)
	
	return _broken

def get_bruised_limbs(life):
	"""Returns list of bruised limbs."""
	_bruised = []
	
	for limb in life['body']:
		if life['body'][limb]['bruised']:
			_bruised.append(limb)
	
	return _bruised

def get_cut_limbs(life):
	"""Returns list of cut limbs."""
	_cut = []
	
	for limb in life['body']:
		if life['body'][limb]['cut']:
			_cut.append(limb)
	
	return _cut

def limb_is_cut(life, limb):
	_limb = life['body'][limb]
	
	return _limb['cut']

#TODO: Unused?
def limb_is_broken(life, limb):
	_limb = life['body'][limb]
	
	return _limb['broken']

def limb_is_in_pain(life, limb):
	_limb = life['body'][limb]
	
	_score = _limb['pain']
	
	if _limb['bruised']:
		_score *= 1.5
	
	if _limb['broken']:
		_score *= 2
	
	return _score

#TODO: Unused?
def artery_is_ruptured(life, limb):
	_limb = life['body'][limb]
	
	return _limb['artery_ruptured']

def can_knock_over(life, limb):
	_limb = life['body'][limb]
	
	if life['stance'] == 'crawling':
		return False
	
	if limb in get_legs(life):
		return True
	
	return False

def remove_limb(life, limb, no_children=False):
	if limb in life['hands']:
		life['hands'].remove(limb)
	
	if limb in life['legs']:
		life['legs'].remove(limb)
	
	if limb in life['melee']:
		life['melee'].remove(limb)	
	
	if not limb in life['body']:
		return False
	
	for item in get_items_attached_to_limb(life, limb):
		remove_item_from_inventory(life, item)
	
	if can_knock_over(life, limb):
		if 'player' in life:
			gfx.message('You fall over.', style='player_combat_bad')
		else:
			say(life, '%s falls over!' % language.get_introduction(life), action=True)
		
		collapse(life)
	
	if 'CRUCIAL' in life['body'][limb]['flags']:
		if not life['dead']:
			kill(life, 'a severed %s' % limb)
	
	if 'children' in life['body'][limb] and not no_children:
		for _attached_limb in life['body'][limb]['children']:
			#say(life, '%s %s is severed!' % (language.get_introduction(life, posession=True), _attached_limb), action=True)
			remove_limb(life, _attached_limb)
	
	life['blood'] -= life['body'][limb]['size']*10
	
	del life['body'][limb]
	
	logging.debug('%s\'s %s was removed!' % (' '.join(life['name']), limb))

def sever_limb(life, limb, impact_velocity):
	say(life, '%s %s is severed!' % (language.get_introduction(life, posession=True), limb), action=True)
	
	if 'parent' in life['body'][limb] and 'children' in life['body'][life['body'][limb]['parent']]:
		life['body'][life['body'][limb]['parent']]['children'].remove(limb)
		life['body'][life['body'][limb]['parent']]['bleeding'] += life['body'][limb]['size']
		add_pain_to_limb(life, life['body'][limb]['parent'], amount=life['body'][limb]['size']*5)
	
	set_animation(life, ['X', '!'], speed=4)
	
	effects.create_gib(life, '-', life['body'][limb]['size'], limb, impact_velocity)
	
	remove_limb(life, limb)
	
	_total_blood = calculate_max_blood(life)
	if life['blood'] > _total_blood:
		life['blood'] = _total_blood

def cut_limb(life, limb, amount=2, impact_velocity=[0, 0, 0]):
	_limb = life['body'][limb]
	
	_limb['bleeding'] += amount*float(_limb['bleed_mod'])
	_limb['cut'] += amount
	
	if _limb['cut'] >= _limb['size']:
		if 'CRUCIAL' in life['body'][limb]['flags']:
			kill(life, 'a critical blow to the %s' % limb)
			return True
		
		sever_limb(life, limb, impact_velocity)
		return True
	
	effects.create_splatter('blood', life['pos'], velocity=1, intensity=amount)
	
	if life.has_key('player'):
		gfx.message('Your %s is severely cut!' % limb,style='damage')

def bruise_limb(life, limb):
	_limb = life['body'][limb]
	
	_limb['bruised'] = True

def break_limb(life,limb):
	_limb = life['body'][limb]
	
	_limb['broken'] = True

def rupture_artery(life, limb):
	_limb = life['body'][limb]
	
	_limb['artery_ruptured'] = True

def burn(life, intensity):
	#TODO: Fire resistance
	#TODO: Items burning
	_limbs = []
	
	if life['stance'] == 'standing' and intensity>=3:
		_limbs.extend(get_legs(life))
	elif life['stance'] == 'crouching' and intensity>=3:
		_limbs.extend(life['body'].keys())
	elif life['stance'] == 'crawling':
		_limbs.extend(life['body'].keys())
	else:
		return False
	
	_burn_amount = intensity*.015
	_burn_limb = random.choice(_limbs)
	
	if 'player' in life:
		gfx.message('The fire burns!')
	
	add_pain_to_limb(life, _burn_limb, amount=_burn_amount)

def add_force_to_limb(life, limb, impact_velocity):
	_limb = life['body'][limb]
	
	if max(impact_velocity) >= _limb['size']:
		return sever_limb(life, limb, impact_velocity)
	
	if not _limb['bruised']:
		logging.debug('%s bruised their %s.' % (' '.join(life['name']), limb))
		add_pain_to_limb(life, limb, amount=max(impact_velocity))
		bruise_limb(life, limb)

def add_pain_to_limb(life, limb, amount=1):
	_limb = life['body'][limb]
	
	_limb['pain'] += amount
	
	logging.debug('%s hurts their %s (%s)' % (' '.join(life['name']), limb, amount))

def add_wound(life, limb, cut=0, pain=0, force_velocity=[0, 0, 0], artery_ruptured=False, lodged_item=None, impact_velocity=[0, 0, 0]):
	_limb = life['body'][limb]
	
	if cut:
		cut_limb(life, limb, amount=cut, impact_velocity=impact_velocity)
		
		if not limb in life['body']:
			return False
		
		add_pain_to_limb(life, limb, amount=cut*float(_limb['damage_mod']))
	
	if pain:
		add_pain_to_limb(life, limb, amount=pain)
	
	if force_velocity:
		add_force_to_limb(life, limb, force_velocity)
	
	if artery_ruptured:
		#_limb['bleeding'] += 7
		rupture_artery(life, limb)
		
		add_pain_to_limb(life, limb, amount=3*float(_limb['damage_mod']))
	
	if lodged_item:
		if 'sharp' in lodged_item['damage']:
			add_pain_to_limb(life, limb, amount=lodged_item['damage']['sharp']*2)
		else:
			add_pain_to_limb(life, limb, amount=2)
	
	_injury = {'limb': limb,
		'cut': cut,
		'artery_ruptured': artery_ruptured,
		'lodged_item': lodged_item}
	
	_limb['wounds'].append(_injury)

def get_limb_stability(life, limb):
	_limb = get_limb(life, limb)
	
	if limb_is_broken(life, limb):
		return 0
	
	_stability = 10
	_stability -= limb_is_cut(life, limb)
	
	return numbers.clip(_stability, 0, 10)/10.0

def get_all_attached_limbs(life,limb):
	_limb = life['body'][limb]
	
	if not 'children' in _limb:
		return [limb]
	
	_attached = [limb]
	
	for child in _limb['children']:
		_attached.extend(get_all_attached_limbs(life,child))
	
	return _attached

def damage_from_fall(life,dist):
	memory(life,'fell %s feet' % (dist*15),
		pos=life['pos'][:])
	
	if 0<dist<=3:
		if 'player' in life:
			gfx.message('You land improperly!')
			gfx.message('Your legs are bruised in the fall.',style='damage')
		
		for limbs in life['legs']:
			for leg in get_all_attached_limbs(life,limbs):
				if life['body'][leg]['bruised']:
					add_pain_to_limb(life,leg,amount=dist*2)
				else:
					memory(life,'bruised their %s in a fall' % (leg),
						pos=life['pos'][:],
						limb=leg)
					
					bruise_limb(life,leg)
					add_pain_to_limb(life,leg,amount=dist)
			
	elif dist>3:
		if 'player' in life:
			gfx.message('You hear the sound of breaking bones!')
			gfx.message('You break both legs in the fall.',style='damage')
		
		for limbs in life['legs']:
			for leg in get_all_attached_limbs(life,limbs):				
				if life['body'][leg]['broken']:
					add_pain_to_limb(life,leg,amount=dist*10)
				else:
					memory(life,'broke their %s in a fall' % (leg),
						pos=life['pos'][:],
						limb=leg)
					
					break_limb(life,leg)
					add_pain_to_limb(life,leg,amount=dist*3)
	else:
		return False
	
	create_and_update_self_snapshot(life)
	
	return True

def difficulty_of_hitting_limb(life, limb, item_uid):
	_scatter = weapons.get_bullet_scatter_to(life, life['pos'], item_uid)
	_scatter *= 1+((10-numbers.clip(get_limb(life, limb)['size'], 1, 10))/10)
	
	return _scatter

def damage_from_item(life, item, damage):
	#Step 1: If we are aiming at something, what are the chances of hitting it?
	#Limbs:
	print item['accuracy'], difficulty_of_hitting_limb(life, item['aim_at_limb'], item['uid'])
	if item['aim_at_limb'] and item['accuracy']>=difficulty_of_hitting_limb(life, item['aim_at_limb'], item['uid']):
		_rand_limb = [item['aim_at_limb'] for i in range(item['accuracy'])]
	else:
		_rand_limb = [random.choice(life['body'].keys())]
	
	_poss_limbs = _rand_limb
	_shot_by_alife = LIFE[item['owner']]
	
	if not _rand_limb:
		memory(life, 'shot at by (missed)', target=item['owner'], danger=3, trust=-10)
		create_and_update_self_snapshot(life)
		
		if 'player' in _shot_by_alife:
			gfx.message('You miss wildly!', style='action')
		elif 'player' in life:
			gfx.message('%s shoots at you, but misses.' % language.get_introduction(life), style='player_combat_bad')
		
		return False
	
	memory(_shot_by_alife, 'shot', target=life['id'])
	memory(life, 'shot by', target=item['owner'], danger=3, trust=-10)
	create_and_update_self_snapshot(LIFE[item['owner']])
	
	if get_memory(life, matches={'target': item['owner'], 'text': 'friendly'}):
		memory(life, 'traitor',
			target=item['owner'])
	
	if 'parent' in life['body'][_rand_limb[0]]:
		_poss_limbs.append(life['body'][_rand_limb[0]]['parent'])
	
	if 'children' in life['body'][_rand_limb[0]] and life['body'][_rand_limb[0]]['children']:
		_poss_limbs.append(life['body'][_rand_limb[0]]['children'][0])

	_hit_limb = random.choice(_poss_limbs)
	_dam_message = dam.bullet_hit(life, item, _hit_limb)
	
	if 'player' in _shot_by_alife:
		gfx.message(_dam_message, style='player_combat_good')
		logic.show_event(_dam_message, time=35, life=life)
	elif 'player' in life:
		gfx.message(_dam_message, style='player_combat_bad')
	else:
		say(life, _dam_message, action=True)
	
	create_and_update_self_snapshot(life)
	
	return True

def natural_healing(life):
	for limb_name in life['body']:
		_limb = get_limb(life, limb_name)
		_remove_wounds = []
		
		for wound in _limb['wounds']:			
			_remove = True
			for key in wound:
				if key == 'limb':
					continue
				
				if wound[key]:
					_remove = False
					break
			
			if _remove:
				_remove_wounds.append(wound)
		
		#if _limb['bleeding']>0:
		#	_limb['bleeding'] -= .5*(_limb['bleed_mod']*float(len(_limb['wounds'])))
		#	_limb['bleeding'] = numbers.clip(_limb['bleeding'], 0, 255)
		
		for wound in _remove_wounds:
			_limb['wounds'].remove(wound)
			
			if 'player' in life:
				gfx.message('Your %s has healed.' % limb_name)

def generate_life_info(life):
	_stats_for = ['name', 'id', 'pos', 'memory']
	_lines = []
	
	for key in _stats_for:
		if isinstance(life[key], list):
			print '\n',key,'\t-',
			for value in life[key]:
				if isinstance(value, dict):
					print '\n'
					for _key in value:
						print '\t',_key,'\t' * (2-(len(_key)/8)),value[_key]
				else:
					print value,
			print '\t\t',
		elif isinstance(life[key], dict):
			for _key in life[key]:
				print '\t',_key,'\t' * (2-(len(_key)/8)),life[key][_key]
		
		else:
			print '\n',key,'\t-',life[key],
		
	return _lines

def print_life_table():
	print '%' * 16
	print '^ Life (Table) ^'
	print '%' * 16,'\n'
	
	for life in [LIFE[i] for i in LIFE]:
		generate_life_info(life)
		print '\n','%' * 16,'\n'

def tick_all_life(source_map):
	for life in [LIFE[i] for i in LIFE]:
		tick(life,source_map)
