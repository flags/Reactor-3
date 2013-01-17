from copy import deepcopy
from globals import *
import logging
import numpy
import tiles
import time
import sys

class astar:
	def __init__(self,start=None,end=None,omap=None,size=None,goals=None,dij=False,inverted=False):
		self.map = []
		self.omap = omap
		self.size = size
		self.dij = dij
		self.goals = goals
		self.inverted = inverted

		if not self.dij:
			self.start = tuple(start)
			self.end = tuple(end)
			self.olist = [self.start]
			self.goals = []
		else:
			self.start = (0,0)
			self.end = tuple(self.goals.pop())
			self.olist = [self.end]

		self.clist = []
		
		#Let's make a few of these
		self.fmap = []
		self.gmap = []
		self.hmap = []
		self.pmap = []
		self.tmap = []
		for x in range(self.size[0]):
			self.fmap.append([0] * self.size[1])
			self.gmap.append([0] * self.size[1])
			self.hmap.append([0] * self.size[1])
			self.pmap.append([0] * self.size[1])
			self.tmap.append([0] * self.size[1])
			
		#Create our map
		self.map = numpy.ones((self.size[1],self.size[0]))
		
		for x in xrange(self.size[0]):
			for y in xrange(self.size[1]):
				#Can't walk if there's no ground beneath this position
				if not self.omap[x][y][self.start[2]]:
					self.map[y,x] = -2
					
					#TODO: Will probably need this at some point (for falling risk?)
					#for i in xrange(1,self.start[2]+1):
					#	if not self.omap[x][y][self.start[2]-1-i]:
					#		self.map[y,x] = -1-i
					#		
					#		break
				
				#But we can climb to this position if there is something to climb on
				if self.omap[x][y][self.start[2]+1]:
					self.map[y,x] = 2
				
					#Not if there's a tile above the position we'd be climing to!
					if self.omap[x][y][self.start[2]+2]:
						self.map[y,x] = 0
		
		#Calculate our starting node
		if not self.dij:
			self.hmap[start[0]][start[1]] = (abs(self.start[0]-end[0])+abs(self.start[1]-end[1]))*10
		else:
			if self.goals:
				for goal in self.goals:
					self.olist.append(goal)
		
		self.fmap[self.start[0]][self.start[1]] = self.hmap[self.start[0]][self.start[1]]
		
		self.calculate()
		
	def calculate(self):
		if self.map[self.end[1],self.end[0]] == 0:
			return False
		
		node = self.olist[0]
		
		_clist = self.clist
		_olist = self.olist
		_gmap = self.gmap
		_hmap = self.hmap
		_fmap = self.fmap
		_pmap = self.pmap
		while len(_olist):
			_olist.remove(node)
			
			#Is it the end?
			if tuple(node) == tuple(self.end) and not self.dij:
				_olist = []
				break
			
			_clist.append(node)
			_lowest = {'pos':None,'f':9000}
			
			#Check adjacent
			for adj in self.getadj(node):
				if not adj in _olist:
					#Calculate g score for adj
					if abs(node[0]-adj[0])+abs(node[1]-adj[1]) == 1:
						_gmap[adj[0]][adj[1]] = _gmap[node[0]][node[1]]+10
					else:
						_gmap[adj[0]][adj[1]] = _gmap[node[0]][node[1]]+14
					
					#Calculate h score for adj
					if not self.dij:
						_hmap[adj[0]][adj[1]] = (abs(adj[0]-self.end[0])+abs(adj[1]-self.end[1]))*10
					_fmap[adj[0]][adj[1]] = _gmap[adj[0]][adj[1]]+_hmap[adj[0]][adj[1]]
					_pmap[adj[0]][adj[1]] = node
					
					_olist.append(adj)
				
			for o in _olist:			
				#_lowest check
				if _fmap[o[0]][o[1]] < _lowest['f']:
					_lowest['pos'] = o
					_lowest['f'] = _fmap[o[0]][o[1]]
				
			
			if _lowest['pos']:
				node = _lowest['pos']
		
		if self.inverted:
			for y in range(self.size[1]):
				for x in range(self.size[0]):
					_fmap[x][y] = _fmap[x][y]*-1
			
		if not self.dij: self.find_path(self.start)
		
		if len(self.path)==1:
			if abs(self.start[0]-self.path[0][0])+abs(self.start[1]-self.path[0][1])>1:
				self.path = None
	
	def find_path(self,start):
		if not self.dij:
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
				
		else:
			#Roll downhill
			node = start
			self.path = []
			if self.inverted:
				moves = var.alife_fleesteps
				while moves:
					_lowest = {'pos':None,'f':1}
					for adj in self.getadj(node,checkclist=False):
						if self.fmap[adj[0]][adj[1]] < _lowest['f']:
							_lowest['pos'] = adj
							_lowest['f'] = self.fmap[adj[0]][adj[1]]
					
					if _lowest['pos']:
						node = _lowest['pos']
						self.tmap[node[0]][node[1]] = 1
						self.path.append(node)
					moves -= 1
			else:
				while self.fmap[node[0]][node[1]]:
					_lowest = {'pos':None,'f':9000}
					for adj in self.getadj(node,checkclist=False):
						if self.fmap[adj[0]][adj[1]] < _lowest['f']:
							_lowest['pos'] = adj
							_lowest['f'] = self.fmap[adj[0]][adj[1]]
					
					if _lowest['pos']:
						node = _lowest['pos']
						self.tmap[node[0]][node[1]] = 1
						self.path.append(node)
			
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

def path_from_dijkstra(start_position,dijkstra,downhill=False):
	_s_pos = start_position[:]
	_next_pos = {'pos': None,'score': 0}
	
	_path = []
	
	while 1:
		for x1 in range(-1,2):
			_x = (_s_pos[0]+x1)
			x = (_s_pos[0]-dijkstra['x_range'][0])+x1
			
			if dijkstra['x_range'][0]>=x or x>=len(dijkstra['map']):
				continue
			
			for y1 in range(-1,2):
				if (x1,y1) == (0,0):
					continue
				
				_y = (_s_pos[1]+y1)
				y = (_s_pos[1]-dijkstra['y_range'][0])+y1
				
				if dijkstra['y_range'][0]>y or y>=len(dijkstra['map'][0]):
					continue
				
				#print 'x',x,dijkstra['x_range'],
				#print 'y',y,dijkstra['y_range']
				if dijkstra['map'][x][y]==-1:
					continue
				
				_score = dijkstra['map'][x][y]
				
				if downhill:
					if _score < _next_pos['score']:
						_next_pos['score'] = _score
						_next_pos['pos'] = (_x,_y,0)
					
					continue
				
				if _score > _next_pos['score']:
					_next_pos['score'] = _score
					_next_pos['pos'] = (_x,_y,0)
		
		if _path and _path[len(_path)-1] == _next_pos['pos']:
			return _path
		elif _next_pos['pos']:
			if len(_path)>=2 and _next_pos['pos'] == _path[len(_path)-2]:
				return _path
			
			_path.append(_next_pos['pos'])
			_s_pos = _path[len(_path)-1][:]
		else:
			logging.info('No path found!')
			return _path
