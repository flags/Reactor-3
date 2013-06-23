from globals import *

import brain

import random

MAX_INTROVERSION = 10
MAX_SOCIABILITY = 25
MAX_INTERACTION = 25
MAX_CHARISMA = 20

def init(life):
	life['stats']['will'] = 25
	life['stats']['sociability'] = random.randint(1, MAX_SOCIABILITY)
	life['stats']['introversion'] = random.randint(1, MAX_INTROVERSION)
	life['stats']['charisma'] = random.randint(1, MAX_CHARISMA)

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

def desires_group(life):
	if life['group']:
		return False
	
	
	brain.flag(life, 'wont_work', value=1000-(life['stats']['will']*15))

def desires_life(life, life_id):
	_diff = MAX_CHARISMA-abs(life['stats']['charisma']-LIFE[life_id]['stats']['charisma'])
	
	if _diff < life['stats']['sociability']:
		return True
	
	return False

def desires_interaction(life):
	return MAX_INTERACTION-life['stats']['sociability']

def get_antisocial_percentage(life):
	return life['stats']['introversion']/float(MAX_INTROVERSION)

def desires_group_threshold(life):
	return int(round(life['stats']['sociability']*get_antisocial_percentage(life)))

def get_employability(life):
	return 50
	