import brain

import judgement

import logging

def get_stance_towards(life, target):	
	_remembered_alife = brain.get_remembered_alife(life, target)

	if judgement.is_dangerous(life, target['id'])>0:
		return 'friendly'
	elif not _remembered_alife['score']:
		return 'neutral'
	else:
		return 'hostile'
