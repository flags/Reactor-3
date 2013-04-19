import life as lfe

import language
import numbers
import items

DAMAGE_LOOKUP = {'leather': 3}

def bullet_hit(life, bullet, limb):
	_velos = sum([abs(i) for i in bullet['velocity']])
	_falloff = numbers.clip(_velos, 0, bullet['max_speed'])/float(bullet['max_speed'])
	#_falloff = max(bullet['velocity'])/float(bullet['max_speed'])
	_damage = 0
	_cut = 0
	_bruise = 0
	_breaking = False
	_msg = ['The %(name)s' % bullet]
	
	if 'sharp' in bullet['damage']:
		_cut = int(round(bullet['damage']['sharp']*_falloff))
		print 'cut',_cut
	
	if _cut:		
		for _item in [lfe.get_inventory_item(life, i) for i in lfe.get_items_attached_to_limb(life, limb)]:
			_thickness = _item['thickness']
			_item['thickness'] = numbers.clip(_item['thickness']-_cut, 0, 100)
			_cut -= _thickness
			_tear = _item['thickness']-_thickness
							
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
				break
	
		if not lfe.limb_is_cut(life, limb):
			_msg.append('entering the %s' % limb)
			
			if _cut==1:
				_msg.append(', barely cutting it.')
			elif _cut==2:
				_msg.append(', tearing it open.')
			elif _cut==3:
				_msg.append(', severing it!')
				return _msg
			else:
				_msg.insert(1, 'hits the %s' % limb)
				_bruise = _cut
	
	print _falloff	, _cut
	
	return ' '.join(_msg)
