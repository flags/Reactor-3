from globals import *

import judgement
import groups
import brain

import logging
import random

MAX_WILLPOWER = 25
MAX_INTROVERSION = 10
MAX_SOCIABILITY = 25
MAX_INTERACTION = 25
MAX_CHARISMA = 20

def init(life):
	life['stats']['will'] = random.randint(1, MAX_WILLPOWER)
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

def desires_life(life, life_id):
	_diff = MAX_CHARISMA-abs(life['stats']['charisma']-LIFE[life_id]['stats']['charisma'])
	
	if _diff < life['stats']['sociability']:
		return True
	
	return False

def desires_interaction(life):
	return MAX_INTERACTION-life['stats']['sociability']

def desires_conversation_with(life, life_id):
	_knows = brain.knows_alife_by_id(life, life_id)
	
	if not _knows:
		logging.error('FIXME: Improperly Used Function: Doesn\'t know talking target.')
		return False
	
	if not judgement.can_trust(life, life_id):
		return False
	
	return True

def desires_to_create_group(life):
	if life['group']:
		return False
	
	if life['stats']['will'] >= MAX_WILLPOWER*.5:
		return True
	
	return False

def desires_group(life):
	#judgement.judge_group(life, life['group'])>get_minimum_group_score(life):
	if life['group'] and len(groups.get_group(life['group'])['members'])==1:
		return False
	
	_trusted = sum([brain.knows_alife_by_id(life, t)['trust'] for t in judgement.get_trusted(life, visible=True)])
	_not_trusted = sum([brain.knows_alife_by_id(life, t)['trust'] for t in judgement.get_untrusted(life, visible=True)])
	
	if _trusted < _not_trusted:
		return False
	
	return True

def desires_camp(life):
	if life['group'] and groups.is_leader(life['group'], life['id']):
		if not groups.get_camp(life['group']):
			return True
	
	return False

def get_antisocial_percentage(life):
	return life['stats']['introversion']/float(MAX_INTROVERSION)

def get_minimum_group_score(life):
	#TODO: Placeholder
	return 0

def get_max_group_size(life):
	return int(round(life['stats']['sociability']*get_antisocial_percentage(life)))

def get_employability(life):
	return 50

def wants_group_members(life):
	if not life['group']:
		return False
	
	_group = groups.get_group(life['group'])
	if len(_group)<get_max_group_size(life):
		return True
	
	return False
	