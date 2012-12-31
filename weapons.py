from globals import *
import numbers
import bullets
import random

random.seed()

def fire(life,target):
	for i in range(4):
		direction = numbers.direction_to(life['pos'],target)
		direction += random.randint(-13,10)
		
		weapon = life['firing']
		bullets.create_bullet(life['pos'],direction,5,life)
	
	life['firing'] = None
