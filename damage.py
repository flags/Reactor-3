from globals import *

import life as lfe

import language
import graphics
import numbers
import timers
import items
import alife

import logging
import random

#Scale & Design
def get_puncture_value(item, target_structure, target_structure_name='object', debug=True):
	_damage = (((item['speed']/float(item['max_speed']))*item['damage']['sharp'])*\
	           (target_structure['max_thickness']/float(target_structure['thickness'])))*\
	           (item['size']/float(numbers.get_surface_area(target_structure)))
	if debug:
		logging.debug('%s is pucturing %s.' % (item['name'], target_structure_name))
		logging.debug('%s\'s max speed is %s and is currently traveling at speed %s.' % (item['name'], item['max_speed'], item['speed']))
		logging.debug('The %s\'s material has a thickness of %s (with a max of %s).' % (target_structure_name, target_structure['thickness'], target_structure['max_thickness']))
		logging.debug('%s has a puncture rating of %s.' % (item['name'], item['damage']['sharp']))
		logging.debug('Size of %s: %s, size of %s: %s' % (item['name'], item['size'], target_structure_name, target_structure['size']))
		logging.debug('The %s does %s points of damage to the %s.' % (item['name'], _damage, target_structure_name))
	
	return _damage

def own_language(life, message):
	_mentioned_name = False
	_ret_string = ''
	for txt in message:
		if 'player' in life:
			_ret_string += txt.replace('<own>', 'your')
		else:
			_name = txt.replace('<own>', language.get_name_ownership(life, pronoun=_mentioned_name))
			
			if not _name == txt:
				_mentioned_name = True
			
			_ret_string += _name
	
	return _ret_string

def bullet_hit(life, bullet, limb):
	_owner = LIFE[bullet['shot_by']]
	_actual_limb = lfe.get_limb(life, limb)
	_items_to_check = []
	
	if 'player' in _owner:
		if bullet['aim_at_limb'] == limb:
			_msg = ['The round hits']
		elif not limb in life['body']:
			return 'The round misses entirely!'
		else:
			_msg = ['The round misses slightly']
		_detailed = True
	elif 'player' in life:
		_msg = ['The round hits']
	else:
		_msg = ['%s hits %s\'s %s' % (items.get_name(bullet), life['name'][0], limb)]
	
	for item_uid in lfe.get_items_attached_to_limb(life, limb):
		_items_to_check.append({'item': item_uid, 'visible': True})
		_item = items.get_item_from_uid(item_uid)
		
		if 'storing' in _item:
			for item_in_container_uid in _item['storing']:
				_chance_of_hitting_item = bullet['size']*(_item['capacity']/float(_item['max_capacity']))
				
				if random.uniform(0, 1)<_chance_of_hitting_item:
					continue
				
				_items_to_check.append({'item': item_in_container_uid, 'visible': False})
		
	for entry in _items_to_check:
		_item = items.get_item_from_uid(entry['item'])
		_item_damage = get_puncture_value(bullet, _item, target_structure_name=_item['name'])
		_item['thickness'] = numbers.clip(_item['thickness']-_item_damage, 0, _item['max_thickness'])
		
		_speed_mod = _item_damage
		bullet['speed'] *= _speed_mod
		bullet['velocity'][0] *= _speed_mod
		bullet['velocity'][1] *= _speed_mod
		
		if not _item['thickness']:
			_msg.append(', destroying the %s' % _item['name'])

			if _item['type'] == 'explosive':
				items.explode(_item)
			else:
				items.delete_item(_item)
		else:
			if bullet['speed']<=1:
				_msg.append(', lodging itself in %s' % items.get_name(_item))
				_ret_string = own_language(life, _msg)
			
				if _ret_string.endswith('!'):
					return _ret_string
				else:
					return _ret_string+'.'
			else:
				if 'material' in _item:
					if _item['material'] == 'metal':
						_msg.append(', puncturing the %s' % _item['name'])
					else:
						_msg.append(', ripping through the %s' % _item['name'])
	
	_damage = get_puncture_value(bullet, _actual_limb, target_structure_name=limb)
	_actual_limb['thickness'] = numbers.clip(_actual_limb['thickness']-_damage, 0, _actual_limb['max_thickness'])
	_damage_mod = 1-(_actual_limb['thickness']/float(_actual_limb['max_thickness']))
	
	if limb in life['body']:
		_msg.append(', '+lfe.add_wound(life, limb, cut=_damage*_damage_mod, impact_velocity=bullet['velocity']))
	
	_ret_string = own_language(life, _msg)
	
	if _ret_string.endswith('!'):
		return _ret_string
	else:
		return _ret_string+'.'

def bite(life, target_id, limb):
	logging.debug('%s bit %s in the %s.' % (' '.join(life['name']), ' '.join(LIFE[target_id]['name']), limb))
	target = LIFE[target_id]
	_msg = ['%s' % language.get_introduction(life)]
	
	_bite_strength = random.randint(1, 3)
	
	if numbers.distance(life['pos'], target['pos'])>1:
		_msg.append('bites the air')
		
		return ' '.join(_msg)+'.'
	
	_items_to_check = []
	
	for _item in lfe.get_items_attached_to_limb(target, limb):
		_items_to_check.append({'item': _item, 'visible': True})
		_actual_item = items.get_item_from_uid(_item)
		
		if 'storing' in _actual_item:
			for _item_in_container in _actual_item['storing']:
				_items_to_check.append({'item': _item_in_container, 'visible': False})
	
	for entry in _items_to_check:
		_item = items.get_item_from_uid(entry['item'])

		if not 'thickness' in _item:
			logging.warning('Item \'%s\' has no set thickness. Guessing...' % _item['name'])
			_item['thickness'] = _item['size']/2
		
		_thickness = _item['thickness']
		_item['thickness'] = numbers.clip(_item['thickness']-_bite_strength, 0, 100)
		_bite_strength -= _thickness
		_tear = _item['thickness']-_thickness
		_limb_in_context = False
		
		if _item['material'] == 'cloth':
			if _thickness and not _item['thickness']:
				_msg.append('rips through <own> %s' % _item['name'])
			elif _tear<=-3:
				_msg.append('rips <own> %s' % _item['name'])
			elif _tear<=-2:
				_msg.append('tears <own> %s' % _item['name'])
			elif _tear<=-1:
				_msg.append('slightly tears <own> %s' % _item['name'])
			
			if _bite_strength <= 0 and _item['thickness']:
				_msg.append('is stopped by <own> %s' % _item['name'])
				return ' '.join(_msg)
	
	#if not lfe.limb_is_cut(target, limb):
	if _bite_strength==1:
		_msg.append(', cutting <own> %s' % limb)
	elif _bite_strength==2:
		_msg.append(', tearing <own> %s' % limb)
	elif _bite_strength==3:
		_msg.append(', ripping open <own> %s' % limb)

	if _bite_strength:
		lfe.add_wound(target, limb, cut=_bite_strength)
	
	#TODO: How thick is skin?
	_bite_strength -= 1
	
	#if not _bite_strength:
	#	return ' '.join(_msg)
	
	_ret_string = own_language(target, _msg)
	
	return _ret_string+'.'