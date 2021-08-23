from globals import *

import life as lfe

from . import judgement
from . import movement
import bad_numbers
from . import sight
from . import brain

import logging

def tick(life):
	_threats = judgement.get_threats(life, ignore_escaped=2)
	
	if not _threats:
		return True
	
	for target in [LIFE[t] for t in _threats]:
		if bad_numbers.distance(life['pos'], brain.knows_alife(life, target)['last_seen_at']) >= sight.get_vision(life):
			_threats.remove(target['id'])
	
	return movement.hide(life, _threats)
