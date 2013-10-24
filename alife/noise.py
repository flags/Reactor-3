#This isn't for playing sound - R3 uses outside libraries for that,
#and this module utilizes that in places.
#
#This is for simulating noises (that aren't voices)
from globals import *

import graphics as gfx

import numbers
import random

FAR_TEXT = ['You hear @t to the @d.']

def create(position, volume, close_text, far_text, **sound):
	_noise = {'pos': position,
	          'volume': volume,
	          'text': (close_text, far_text)}
	
	_spread(_noise)

def _spread(noise):
	for alife in LIFE.values():
		_dist = numbers.distance(noise['pos'], alife['pos'])
		
		if _dist>noise['volume']:
			continue
		
		#TODO: Check walls between positions
		#TODO: Add memory
		if _dist >=noise['volume']/2:
			if 'player' in alife:
				gfx.message(random.choice(FAR_TEXT).replace('@t', noise['text'][1]).replace('@d', 'north'))
		else:
			if 'player' in alife:
				gfx.message(random.choice(FAR_TEXT).replace('@t', noise['text'][0]).replace('@d', 'north'))
				