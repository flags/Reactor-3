from globals import *

import life as lfe

import missions


def tick(life):
	if not life['mission_id']:
		return False
	
	missions.do_mission(life, life['mission_id'])