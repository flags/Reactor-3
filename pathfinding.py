from copy import deepcopy
from globals import *
import numpy
import time
import sys

class astar:
	def __init__(self,start=None,end=None,omap=None,size=None,goals=None,blocking=None,dij=False,inverted=False):
		self.map = []
		self.omap = omap
		self.size = size
		self.dij = dij
		self.goals = goals
		self.inverted = inverted
		
		#if not blocking:
		self.blocking = []#var.blocking[:]
		#self.blocking.extend(var.solid)
		#else: self.blocking = blocking

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
				if self.omap[x][y][2] in self.blocking:
					self.map[y,x] = 0
		
		#for pos in blocking:
		#	self.map[pos[1],pos[0]] = 0
		
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
		_stime = time.time()
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
		
		print time.time()-_stime
	
	def find_path(self,start):
		if not self.dij:
			node = self.pmap[self.end[0]][self.end[1]]
			self.path = [self.end]
			
			_broken = False
			while not tuple(node) == tuple(start):
				if not node: _broken = True;break
				else: self.path.insert(0,node)
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
			
			if _x<0 or _x>=self.size[0] or _y<0 or _y>=self.size[1] or not self.map[_y,_x]: continue
			
			if (_x,_y) in self.clist and checkclist:
				continue 
			adj.append((_x,_y))
			
		return adj
