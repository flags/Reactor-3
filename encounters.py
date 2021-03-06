from globals import *

import life as lfe
import libtcodpy as tcod

import language
import alife
import menus

import logging

def create_encounter(life, target, context=None):
	_encounter = {}
	
	if life['encounters']:
		return None
	
	if not life['id'] in target['know']:
		logging.warning('Encounter: %s does not know %s.' % (' '.join(life['name']), ' '.join(target['name'])))
		return False
	
	target['know'][life['id']]['last_encounter_time'] = WORLD_INFO['ticks']
	_encounter['target'] = target
	
	_remembered_alife = alife.brain.knows_alife(target, life)
	_stance = alife.stances.get_stance_towards(target, life['id'])
	_time_since_met = WORLD_INFO['ticks'] - _remembered_alife['met_at_time']
	
	_text = []
	_text.append('You see %s.' % ' '.join(target['name']))
	_text.append('_' * 38)
	
	if alife.brain.has_met_in_person(target, life) and _time_since_met<1000:
		_text.append('You just met %s recently.' % target['name'][0])
	
	_text.append('He appears to be %s towards you.' % _stance)
	_text.append('_' * 38)
	_text.append('<Shift>+f - Appear Friendly')
	_text.append('<Shift>+h - Appear Hostile')
	#_text.append('<Shift>+s - Surrender')
	#_text.append('<Shift>+q - Ignore')
	_text.append('_' * 38)
	
	_encounter['text'] = _text
	_encounter['start_time'] = WORLD_INFO['ticks']
	
	SETTINGS['following'] = target['id']
	life['encounters'].append(_encounter)
	logging.debug('%s created encounter.' % ' '.join(target['name']))
	SETTINGS['encounter animation timer'] = ENCOUNTER_ANIMATION_TIME
	
	return _encounter

def draw_encounter(life, encounter):
	if SETTINGS['encounter animation timer']>0:
		if SETTINGS['encounter animation timer'] == ENCOUNTER_ANIMATION_TIME:
			lfe.set_animation(encounter['target'], TICKER, speed=1, loops=2)
		
		SETTINGS['encounter animation timer']-=1
		return False
	
	if not 'console' in encounter:
		encounter['console'] = tcod.console_new(40, 40)
	
	_y = 1
	for line in encounter['text']:
		_x = 1
		
		while line:
			_line = line
			while len(_line)>=40:
				_words = _line.split(' ')
				_line = ' '.join(_words[:len(_words)-1])
				
			_lines = [_line]
			
			if not _line == line:
				_lines.append(line.replace(_line, ''))
			
			_i = 0
			for txt in _lines:
				tcod.console_print(encounter['console'],
					_x+_i,
					_y,
					txt)
				
				_i += 1
				_y += 1
			
			_x += 1
			_y += 1
			
			break
