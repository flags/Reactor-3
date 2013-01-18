from globals import *
import graphics as gfx
import numbers
import bullets
import random
import items

random.seed()

def get_feed(weapon):
	return weapon[weapon['feed']]

def get_fire_mode(weapon):
	"""Returns current fire mode for a weapon."""
	return weapon['firemodes'][weapon['firemode']]

def fire(life,target):
	weapon = life['firing']
	
	_mode = get_fire_mode(weapon)
	if _mode == 'single':
		_bullets = 1
	elif _mode == '3burst':
		_bullets = 3
	
	_ooa = False
	for i in range(_bullets):
		_feed = get_feed(weapon)
		
		if not _feed or (_feed and not _feed['rounds']):
			if 'player' in life:
				gfx.message('*Click*')
			
			_ooa = True
			continue
		
		direction = numbers.direction_to(life['pos'],target)
		direction += random.randint(-13,10)
		
		#TODO: Clean this up...
		#bullets.create_bullet(life['pos'],direction,5,life)
		_bullet = _feed['rounds'].pop()
		_bullet['owner'] = life['id']
		del _bullet['parent']
		items.move(_bullet,direction,5)
	
	if _ooa:
		if 'player' in life:
			gfx.message('You are out of ammo.')
	
	life['firing'] = None
