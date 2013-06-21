from globals import *

import brain

import random

def init(life):
	#Will - t
	life['stats'] = {}
	life['stats']['will'] = 25

def desires_job(life):
	_wont = brain.get_flag(life, 'wont_work')
	if life['job'] or _wont:
		if _wont:
			_wont = brain.flag(life, 'wont_work', value=_wont-1)
			
		return False
	
	if life['stats']['will']>random.randint(0, 100-(life['stats']['will']/2)):
		return True
	
	brain.flag(life, 'wont_work', value=1000-(life['stats']['will']*15))
	return False

def get_employability(life):
	return 50