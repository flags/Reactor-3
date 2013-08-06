from globals import *
import life as lfe

import alife
import raids

TIER = TIER_PASSIVE

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	return RETURN_SKIP

def add_raid_targets(life):
	for raider in [LIFE[r] for r in raids.get_raiders(life['camp'])]:
		if raider['id'] == life['id']:
			continue
		
		if not alife.brain.knows_alife(life, raider):
			alife.brain.meet_alife(life, raider)

		if not lfe.get_memory(life, matches={'text': 'target_is_raiding', 'target': raider['id'], 'camp': life['camp']}):
			lfe.memory(life,
			           'target_is_raiding',
			           target=raider['id'],
			           camp=life['camp'],
			           danger=2,
			           trust=-10)


def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	if life['camp']:
		if raids.camp_has_raid(life['camp']):
			add_raid_targets(life)