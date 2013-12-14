#This isn't for playing sound - R3 uses outside libraries for that,
#and this module utilizes that in places.
#
#This is for simulating noises (that aren't voices)
from globals import *

import graphics as gfx

import judgement
import numbers
import sight

import random

FAR_TEXT = ['You hear @t to the @d.']

def create(position, volume, close_text, far_text, **sound):
	_noise = {'pos': position,
	          'volume': volume,
	          'text': (close_text, far_text)}
	
	_spread(_noise)

def update_targets_around_noise(life, noise):
	for target in life['know'].values():
		if not target['escaped']:
			continue
		
		if numbers.distance(target['last_seen_at'], noise['pos']) > noise['volume']:
			continue
		
		target['last_seen_at'] = noise['pos'][:]
		print 'SOUND UPDATED' * 100

def _spread(noise):
	for alife in LIFE.values():
		if sight.can_see_position(alife, noise['pos']):
			continue
		
		_dist = numbers.distance(noise['pos'], alife['pos'])
		
		if _dist>noise['volume']:
			continue
		
		update_targets_around_noise(alife, noise)		
		
		_direction_to = numbers.direction_to(alife['pos'], noise['pos'])
		if abs(_direction_to)<22 or abs(_direction_to-360)<22:
			_direction = 'east'
		elif abs(_direction_to-45)<22:
			_direction = 'northeast'
		elif abs(_direction_to-90)<22:
			_direction = 'north'
		elif abs(_direction_to-135)<22:
			_direction = 'northwest'
		elif abs(_direction_to-180)<22:
			_direction = 'west'
		elif abs(_direction_to-225)<22:
			_direction = 'southwest'
		elif abs(_direction_to-270)<22:
			_direction = 'south'
		elif abs(_direction_to-315)<22:
			_direction = 'southeast'
		else:
			_direction = 'east'
		
		#TODO: Check walls between positions
		#TODO: Add memory
		if _dist >=noise['volume']/2:
			if 'player' in alife:
				gfx.message(random.choice(FAR_TEXT).replace('@t', noise['text'][1]).replace('@d', _direction))
		else:
			if 'player' in alife:
				gfx.message(random.choice(FAR_TEXT).replace('@t', noise['text'][0]).replace('@d', _direction))
				