from globals import *
import numbers
import bullets
import random

random.seed()

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
	
	for i in range(_bullets):
		direction = numbers.direction_to(life['pos'],target)
		direction += random.randint(-13,10)
		
		bullets.create_bullet(life['pos'],direction,5,life)
	
	life['firing'] = None
