#This isn't for playing sound - R3 uses outside libraries for that,
#and this module utilizes that in places.
#
#This is for simulating noises (that aren't voices)

from globals import *

import graphics as gfx

import language
import judgement
import bad_numbers
import sight
import brain

import logging
import random

FAR_TEXT = ['You hear @t to the @d.']

def create(position, volume, close_text, far_text, skip_on_visual=True, **sound):
	_noise = {'pos': position,
	          'volume': volume,
	          'text': (close_text, far_text),
	          'skip_on_visual': skip_on_visual}
	_noise.update(sound)
	
	_spread(_noise)

def update_targets_around_noise(life, noise):
	_most_likely_target = {'target': None, 'last_seen_time': 0}
	
	if 'target' in noise and not life['id'] == noise['target']:
		_visiblity = bad_numbers.clip(sight.get_stealth_coverage(LIFE[noise['target']]), 0.0, 1.0)
		_visiblity = bad_numbers.clip(_visiblity+(bad_numbers.distance(life['pos'], LIFE[noise['target']]['pos']))/(sight.get_vision(life)/2), 0, 1.0)
		
		if _visiblity >= sight.get_visiblity_of_position(life, LIFE[noise['target']]['pos']):
			brain.meet_alife(life, LIFE[noise['target']])
			
			life['know'][noise['target']]['escaped'] = 1
			life['know'][noise['target']]['last_seen_at'] = noise['pos'][:]
			life['know'][noise['target']]['last_seen_time'] = 0
	
	for target in life['know'].values():
		if not target['escaped'] or not target['last_seen_at'] or target['dead']:
			continue
		
		if bad_numbers.distance(target['last_seen_at'], noise['pos']) > noise['volume']:
			continue
		
		if judgement.is_target_threat(life, target['life']['id']):
			if not _most_likely_target['target'] or target['last_seen_time'] < _most_likely_target['last_seen_time']:
				_most_likely_target['last_seen_time'] = target['last_seen_time']
				_most_likely_target['target'] = target
	
	if _most_likely_target['target']:
		_most_likely_target['target']['escaped'] = 1
		_most_likely_target['target']['last_seen_at'] = noise['pos'][:]
		_most_likely_target['target']['last_seen_time'] = 1
		
		logging.debug('%s heard a noise, attributing it to %s.' % (' '.join(life['name']), ' '.join(_most_likely_target['target']['life']['name'])))

def _spread(noise):
	for alife in LIFE.values():
		if alife['dead']:
			continue
		
		_can_see = False
		if sight.can_see_position(alife, noise['pos']):
			_can_see = True
		
		_dist = bad_numbers.distance(noise['pos'], alife['pos'])
		
		if _dist>noise['volume']:
			continue
		
		update_targets_around_noise(alife, noise)		
		
		_direction_to = bad_numbers.direction_to(alife['pos'], noise['pos'])
		_direction_string = language.get_real_direction(_direction_to)
		
		#TODO: Check walls between positions
		#TODO: Add memory
		if not _can_see or not noise['skip_on_visual']:
			if _dist >=noise['volume']/2:
				if 'player' in alife:
					gfx.message(random.choice(FAR_TEXT).replace('@t', noise['text'][1]).replace('@d', _direction_string), style='sound')
			else:
				if 'player' in alife:
					gfx.message(random.choice(FAR_TEXT).replace('@t', noise['text'][0]).replace('@d', _direction_string), style='sound')
				