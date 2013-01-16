from math import *
import numpy

def clip(number,start,end):
	"""Returns `number`, but makes sure it's in the range of [start..end]"""
	return max(start, min(number, end))

def distance(pos1,pos2):
	return abs(pos2[1]-pos1[1])+abs(pos2[0]-pos1[0])

def velocity(direction,speed):
	rad = direction*(pi/180)
	velocity = numpy.multiply(numpy.array([cos(rad),sin(rad)]),speed)
	
	return [velocity[0],-velocity[1],0]

def direction_to(pos1,pos2):
	theta = atan2((pos1[1]-pos2[1]),-(pos1[0]-pos2[0]))
		
	if theta < 0:
		theta += 2 * pi
	
	return theta * (180/pi)
	
