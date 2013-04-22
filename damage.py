import life as lfe

import language
import numbers
import items

import random

def bullet_hit(life, bullet, limb):
	_velos = sum([abs(i) for i in bullet['velocity']])
	_falloff = numbers.clip(_velos, 0, bullet['max_speed'])/float(bullet['max_speed'])
	#_falloff = max(bullet['velocity'])/float(bullet['max_speed'])
	_damage = 0
	_cut = 0
	_bruise = 0
	_breaking = False
	_lodged = False
	_msg = ['The %(name)s' % bullet]
	_msg.append('hits the %s,' % limb)
	
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
			print _item['name']
			_thickness = _item['thickness']
			_item['thickness'] = numbers.clip(_item['thickness']-_cut, 0, 100)
			_cut -= _thickness
			_tear = _item['thickness']-_thickness
			_limb_in_context = False
			
			if _item['material'] == 'cloth':
				if _thickness and not _item['thickness']:
					_msg.append('completely tearing apart the %s' % _item['name'])
				elif _tear<=-3:
					_msg.append('ripping through the %s' % _item['name'])
				elif _tear<=-2:
					_msg.append('tearing the %s' % _item['name'])
				elif _tear<=-1:
					_msg.append('slightly tearing the %s' % _item['name'])
				
				if _cut <= 0 and _item['thickness']:
					_msg.append(', finally stopped by the %s' % _item['name'])
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
			if _cut==1:
				if _limb_in_context:
					_msg.append(', barely cutting it.')
				else:
					_msg.append(', barely cutting the %s.' % limb)
			elif _cut==2:
				if _limb_in_context:
					_msg.append(', tearing it open')
				else:
					_msg.append(', tearing open the %s' % limb)
			elif _cut==3:
				if _limb_in_context:
					_msg.append(', ripping it open')
				else:
					_msg.append(', ripping open the %s' % limb)
			elif _cut==4:
				if _limb_in_context:
					_msg.append(', severing it!')
				else:
					_msg.append(', severing the %s!' % limb)
				return ' '.join(_msg)
			else:
				_bruise = _cut
		
			if _cut:
				lfe.add_wound(life, limb, cut=_cut)
			
			#TODO: How thick is skin?
			_cut -= 1
		
		if not _cut:
			return ' '.join(_msg)
		
		if not lfe.artery_is_ruptured(life, limb) and random.randint(0, 9)>=9-_cut:
			if _limb_in_context:
				_msg.append('rupturing an artery')
			else:
				_msg.append('and rupturing an artery,')
			
			lfe.add_wound(life, limb, artery_ruptured=True)
		
		if random.randint(0, 9)>=9-(_cut*2):
			_msg.append(', lodging itself in the %s' % limb)
			lfe.add_wound(life, limb, lodged_item=bullet)
			return ' '.join(_msg)
		else:
			_msg.append('exiting through the %s' % limb)
			lfe.add_wound(life, limb, cut=_cut/2)
	
	print _falloff	, _cut
	print ' '.join(_msg)
	return ' '.join(_msg)
