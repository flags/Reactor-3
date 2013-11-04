from globals import *

import alife


#Scale & Design
def puncture(item, target_structure, debug=True):
	if debug:
		logging.debug('%s is pucturing %s.' % (item['name'], target_structure['name']))
		logging.debug('%s\'s max speed is %s and is currently traveling at speed %s.' % (item['name'], item['max_speed'], item['speed']))
		logging.debug('The %s\'s material has a thickness of %s (with a max of %s).' % (target_structure['name'], target_structure['thickness'], target_structure['max_thickness']))
		logging.debug('')
		
	return (((item['speed']/item['max_speed'])*item['damage']['sharp'])*\
	       (target_structure['max_thickness']/target_structure['thickness']))*\
	       (item['size']/target_structure['size'])
