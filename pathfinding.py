from copy import deepcopy
from globals import *
import numbers
import logging
import numpy
import tiles
import time
import sys

class Astar:
	def __init__(self, start=None, end=None, omap=None, dist=None):
		self.map = []
		self.omap = omap

		self.start = tuple(start)
		self.end = tuple(end)
		self.olist = [self.start]
		self.goals = []

		self.clist = []
		
		_s = time.time()
		
		if not dist:
			dist = numbers.distance(start,end)+1
		
		if dist<75:
			dist=75
		
		_x_min = 0#numbers.clip(start[0]-dist,0,MAP_SIZE[0])
		_x_max = numbers.clip(start[0]+dist, 0, MAP_SIZE[0])
		_y_min = 0#numbers.clip(start[1]-dist,0,MAP_SIZE[1])
		_y_max = numbers.clip(start[1]+dist, 0, MAP_SIZE[1])
		
		self.size = (_x_max+1,_y_max+1)
		
		#Let's make a few of these
		self.fmap = numpy.zeros((self.size[1],self.size[0]))
		self.gmap = numpy.zeros((self.size[1],self.size[0]))
		self.hmap = numpy.zeros((self.size[1],self.size[0]))
		self.pmap = []
		self.tmap = numpy.zeros((MAP_SIZE[1],MAP_SIZE[0]))
		for x in range(self.size[0]):
			self.pmap.append([0] * self.size[1])
		
		#Create our map
		self.map = numpy.ones((self.size[1],self.size[0]))
		
		for _x in xrange(self.size[0]):
			_map_x_pos = _x+_x_min
			for _y in xrange(self.size[1]):
				_map_y_pos = _y+_y_min
				
				if _map_x_pos >= MAP_SIZE[0] or _map_y_pos >= MAP_SIZE[1]:
					continue
				
				#Can't walk if there's no ground beneath this position
				if not self.omap[_map_x_pos][_map_y_pos][self.start[2]]:
					self.map[_y,_x] = -2
					
					#TODO: Will probably need this at some point (for falling risk?)
					#for i in xrange(1,self.start[2]+1):
					#	if not self.omap[x][y][self.start[2]-1-i]:
					#		self.map[y,x] = -1-i
					#		
					#		break
				
				#But we can climb to this position if there is something to climb on
				if self.omap[_map_x_pos][_map_y_pos][self.start[2]+1]:
					self.map[_y,_x] = 2
				
					#Not if there's a tile above the position we'd be climing to!
					if self.omap[_map_x_pos][_map_y_pos][self.start[2]+2]:
						self.map[_y,_x] = 0
		
		start = (start[0]-_x_min,start[1]-_y_min)
		
		#Calculate our starting node
		self.hmap[start[1],start[0]] = (abs(self.start[0]-end[0])+abs(self.start[1]-end[1]))*10
		
		self.fmap[self.start[1],self.start[0]] = self.hmap[self.start[1],self.start[0]]
		
		#init time 0.00857901573181
		#print 'init time',time.time()-_s
		
		self.path = []
		
		self.calculate()
		
	def calculate(self):
		if self.map[self.end[1],self.end[0]] == 0:
			logging.warning('Pathfinding: Attempted to create path ending in an unpathable area.')
			return False
		
		node = self.olist[0]
		
		_clist = self.clist
		_olist = self.olist
		_gmap = self.gmap
		_hmap = self.hmap
		_fmap = self.fmap
		_pmap = self.pmap
		_stime = time.time()
		while len(_olist):
			_olist.remove(node)
			
			#Is it the end?
			if tuple(node) == tuple(self.end):
				_olist = []
				break
			
			_clist.append(node)
			_lowest = {'pos':None,'f':9000}
			
			#Check adjacent
			for adj in self.getadj(node):
				if not adj in _olist:
					#Calculate g score for adj
					if abs(node[0]-adj[0])+abs(node[1]-adj[1]) == 1:
						_gmap[adj[1],adj[0]] = _gmap[node[1],node[0]]+10
					else:
						_gmap[adj[1],adj[0]] = _gmap[node[1],node[0]]+14
					
					#Calculate h score for adj
					#_hmap[adj[1],adj[0]] = (abs(adj[0]-self.end[0])+abs(adj[1]-self.end[1]))*10
					
					xDistance = abs(adj[0]-self.end[0])
					yDistance = abs(adj[1]-self.end[1])
					if xDistance > yDistance:
						 _hmap[adj[1],adj[0]] = 14*yDistance + 10*(xDistance-yDistance)
					else:
						 _hmap[adj[1],adj[0]] = 14*xDistance + 10*(yDistance-xDistance)
					
					_fmap[adj[1],adj[0]] = _gmap[adj[1],adj[0]]+_hmap[adj[1],adj[0]]
					_pmap[adj[0]][adj[1]] = node
					
					_olist.append(adj)
				
			for o in _olist:			
				#_lowest check
				if _fmap[o[1],o[0]] < _lowest['f']:
					_lowest['pos'] = o
					_lowest['f'] = _fmap[o[1],o[0]]
				
			
			if _lowest['pos']:
				node = _lowest['pos']
		
		#if self.inverted:
		#	for y in range(self.size[1]):
		#		for x in range(self.size[0]):
		#			_fmap[x][y] = _fmap[x][y]*-1
			
		self.path = self.find_path(self.start)
		
		if len(self.path)==1:
			if abs(self.start[0]-self.path[0][0])+abs(self.start[1]-self.path[0][1])>1:
				self.path = None
		
		#print 'calc time',time.time()-_stime
	
	def get_path(self):
		return self.path
	
	def find_path(self,start):
		if self.map[self.end[1],self.end[0]] == 0:
			return [[self.start[0],self.start[1],0]]
		
		node = self.pmap[self.end[0]][self.end[1]]
		self.path = [[self.end[0],self.end[1],int(self.map[self.end[1],self.end[0]])]]
		
		_broken = False
		while not tuple(node) == tuple(start):
			if not node:
				_broken = True
				break
			else:
				self.path.insert(0,(node[0],node[1],int(self.map[node[1],node[0]])))
			
			self.tmap[node[0]][node[1]] = 1
			node = self.pmap[node[0]][node[1]]
		
		#There's a few ways to fix this...
		#The issue is that pmap[self.end[0]][self.end[1]]
		#fails, leading to only self.end being the path.
		#The only way to REALLY fix this is to track where A*
		#fails, which we can fix in getadj()
		#If (_x,_y) is in an array (list of ALife positions), then
		#we could walk backwards from there...
		if _broken:
			print self.end
			print 'Broken A*!'
			return self.start
			
		return self.path
	
	def getadj(self,pos,checkclist=True):
		adj = []
		
		for r in [(-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1)]:
			_x = pos[0]+r[0]
			_y = pos[1]+r[1]
			
			if _x<0 or _x>=self.size[0] or _y<0 or _y>=self.size[1] or not self.map[_y,_x]:
				continue
			
			if (_x,_y) in self.clist and checkclist:
				continue
			
			adj.append((_x,_y))
			
		return adj

