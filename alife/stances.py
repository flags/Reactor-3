import brain

import logging

def get_stance_towards(life, target):	
	_remembered_alife = brain.get_remembered_alife(life, target)

	if _remembered_alife['score']>0:
		return 'friendly'
	elif not _remembered_alife['score']:
		return 'neutral'
