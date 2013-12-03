from globals import *

import life as lfe

import judgement
import movement
import numbers
import sight
import brain

import logging

def tick(life):
	_threats = judgement.get_threats(life, recent_only=True, ignore_escaped=2)
	
	for target in [LIFE[t] for t in _threats]:
		if numbers.distance(life['pos'], brain.knows_alife(life, target)['last_seen_at']) >= sight.get_vision(life):
			_threats.remove(target['id'])
	
	movement.escape(life, _threats)
