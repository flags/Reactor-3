from . import brain

from . import judgement

import logging

def get_stance_towards(life, target_id):
	_know = brain.knows_alife_by_id(life, target_id)
	
	if _know:
		if judgement.can_trust(life, target_id):
			return 'friendly'
		elif judgement.is_target_dangerous(life, target_id):
			return 'hostile'
		else:
			return 'neutral'
	else:
		return 'neutral'