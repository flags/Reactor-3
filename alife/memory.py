from globals import *

import life as lfe

from . import judgement
from . import rawparse
from . import action
from . import speech
from . import brain
from . import jobs

import logging

def create_question(life, life_id, gist, ignore_if_said_in_last=0, recent_time=0, **kwargs):
	_target = brain.knows_alife_by_id(life, life_id)
	_question = {'gist': gist, 'args': kwargs}
	
	if not _target:
		logging.critical('%s does not know %s but is creating questions for them.' % (' '.join(life['name']), ' '.join(LIFE[life_id]['name'])))
		return False
	
	if _target['time_visible'] < recent_time:
		return False
	
	if _question in _target['questions']:
		return False
	
	_sent = speech.has_sent(life, life_id, gist)
	
	if _sent and (WORLD_INFO['ticks']-_sent<ignore_if_said_in_last or ignore_if_said_in_last == -1):
		return False
	
	speech.send(life, life_id, gist)
	_target['questions'].append(_question)
	
	#logging.debug('%s created question for %s: %s' % (' '.join(life['name']), ' '.join(LIFE[life_id]['name']), gist))

def create_order(life, life_id, order, message, **kwargs):
	_target = brain.knows_alife_by_id(life, life_id)
	_order = {'active': True, 'order': order, 'message': message, 'args': kwargs}
	
	if not _target:
		logging.critical('%s does not know %s but is giving orders to them.' % (' '.join(life['name']), ' '.join(LIFE[life_id]['name'])))
		return False
	
	if _order in list(_target['orders'].values()):
		return False
	
	_order['active'] = False
	if _order in list(_target['orders'].values()):
		return False
	
	_order['active'] = True
	_target['orders'][str(_target['orderid'])] = _order
	_target['orderid'] += 1
	
	logging.debug('%s created order for %s: %s' % (' '.join(life['name']), ' '.join(LIFE[life_id]['name']), order))

def get_questions_for_target(life, life_id):
	_target = brain.knows_alife_by_id(life, life_id)
	
	return _target['questions']

def get_orders_for_target(life, life_id, active_only=True):
	_active_orders = []
	for order in list(brain.knows_alife_by_id(life, life_id)['orders'].values()):
		if active_only and not order['active']:
			continue
		
		_active_orders.append(order)
	
	return _active_orders

def ask_target_question(life, life_id):
	return get_questions_for_target(life, life_id).pop(0)

def give_target_order(life, life_id):
	return get_orders_for_target(life, life_id)[0]['order']

def take_order(life, life_id):
	_orders = get_orders_for_target(life, life_id)

	if not _orders:
		return False
	
	_order = _orders[0]
	_order['active'] = False
	
	if 'job_id' in _order['args']:
		jobs.join_job(_order['args']['job_id'], life_id)
	
	return True

def reject_order(life, life_id):
	_orders = get_orders_for_target(life, life_id)

	if not _orders:
		return False
	
	_order = _orders[0]
	_order['active'] = False
	
	if 'job_id' in _order['args']:
		jobs.join_job(_order['args']['job_id'], life_id)
	
	return True

def give_target_order_message(life, life_id):
	_orders = get_orders_for_target(life, life_id)
	print(life['name'], LIFE[life_id]['name'], 'ORDER MESSAGE', _orders[0]['message'])
	return _orders[0]['message']

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

def process(life):
	detect_lies(life)
	rescore_history(life)
