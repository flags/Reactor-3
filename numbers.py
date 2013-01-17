from globals import *
from math import *
import logging
import numpy
import tiles
import copy
import time

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
	
def create_dijkstra_map(center,source_map,size=(100,100),calculate=None,**kvargs):
	_map = []
	
	_min_x = clip(center[0]-(size[0]/2),0,MAP_SIZE[0])
	_max_x = clip(center[0]+(size[0]/2),0,MAP_SIZE[0])
	
	_min_y = clip(center[1]-(size[1]/2),0,MAP_SIZE[1])
	_max_y = clip(center[1]+(size[1]/2),0,MAP_SIZE[1])
	
	_stime = time.time()
	for x in range(_min_x,_max_x):
		#x = _x-_min_x
		_col = []
		
		for y in range(_min_y,_max_y):
			#y = _y-_min_y
			
			if source_map[x][y][center[2]+1]:
				_col.append(-1)
				
				continue
			
			if calculate:
				_score = abs(calculate((x,y),**kvargs))
			else:
				_score = distance(center,(x,y))
			
			_col.append(_score)
		
		_map.append(_col)
	
	#logging.info('Dijkstra map took: %s, size %s,%s' % (str(time.time()-_stime),(_max_x-_min_x),(_max_y-_min_y)))
	
	return {'map': _map,
		'x_range': (_min_x,_max_x),
		'y_range': (_min_y,_max_y)}

def draw_dijkstra(dijkstra):
	for _y in range(dijkstra['y_range'][0],dijkstra['y_range'][1]):
		y = _y-dijkstra['y_range'][0]
		
		for _x in range(dijkstra['x_range'][0],dijkstra['x_range'][1]):
			x = _x-dijkstra['x_range'][0]
			
			#if _x == 20:
			#	continue
			
			#print _x,dijkstra['x_range']#,_y#,dijkstra['x_range'][1],dijkstra['y_range'][1]
			_score = clip(dijkstra['map'][x][y],0,9)
			
			print '%s' % _score,
		
		print

#_a = create_dijkstra_map((90,10,2),[],size=(20,20))
#draw_dijkstra(_a)
