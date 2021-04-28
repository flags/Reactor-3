from globals import *

import life as lfe

from . import judgement
from . import survival
from . import chunks
from . import sight
from . import brain
import smp

import logging

def tick(life):
	if not lfe.execute_raw(life, 'discover', 'discover_type'):
		_lost_method = lfe.execute_raw(life, 'discover', 'when_lost')
		if _lost_method:
			if not life['path'] or not brain.retrieve_from_memory(life, 'discovery_lock'):
				if not 'scanned_chunks' in life['state_flags']:
					life['state_flags']['scanned_chunks'] = []

				sight.scan_surroundings(life, _chunks=brain.get_flag(life, 'visible_chunks'), ignore_chunks=life['state_flags']['scanned_chunks'])
				
				_explore_chunk = chunks.find_best_chunk(life, ignore_starting=True, ignore_time=True, lost_method=_lost_method, only_recent=True)
				brain.store_in_memory(life, 'discovery_lock', True)
				brain.store_in_memory(life, 'explore_chunk', _explore_chunk)
				
				if not _explore_chunk:
					brain.flag(life, 'lost')
					return False
				
				survival.explore_known_chunks(life)
		else:
			return False
