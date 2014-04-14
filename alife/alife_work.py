from globals import *

import life as lfe

import missions


def tick(life):
	if life['missions']:
		missions.do_mission(life, life['missions'].keys()[0])