def short_path(start,end,source_map):
	if source_map[end[0]][end[1]][start[2]+1]:
		if source_map[end[0]][end[1]][start[2]+2]:
			return [(start[0],start[1],0)]
		return [(end[0],end[1],2)]
	
	return [(end[0],end[1],0)]

def create_path(start,end,source_map):
	_dist = numbers.distance(start,end)
	
	for x1 in range(-1,2):
		for y1 in range(-1,2):
			if (start[0],start[1]) == (end[0]+x1,end[1]+y1):
				return short_path(start,end,source_map)
	
	return Astar(start=start,end=end,omap=source_map,dist=_dist).get_path()

def path_from_dijkstra(start_position,dijkstra,downhill=False):
	_s_pos = start_position[:]
	_path = []
	
	if downhill:
		_next = {'pos': [],'score': 9000}
	else:
		_next = {'pos': [],'score': 0}
	
	while 1:
		for x1 in range(-1,2):
			_x = (_s_pos[0]+x1)
			x = (_s_pos[0]-dijkstra['x_range'][0])+x1
			
			if 0>x or x>=dijkstra['x_range'][1]:
				continue
			
			for y1 in range(-1,2):
				if (x1,y1) == (0,0):
					continue
				
				_y = (_s_pos[1]+y1)
				y = (_s_pos[1]-dijkstra['y_range'][0])+y1
				
				if 0>y or y>=dijkstra['y_range'][1]:
					continue
				
				if (x,y) in dijkstra['ignore']:
					continue
				
				_dist = numbers.distance(_s_pos,(_x,_y))
				_score = dijkstra['map'][y,x]#*_dist
				#print _score
				
				if downhill:
					if _score <= _next['score']:
						_next['score'] = _score
						_next['pos'] = (_x,_y,0)
				else:
					#print _score,_next['score']
					if _score >= _next['score']:
						_next['score'] = _score
						_next['pos'] = (_x,_y,0)
		
		if _path and _path[len(_path)-1] == _next['pos']:
			return _path
		
		elif _next['score']<=0:
			return _path
		
		elif _next['pos']:
			if len(_path)>=2 and _next['pos'] == _path[len(_path)-2]:
				return _path
			
			_path.append(_next['pos'])
			_s_pos = _path[len(_path)-1][:]
		
		else:
			logging.info('No path found!')
			return _path

