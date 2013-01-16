############
# ALife v2 ########################
# Created by Luke Martin (flags)  #
###################################
# Started: 12:10 AM, 1/16/2013    #
# Ended: Probably not for a while #
###################################

from globals import *
import life as lfe
import pathfinding
import drawing
import logging
import numbers

def look(life):
	life['sight'] = []
	
	for ai in LIFE:
		if ai == life:
			continue
		
		if numbers.distance(life['pos'],ai['pos']) > 20:
			#TODO: "see" via other means?
			continue
		
		#TODO: Don't pass entire life, just id
		life['sight'].append(ai)
	
	logging.debug('\tTargets: %s' % (len(life['sight'])))

def understand(life):
	for item in life['sight']:
		if lfe.can_see(life,item['pos']):
			print 'Yo!'
			break

def think(life):
	logging.debug('*THINKING*')
	logging.debug('Look:')
	look(life)
	
	logging.debug('Understand:')
	understand(life)
