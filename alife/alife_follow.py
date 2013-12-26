from globals import *

import life as lfe

import judgement
import movement
import sight


def tick(life):
	_guard = judgement.get_target_to_guard(life)
	
	if _guard:
		return movement.find_target(life, _guard, follow=False, distance=sight.get_vision(life)*.25, call=False)
	
	return movement.find_target(life, judgement.get_target_to_follow(life), follow=True, call=False)