def path_from_dijkstra_old(start_position,dijkstra,downhill=False):
	_s_pos = start_position[:]
	
	if downhill:
		_next_pos = {'pos': [],'score': 9000}
	else:
		_next_pos = {'pos': [],'score': -9000}
	
	_path = []
	
	while 1:
		for x1 in range(-1,2):
			_x = (_s_pos[0]+x1)
			x = (_s_pos[0]-dijkstra['x_range'][0])+x1
			
			if 0>x or x>=dijkstra['x_range'][1]:
				continue
			
			for y1 in range(-1,2):
				if (x1,y1) == (0,0):
					continue
				
				_y = (_s_pos[1]+y1)
				y = (_s_pos[1]-dijkstra['y_range'][0])+y1
				
				if 0>y or y>=dijkstra['y_range'][1]:
					continue
				
				#print 'x',x,dijkstra['x_range'],
				#print 'y',y,dijkstra['y_range']
				if (x,y) in dijkstra['ignore']:
					continue
				
				_score = dijkstra['map'][y,x]
				
				if downhill:
					if _score < _next_pos['score'] and not (_x,_y,0) in _path:
						if _score == _next_pos['score']:
							_next_pos['pos'].append((_x,_y,0))
						else:
							_next_pos['score'] = _score
							_next_pos['pos'] = [(_x,_y,0)]
					
					continue
				
				if _score >= _next_pos['score'] and not (_x,_y,0) in _path:
					if _score == _next_pos['score']:
						_next_pos['pos'].append((_x,_y,0))
					else:
						_next_pos['score'] = _score
						_next_pos['pos'] = [(_x,_y,0)]
		
		#TODO: Tear this apart if we need to...
		if _path and _path[len(_path)-1] == _next_pos['pos']:
			return _path
		elif _next_pos['pos']:			
			_winning_pos = {'pos': None,'score': 3}
			for pos in _next_pos['pos']:
				_dist = numbers.distance(_s_pos,pos)
				if _dist < _winning_pos['score']:
					_winning_pos['pos'] = pos
					_winning_pos['score'] = _dist
			
			_next_pos['pos'] = []
			
			if len(_path)>=2 and _winning_pos['pos'] == _path[len(_path)-2]:
				return _path
			
			_path.append(_winning_pos['pos'])
			_s_pos = _path[len(_path)-1][:]
		else:
			logging.info('No path found!')
			return _path
