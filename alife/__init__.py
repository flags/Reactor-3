############
# ALife v2 ########################
# Created by Luke Martin (flags)  #
###################################
# Started: 12:10 AM, 1/16/2013    #
# Ended: Probably not for a while #
###################################

from alife import combat, survival, sight, sound, core

def think(life, source_map):
	sight.look(life)
	sound.listen(life)
	core.understand(life, source_map)
