from globals import *

import life as lfe

import missions


def setup(life):
	if not life['mission_id']:
		return False
	
	print 'Working...', life['name']
	missions.do_mission(life, life['mission_id'])