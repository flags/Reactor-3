from globals import *

import life as lfe

from . import judgement
from . import movement
from . import groups
from . import speech
from . import action
import events
from . import brain
from . import stats
from . import jobs


def setup(life):
	if not life['group']:
		#if not stats.desires_to_create_group(life):
		#	return False
		
		#groups.create_group(life)
		return False
	
	if not groups.is_leader_of_any_group(life):
		return False
	
	_group = groups.get_group(life, life['group'])
	
	#groups.manage_jobs(life, life['group'])
	#groups.manage_territory(life, life['group'])
	groups.manage_combat(life, life['group'])
	groups.manage_raid(life, life['group'])
	#groups.manage_resources(life, life['group'])
	#groups.manage_known_groups(life, life['group'])
	#groups.manage_combat(life, life['group'])