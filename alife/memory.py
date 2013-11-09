from globals import *

import life as lfe

import judgement
import rawparse
import action
import brain

import logging

def create_question(life, life_id, gist):
	_target = brain.knows_alife_by_id(life, life_id)
	
	if 'gist' in _target['questions']:
		return False
	
	_target['questions'].append(gist)

def get_questions_for_target(life, life_id):
	_knows = brain.knows_alife_by_id(life, life_id)
	
	return _knows['questions']

def ask_target_question(life, life_id):
	return get_questions_for_target(life, life_id).pop(0)

def rescore_history(life):
	pass
	#for memory in life['memory']:
	#	if (brain.get_flag(life, 'hungry') or brain.get_flag(life, 'thirsty')) and memory['text'] == 'consume_item':
	#		if not 'trust' in memory:
	#			memory['trust'] = -2
	#			memory['danger'] = 3
	#			print 'HATE!'

def detect_lies(life):
	pass

def reflect(life):
	while life['unchecked_memories']:
		_memory = lfe.get_memory_via_id(life, life['unchecked_memories'].pop())
		
		if not rawparse.raw_section_has_identifier(life, 'memory', _memory['text']):
			continue
		
		_return_value = lfe.execute_raw(life, 'memory', _memory['text'])
		
		if _return_value == 'investigate_chunk':
			judgement.judge_chunk(life, _memory['chunk_key'], investigate=True)

def process(life):
	detect_lies(life)
	rescore_history(life)
	reflect(life)