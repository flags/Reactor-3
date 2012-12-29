from globals import *
from math import *
import bullets
import random

random.seed()

def fire(life,target):
	theta = atan2((life['pos'][1]-target[1]),-(life['pos'][0]-target[0]))
	
	if theta < 0:
		theta += 2 * pi
	
	direction = (theta * (180/pi))
	
	direction += random.randint(-13,10)
	
	#print direction
	
	weapon = life['firing']
	bullets.create_bullet(life['pos'],direction,5,life)
	
	life['firing'] = None
