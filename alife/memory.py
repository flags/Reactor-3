from globals import *

import life as lfe

import judgement
import rawparse
import action
import brain
import jobs

import logging

def create_question(life, life_id, gist):
	_target = brain.knows_alife_by_id(life, life_id)
	
	if gist in _target['questions']:
		return False
	
	_target['questions'].append(gist)

def create_order(life, life_id, order, message, **kwargs):
	_target = brain.knows_alife_by_id(life, life_id)
	
	_order = {'order': order, 'message': message, 'args': kwargs}
	
	if _order in _target['orders'].values():
		return False
	
	_target['orders'][str(_target['orderid'])] = _order
	_target['orderid'] += 1

def get_questions_for_target(life, life_id):
	_target = brain.knows_alife_by_id(life, life_id)
	
	return _target['questions']

def get_orders_for_target(life, life_id):
	_target = brain.knows_alife_by_id(life, life_id)
	
	return _target['orders']

def ask_target_question(life, life_id):
	return get_questions_for_target(life, life_id).pop(0)

def give_target_order(life, life_id):
	_orders = get_orders_for_target(life, life_id)
	_order = _orders[_orders.keys()[0]]['order']
	
	return _order

def take_order(life, life_id):
	_orders = get_orders_for_target(life, life_id)
	_order = _orders[_orders.keys()[0]]
	
	print _order
	if 'job_id' in _order['args']:
		jobs.join_job(_order['args']['job_id'], life_id)
	
	return _order

def give_target_order_message(life, life_id):
	_orders = get_orders_for_target(life, life_id)
	_message = _orders[_orders.keys()[0]]['message']
	
	return _message

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