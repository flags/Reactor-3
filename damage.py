from globals import *

import life as lfe

import language
import graphics
import numbers
import timers
import items

import logging
import random

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
	_falloff = sum([abs(i) for i in bullet['velocity']])/sum([abs(i) for i in bullet['start_velocity']])
	_damage = 0
	_cut = 0
	_bruise = 0
	_breaking = False
	_lodged = False
	_owner = LIFE[bullet['owner']]
	_actual_limb = lfe.get_limb(life, limb)
	
	if 'player' in _owner:
		if bullet['aim_at_limb'] == limb:
			_msg = ['The round hits']
		elif not limb in life['body']:
			return 'The round misses entirely!'
		else:
			_msg = ['The round misses slightly']
		_detailed = True
	else:
		_msg = ['%s shoots' % language.get_name(_owner)]
		_detailed = False
	
	#_msg = ['The %(name)s' % bullet]
	#_msg.append('hits the %s,' % limb)
	
	#Language stuff
	_limb_in_context = True
	
	if 'sharp' in bullet['damage']:
		_cut = int(round(bullet['damage']['sharp']*_falloff))
		print 'cut',_cut
		print 'falloff', _falloff
	
	if _cut:
		_items_to_check = []
		for _item in lfe.get_items_attached_to_limb(life, limb):
			_items_to_check.append({'item': _item, 'visible': True})
			_actual_item = items.get_item_from_uid(_item)
			
			if 'storing' in _actual_item:
				for _item_in_container in _actual_item['storing']:
					_items_to_check.append({'item': _item_in_container, 'visible': False})
		
		for entry in _items_to_check:
			_item = items.get_item_from_uid(entry['item'])
			print '***HIT***', _item['name']
			
			if not 'thickness' in _item:
				logging.warning('Item \'%s\' has no set thickness. Guessing...' % _item['name'])
				_item['thickness'] = _item['size']/2
			
			_thickness = _item['thickness']
			_item['thickness'] = numbers.clip(_item['thickness']-_cut, 0, 100)
			_tear = _item['thickness']-_thickness
			_limb_in_context = False
			
			if _item['material'] == 'cloth':
				if _thickness and not _item['thickness']:
					if entry['visible']:
						_msg.append(', destroying <own> %s' % _item['name'])
					else:
						_msg.append(', destroying something')
				elif _tear<=-3:
					if entry['visible']:
						_msg.append(', ripping <own> %s' % _item['name'])
					else:
						_msg.append(', ripping something')
				elif _tear<=-2:
					if entry['visible']:
						_msg.append(', tearing <own> %s' % _item['name'])
					else:
						_msg.append(', tearing something')
				elif _tear<=-1:
					if entry['visible']:
						_msg.append(', slightly tearing <own> %s' % _item['name'])
					else:
						_msg.append(', slightly ripping something')
				
				_cut -= _thickness/2
			
			elif _item['material'] == 'metal':
				if _thickness and not _item['thickness']:
					if entry['visible']:
						_msg.append(', puncturing %s' % items.get_name(_item))
					else:
						_msg.append(', puncturing something')
					
					if _item['type'] == 'explosive':
						timers.create(_item, action.make_small_script(function='explode',
	                                       item=_item['uid']),
	              15+value)
				elif _tear<=-3:
					if entry['visible']:
						_msg.append(', denting %s' % items.get_name(_item))
					else:
						_msg.append(', denting something')
				elif _tear<=-2:
					if entry['visible']:
						_msg.append(', lightly denting %s' % items.get_name(_item))
					else:
						_msg.append(', lightly denting something')
				elif _tear<=-1:
					if entry['visible']:
						_msg.append(', scraping %s' % items.get_name(_item))
					else:
						_msg.append(', scraping something')
				
				_cut -= _thickness
	
			if _cut <= 0:
				return own_language(life, _msg)+'.'
	
		#if not lfe.limb_is_cut(life, limb):
		_cut_percentage = _cut/float(_actual_limb['size'])
		if _cut_percentage<=.25:
			_msg.append(', cutting <own> %s' % limb)
		elif _cut_percentage<=.5:
			_msg.append(', tearing <own> %s' % limb)
		elif _cut_percentage<=.75:
			_msg.append(', ripping open <own> %s' % limb)
		elif _cut_percentage<=1:
			_msg.append(', severing <own> %s!' % limb)
		else:
			_bruise = _cut
	
		if _cut:
			lfe.add_wound(life, limb, cut=_cut, impact_velocity=bullet['velocity'])
		
		#TODO: How thick is skin?
		_cut -= 1
		
		if not _cut or not limb in life['body']:
			return own_language(life, _msg)+'.'
		
		#if not lfe.artery_is_ruptured(life, limb) and random.randint(0, 9)>=9-_cut:
		#	if _limb_in_context:
		#		_msg.append('rupturing an artery')
		#	else:
		#		_msg.append('and rupturing an artery,')
		#	
		#	lfe.add_wound(life, limb, artery_ruptured=True)
		
		if random.randint(0, 9)>=9-(_cut*2):
			_msg.append('. It is lodged!')
			lfe.add_wound(life, limb, lodged_item=bullet['uid'], impact_velocity=bullet['velocity'])
		else:
			lfe.add_wound(life, limb, cut=_cut/2, impact_velocity=bullet['velocity'])
	
	_ret_string = own_language(life, _msg)
	
	if _ret_string.endswith('!'):
		return _ret_string
	else:
		return _ret_string+'.'

def bite(life, target_id, limb):
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