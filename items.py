from globals import *
import graphics as gfx
import logging
import json

def load_item(item):
	with open(os.path.join(ITEM_DIR,item+'.json'),'r') as e:
		return json.loads(''.join(e.readlines()))

def initiate_item(name):
	if name in ITEM_TYPES:
		logging.warning('Item type \'%s\' is already loaded. Reloading...' % name)
	
	item = load_item(name)
	
	if not 'prefix' in item:
		logging.warning('No prefix set for item type \'%s\'. Using default (%s).' % (name,DEFAULT_ITEM_PREFIX))
		item['prefix'] = DEFAULT_ITEM_PREFIX
	
	if not 'icon' in item:
		logging.warning('No icon set for item type \'%s\'. Using default (%s).' % (name,DEFAULT_ITEM_ICON))
		item['tile'] = DEFAULT_ITEM_ICON
	
	if not 'flags' in item:
		logging.error('No flags set for item type \'%s\'. Errors may occur.' % name)
		item['flags'] = ''
	
	if 'attaches_to' in item:
		item['attaches_to'] = item['attaches_to'].split('|')
	
	if 'capacity' in item:
		item['max_capacity'] = [int(c) for c in item['capacity'].split('x')]
		item['max_capacity'] = item['max_capacity'][0]*item['max_capacity'][1]
		item['capacity'] = 0
		item['storing'] = []
	
	if not 'size' in item:
		logging.warning('No size set for item type \'%s\'. Using default (%s).' % (name,DEFAULT_ITEM_SIZE))
		item['size'] = DEFAULT_ITEM_SIZE
	
	item['flags'] = item['flags'].split('|')
	
	item['size'] = 	[int(c) for c in item['size'].split('x')]
	item['size'] = item['size'][0]*item['size'][1]
	
	#Unicode isn't handled all that well on Windows for some reason...
	for key in item:
		_value = item[key]
		del item[key]
		item[str(key)] = _value
		
		if isinstance(item[key],unicode):
			item[key] = str(item[key])
	
	ITEM_TYPES[item['name']] = item
	
	return item

def create_item(name,_map,position=[0,0,2]):
	item = ITEM_TYPES[name].copy()
	
	item['uid'] = len(ITEMS)
	item['map'] = _map
	item['pos'] = list(position)
	item['realpos'] = list(position)
	item['velocity'] = [0,0,0]
	item['friction'] = 0
	item['gravity'] = SETTINGS['world gravity']
	
	ITEMS[item['uid']] = item
	
	return item

def get_item_from_uid(uid):
	return ITEMS[uid]

def get_items_at(position):
	_items = []
	
	for _item in ITEMS:
		item = ITEMS[_item]
		
		if item.has_key('id'):
			continue
		
		if item['pos'] == position:
			_items.append(item)
	
	return _items

def get_name(item):
	return '%s %s' % (item['prefix'],item['name'])

def move(item,velocity,friction=0.05):
	#TODO: We have 30 frames per second. Any formula for finding speeds using that?
	item['friction'] = friction
	item['velocity'] = velocity
	item['realpos'] = item['pos'][:]
	
	logging.debug('The %s flies off in an arc!' % item['name'])

def draw_items():
	for _item in ITEMS:
		item = ITEMS[_item]
		
		if item.has_key('id'):
			continue
		
		if item['pos'][0] >= CAMERA_POS[0] and item['pos'][0] < CAMERA_POS[0]+MAP_WINDOW_SIZE[0] and\
			item['pos'][1] >= CAMERA_POS[1] and item['pos'][1] < CAMERA_POS[1]+MAP_WINDOW_SIZE[1]:
			_x = item['pos'][0] - CAMERA_POS[0]
			_y = item['pos'][1] - CAMERA_POS[1]
		
			if not LOS_BUFFER[0][_y,_x]:
				continue
			
			gfx.blit_char(_x,_y,item['icon'],white,None)

def tick_all_items():
	for _item in ITEMS:
		item = ITEMS[_item]
		
		if not item['velocity'].count(0)==3:
			#if item['velocity'][0]:
			item['realpos'][0]+=item['velocity'][0]
				
			#Friction here if item on ground
			
			item['realpos'][1]+=item['velocity'][1]
				
			#Friction here if item on ground
							
			item['realpos'][2]+=item['velocity'][2]
			
			item['velocity'][2] -= item['gravity']
			
			_nx = int(item['realpos'][0])
			_ny = int(item['realpos'][1])
			_nz = int(item['realpos'][2])
			
			item['velocity'][2] -= item['gravity']
			
			#Collisions!
			#Kinda complicated things going on here...
			#Basically this `if` statement says there is some kind of
			#collision at the position we're moving to, but nothing else.
			#We have to figure all of that out next.
			#print _nx,_ny,_nz
			
			if item['map'][_nx][_ny][_nz]:
				#print _nx,_ny,_nz,'speed of impact',_ny-item['pos'][1],_nz-item['pos'][2]
				
				#We know there's a collision, but how should the item react?
				#First we find the difference between the new position and the
				#old.
				_x_change = _nx-item['pos'][0]
				_y_change = _ny-item['pos'][1]
				_z_change = _nz-item['pos'][2]
				
				if _x_change:
					item['velocity'][0] = -(item['velocity'][0]/2)
					
					#print 'x-collision:',item['velocity'][0]
				
				#A positive/negative _x_change says we made contact to the right/left
				if _y_change:
					item['velocity'][1] = -(item['velocity'][1]/2)
					
					#print 'y-collision:',item['velocity'][1]
				
				if _z_change>0:
					if _z_change>0:
						item['velocity'][2] = -(item['velocity'][2]/2)
						
						#print 'z-collision:',item['velocity'][2]
					
				elif _z_change<0:
					item['velocity'][0] = 0
					item['velocity'][1] = 0
					item['velocity'][2] = 0
					item['gravity'] = 0
					
					print 'z-collision: resting at',_nz
			
			else:
				item['gravity'] = 0.1
				
			item['pos'] = [_nx,_ny,_nz]
			
			if not item['velocity'][2]:
				for i in range(0,2):
					if item['velocity'][i]>0:
						item['velocity'][i]-=item['friction']
						
						if item['velocity'][i]<0:
							item['velocity'][i]=0
						
					elif item['velocity'][i]<0:
						item['velocity'][i]+=item['friction']
						
						if item['velocity'][i]>0:
							item['velocity'][i]=0
			
			if item['velocity'].count(0)==3:
				logging.debug('The %s comes to a rest at %s,%s,%s.' %
					(item['name'],item['pos'][0],item['pos'][1],item['pos'][2]))
