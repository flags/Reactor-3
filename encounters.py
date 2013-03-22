from globals import *

import language
import alife
import menus

import logging

def create_encounter(life, target, context=None):
	if not life['id'] in target['know']:
		logging.warning('Encounter: %s does not know %s.' % (' '.join(life['name']), ' '.join(target['name'])))
		return False
	
	_remembered_alife = alife.brain.get_remembered_alife(target, life)
	_stance = alife.stances.get_stance_towards(target, life)
	_time_since_met = WORLD_INFO['ticks'] - _remembered_alife['met_at_time']
	
	_text = []
	_text.append('You see %s.' % ' '.join(target['name']))
	_text.append('He appears to be %s towards you.' % _stance)
	
	if alife.brain.has_met_in_person(target, life) and _time_since_met<1000:
		_text.append('You just met him recently and haven\'t heard about him.')
		#TODO: You know he is a founder of a camp
	
	print ' '.join(_text)
	
	language.get_name(target)
	
	logging.debug('%s created encounter.' % ' '.join(life['name']))
