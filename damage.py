from globals import *

import life as lfe

import language
import graphics
import numbers
import items

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
	_velos = sum([abs(i) for i in bullet['velocity']])
	_falloff = numbers.clip(_velos, 0, bullet['max_speed'])/float(bullet['max_speed'])
	#_falloff = max(bullet['velocity'])/float(bullet['max_speed'])
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
	
	if _cut:
		_items_to_check = []
		for _item in [lfe.get_inventory_item(life, i) for i in lfe.get_items_attached_to_limb(life, limb)]:
			_items_to_check.append({'item': _item, 'visible': True})
			
			if 'container' in _item:
				for _item_in_container in _item['contains']:
					_items_to_check.append({'item': _item_in_container, 'visible': False, 'inside': _item['name']})
		
		for entry in _items_to_check:
			_item = entry['item']
			_thickness = _item['thickness']
			_item['thickness'] = numbers.clip(_item['thickness']-_cut, 0, 100)
			_cut -= _thickness
			_tear = _item['thickness']-_thickness
			_limb_in_context = False
			
			if _item['material'] == 'cloth':
				if _thickness and not _item['thickness']:
					#_msg.append('penetrates the %s' % _item['name'])
					graphics.message('%s\'s %s is destroyed!' % (language.get_introduction(life, posession=True), _item['name']))
				elif _tear<=-3:
					_msg.append('rips <own> %s' % _item['name'])
				elif _tear<=-2:
					_msg.append('tears <own> %s' % _item['name'])
				elif _tear<=-1:
					_msg.append('slightly tears <own> %s' % _item['name'])
				
				if _cut <= 0 and _item['thickness']:
					_msg.append('is stopped by <own> %s' % _item['name'])
					return ' '.join(_msg)
			
			elif _item['material'] == 'metal':
				if _thickness and not _item['thickness']:
					_msg.append('puncturing the %s' % _item['name'])
				elif _tear<=-3:
					_msg.append('denting the %s' % _item['name'])
				elif _tear<=-2:
					_msg.append('lightly denting the %s' % _item['name'])
				elif _tear<=-1:
					_msg.append('scraping the %s' % _item['name'])
				
				if _cut <= 0 and _item['thickness']:
					_msg.append(', finally stopped by the %s' % _item['name'])
					return ' '.join(_msg)
	
		if not lfe.limb_is_cut(life, limb):
			_cut_percentage = _cut/float(_actual_limb['size'])
			if _cut_percentage<=.25:
				_msg.append(', cutting <own> %s' % limb)
			elif _cut_percentage<=.5:
				_msg.append(', tearing <own> %s' % limb)
			elif _cut_percentage<=.75:
				_msg.append(', ripping open <own> %s' % limb)
			elif _cut_percentage<=1:
				_msg.append(', severing <own> %s!' % limb)
				return ' '.join(_msg)
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
			lfe.add_wound(life, limb, lodged_item=bullet, impact_velocity=bullet['velocity'])
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
	for _item in [lfe.get_inventory_item(target, i) for i in lfe.get_items_attached_to_limb(target, limb)]:
		_items_to_check.append({'item': _item, 'visible': True})
		
		if 'container' in _item:
			for _item_in_container in _item['contains']:
				_items_to_check.append({'item': _item_in_container, 'visible': False, 'inside': _item['name']})
	
	for entry in _items_to_check:
		_item = entry['item']
		_thickness = _item['thickness']
		_item['thickness'] = numbers.clip(_item['thickness']-_bite_strength, 0, 100)
		_bite_strength -= _thickness
		_tear = _item['thickness']-_thickness
		_limb_in_context = False
		
		if _item['material'] == 'cloth':
			if _thickness and not _item['thickness']:
				graphics.message('teeth rip through %s\'s %s!' % (language.get_name(target), _item['name']))
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