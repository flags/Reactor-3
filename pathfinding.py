from copy import deepcopy
from globals import *

import zones as zns
import life as lfe

import render_los
import numbers
import alife
import numpy
import tiles

import logging
import time
import sys

def astar(life, start, end, zones):
	_stime = time.time()
	
	_path = {'start': tuple(start),
	         'end': tuple(end),
	         'olist': [tuple(start)],
	         'clist': [],
	         'segments': [],
	         'map': []}

	_path['fmap'] = numpy.zeros((MAP_SIZE[1], MAP_SIZE[0]), dtype=numpy.int8)
	_path['gmap'] = numpy.zeros((MAP_SIZE[1], MAP_SIZE[0]), dtype=numpy.int8)
	_path['hmap'] = numpy.zeros((MAP_SIZE[1], MAP_SIZE[0]), dtype=numpy.int8)
	_path['pmap'] = []
	_path['tmap'] = numpy.zeros((MAP_SIZE[1], MAP_SIZE[0]), dtype=numpy.int8)
	
	for x in range(MAP_SIZE[0]):
		_path['pmap'].append([0] * MAP_SIZE[1])

	_path['map'] = numpy.zeros((MAP_SIZE[1], MAP_SIZE[0]))
	#KEY:
	#0: Unwalkable (can't walk there, too low/high)
	#1: Walkable
	#2: Travels up
	#3: Travels down
	
	for zone in [zns.get_slice(z) for z in zones]:
		_t = time.time()
		
		if not 'rotmap' in zone:
			zone['rotmap'] = numpy.rot90(numpy.fliplr(numpy.clip(numpy.array(zone['map']), -2, 9999999)))
			logging.debug('Generated rotmap for zone #%s' % zone['id'])
		
		#with open('mapout.txt', 'w') as mo:
			#for y in range(MAP_SIZE[1]):
				#_line = ''
				#for x in range(MAP_SIZE[0]):
					#if _nm[y,x]==zone['id']:
						#_line += ' '
					#elif _nm[y,x]==-1:
						#_line += '^'
					#else:
						#_line += str(_nm[y,x])#'#'
				
				#mo.write(_line+'\n')
		
		#print 'end',zone['z']
		_path['map'] = numpy.add(zone['rotmap'], _path['map'])
		#print time.time()-_t
	
	start = (start[0], start[1])
	
	_path['hmap'][start[1], start[0]] = (abs(_path['start'][0]-_path['end'][0])+abs(_path['start'][1]-_path['end'][1]))*10
	_path['fmap'][_path['start'][1], _path['start'][0]] = _path['hmap'][_path['start'][1],_path['start'][0]]

	#init time 0.00857901573181
	#      old 0.0220770835876
	#      new 0.000559091567993
	#print 'init time',time.time()-_stime
	
	#print 'init:',time.time()-_stime
	return walk_path({}, _path)

def walk_path(life, path):
	if path['map'][path['end'][1], path['end'][0]] == -2:
		logging.warning('Pathfinding: Attempted to create path ending in an unpathable area.')
		#print path['map'][path['end'][1]][path['end'][0]]
		return False

	node = path['olist'][0]

	_clist = path['clist']
	_olist = path['olist']
	_gmap = path['gmap']
	_hmap = path['hmap']
	_fmap = path['fmap']
	_pmap = path['pmap']
	_stime = time.time()

	while len(_olist):
		_olist.remove(node)

		if tuple(node) == path['end']:
			_olist = []
			break

		_clist.append(node)
		_lowest = {'pos':None,'f':9000}

		for adj in getadj(path, node):
			if not adj in _olist:
				if abs(node[0]-adj[0])+abs(node[1]-adj[1]) == 1:
					_gmap[adj[1],adj[0]] = _gmap[node[1],node[0]]+10
				else:
					_gmap[adj[1],adj[0]] = _gmap[node[1],node[0]]+14

				xDistance = abs(adj[0]-path['end'][0])
				yDistance = abs(adj[1]-path['end'][1])
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

	return find_path(path)

def getadj(path, pos, checkclist=True):
	adj = []

	for r in [(-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1)]:
		_x = pos[0]+r[0]
		_y = pos[1]+r[1]

		if _x<0 or _x>=MAP_SIZE[0] or _y<0 or _y>=MAP_SIZE[1] or path['map'][_y,_x]==-2:
			continue

		if (_x,_y) in path['clist'] and checkclist:
			continue

		adj.append((_x,_y))

	return adj

def find_path(path):
		if path['map'][path['end'][1], path['end'][0]] == -2:
			return [[path['start'][0], path['start'][1],0]]

		node = path['pmap'][path['end'][0]][path['end'][1]]
		_path = [[path['end'][0],path['end'][1],int(path['map'][path['end'][1],path['end'][0]])]]

		_broken = False
		while not tuple(node) == tuple(path['start']):
			if not node:
				_broken = True
				break
			else:
				_path.insert(0,(node[0], node[1],int(path['map'][node[1], node[0]])))

			path['tmap'][node[0]][node[1]] = 1
			node = path['pmap'][node[0]][node[1]]

		return _path

def short_path(life, start, end):
	_s = time.time()
	_line = render_los.draw_line(start[0], start[1], end[0], end[1])
	
	if not _line:
		return [start]
	
	_line.pop(0)
	
	for pos in _line:
		if not lfe.can_traverse(life, pos):
			return False
	
	return _line

def create_path(life, start, end, zones):
	_shortpath = short_path(life, start, end)
	if _shortpath:
		return _shortpath
	
	return astar(life, start, end, zones)