from globals import *

import life as lfe

from . import judgement
from . import movement
from . import survival
from . import brain


def setup(life):
	_needs_to_meet = []
	_needs_to_satisfy = []
	_needs_unmet = []
	
	for need in list(life['needs'].values()):
		if not survival.needs_to_satisfy(life, need):
			continue
		
		if survival.can_satisfy(life, need):
			_needs_to_satisfy.append(need)
		
		if not survival.can_satisfy(life, need) and not survival.can_potentially_satisfy(life, need):
			_needs_unmet.append(need)
			continue
		
		if not need in _needs_to_satisfy and not need in _needs_to_satisfy:
			_needs_to_meet.append(need)

	brain.store_in_memory(life, 'needs_to_meet', _needs_to_meet)
	brain.store_in_memory(life, 'needs_to_satisfy', _needs_to_satisfy)
	brain.store_in_memory(life, 'needs_unmet', _needs_unmet)

	if not _needs_to_meet and not _needs_to_satisfy:
		return False

def tick(life):
	if life['actions']:
		return True

	_needs_to_meet = brain.retrieve_from_memory(life, 'needs_to_meet')
	
	for need in _needs_to_meet:
		movement.collect_nearby_wanted_items(life, matches=need['match'], only_visible=False)
		break
	
	_needs_to_satisfy = brain.retrieve_from_memory(life, 'needs_to_satisfy')
	
	for need in _needs_to_satisfy:
		survival.satisfy(life, need)
