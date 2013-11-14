from globals import *

import life as lfe

import judgement
import language
import dialog
import groups
import brain
import menus
import sight
import stats

import logging
import random

def has_sent(life, target, gist):
	if gist in life['know'][target['id']]['sent']:
		return True
	
	return False

def has_received(life, target, gist):
	if gist in life['know'][target['id']]['received']:
		return True
	
	return False

def has_heard(life, target, gist):
	for heard in life['heard']:
		if heard['from']['id'] == target['id'] and heard['gist'] == gist:
			return True
	
	return False

def discussed(life, target, gist):
	if has_heard(life, target, gist):
		return True
	
	if has_sent(life, target, gist):
		return True
	
	return False

def send(life, target, gist):
	life['know'][target['id']]['sent'].append(gist)
	lfe.create_and_update_self_snapshot(target)
		
	return True

def unsend(life, target, gist):
	if gist in life['know'][target['id']]['sent']:
		life['know'][target['id']]['sent'].remove(gist)
		return True
	
	return False

def receive(life, target, gist):
	life['know'][target['id']]['received'].append(gist)
	lfe.create_and_update_self_snapshot(target)
		
	return True

def announce(life, gist, public=False, trusted=False, group=None, **kvargs):
	"""Sends `gist` to any known ALife. If `public`, then send to everyone."""
	if public:
		_announce_to = [LIFE[i] for i in LIFE if not i == life['id']]
	elif trusted:
		_announce_to = [life['know'][i]['life'] for i in life['know'] if judgement.can_trust(life, i)]
	elif group:
		_announce_to = [LIFE[i] for i in groups.get_group(group)['members'] if not i == life['id']]
	else:
		_announce_to = [life['know'][i]['life'] for i in life['know'] if not judgement.is_target_dangerous(life, i)]
	
	for target in _announce_to:
		if not public and has_sent(life, target, gist):
			#print life['name'],'cant reach',target['id'],has_sent(life, target, gist)
			continue
		
		if not stats.can_talk_to(life, target['id']):
			continue
		
		if not sight.can_see_position(life, target['pos']) and not lfe.get_all_inventory_items(life, matches=[{'name': 'radio'}]):
			#print life['name'],'cant see',target['id']
			continue
	
		#logging.debug('%s got announce: %s, %s' % (' '.join(target['name']), gist, life['name']))
		lfe.create_conversation(life, gist, matches=[{'id': target['id']}], **kvargs)
		
		if not public:
			send(life, target, gist)
	
	return True

def get_announce_list(life):
	return [life['know'][i]['life'] for i in life['know'] if life['know'][i]['score']>0]

def communicate(life, gist, msg=None, radio=False, matches=[], **kvargs):
	if 'target' in kvargs:
		logging.warning('Deprecated keyword in speech.communicate(): target')
	
	lfe.create_conversation(life, gist, msg=msg, radio=radio, matches=matches, **kvargs)
	lfe.create_and_update_self_snapshot(life)

def start_dialog(life, target, gist, remote=False, **kwargs):
	_dialog = dialog.create_dialog_with(life, target, remote=remote, **kwargs)
	
	dialog.say_via_gist(life, _dialog, gist)

def determine_interesting_event(life, target):
	_valid_phrases = []
	for memory in life['memory']:
		_memory_age = WORLD_INFO['ticks']-memory['time_created']
		
		if _memory_age >= 500:
			continue
		
		if memory['target'] == target['id']:
			continue
		
		_phrase = language.generate_memory_phrase(memory)
		
		if not _phrase:
			continue
		
		_valid_phrases.append(_phrase)
	
	if not _valid_phrases:
		return 'I don\'t have anything interesting to say.'
		
	return random.choice(_valid_phrases)

def get_recent_events(life):
	if WORLD_INFO['ticks']-life['created']<75:
		return 'Hey, I just got here!'
	
	return 'Nothing much has been going on lately.'

def confirm_target(entry):
	_dialog_id = LIFE[SETTINGS['controlling']]['dialogs'][0]
	for flag in dialog.get_dialog(_dialog_id)['flags']:
		if dialog.get_dialog(_dialog_id)['flags'][flag] == -333:
			dialog.get_dialog(_dialog_id)['flags'][flag] = entry['target']
			break
	
	dialog.say_via_gist(LIFE[SETTINGS['controlling']],
	                    _dialog_id,
	                    dialog.get_flag(_dialog_id, 'NEXT_GIST'))

def get_target(life, dialog_id, gist):
	if 'player' in life:
		_targets = menus.create_target_list()
		
		_menu = menus.create_menu(menu=_targets,
		                          title='Select Target',
		                          format_str='$k',
		                          on_select=confirm_target,
		                          close_on_select=True)
		menus.activate_menu(_menu)
	else:
		dialog.get_dialog(dialog_id)['flags']['target'] = random.choice(judgement.get_threats(life))
		dialog.say_via_gist(life,
			                dialog_id,
			                dialog.get_flag(dialog_id, 'NEXT_GIST'))
	
def get_introduction_message(life, life_id):
	_target = brain.knows_alife_by_id(life, life_id)
	
	if _target['alignment'] == 'hostile':
		return ['You will die, scumbag!']
	
	_alignment = stats.get_goal_alignment_for_target(life, life_id)
	
	if _alignment == 'feign_trust':
		return 'Let\'s have a chat.'
	
	if _alignment == 'malicious':
		return 'Back up. I have no time to talk to you.'
	
	if _alignment == 'genuine':
		return 'You! Let\'s have a chat.'

def get_introduction_gist(life, life_id):
	_alignment = stats.get_goal_alignment_for_target(life, life_id)
	
	if _alignment == 'malicious':
		return 'AGRESSIVE_RESPONSE'
	
	if _alignment == 'feign_trust':
		return 'feign_trust_failed'
	
	return 'trust'

def describe_target(life, life_id):
	if life['id'] == life_id:
		return 'That\'s me.'
	
	_target = brain.knows_alife_by_id(life, life_id)
	_details = []
	
	if _target['dead']:
		return 'He died.'
	
	if sight.can_see_target(life, life_id):
		_details.append('He\'s right over there!')
	else:
		if _target['last_seen_time'] >= 2000:
			_details.append('I last saw him at %s, %s, but it was a long time ago.' % (_target['last_seen_at'][0], _target['last_seen_at'][1]))
		else:
			_details.append('I last saw him at %s, %s, recently.' % (_target['last_seen_at'][0], _target['last_seen_at'][1]))
	
	return ' '.join(_details)