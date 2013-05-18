ALife cases:

	alife_camp.py
		[ ] Do we even want to help other ALife find the founder?
		[ ] Who do we think the founder is?
		[ ] Watch over camp
	
	alife_talk.py
		[ ] Score _potential_talking_targets
		
	damage.py
		[ ] Fix language output
		[ ] Blunt weapons
		[ ] Explosives
		[ ] Melee (?)
		
	judgement.py
		[ ] Placeholder: ALife now view someone positively just by saying hello to them (no response needed)
	
	Conversations:
		[/] Nothing is conveyed to the ALife/Player. Needs: trust, friendly/hostile actions
		[ ] When letting the player answer, only pick one response to show from multiple ones of the same gist.
		[ ] When told about a location, add to map
		[x] Could ALife use new conversation system to talk?
				How would the whole "find founder" situation be done in the new system? Just through topics?
		[ ] Spotting lies (lying about being the camp founder, giving wrong info, etc)
	
	Likes/Dislikes:
		[x] Each ALife will have a set of likes/dislikes based on gists. These are measured in a float from 0.0 to 1.0.
		[x] dialog.get_freshness_of_gist can be used to figure out if a topic is getting old or not
	
	Sight:
		[ ] Every tick: If target seen, update last_seen_at. If target not seen and last_seen_at is visible, mark as lost
		[ ] Proper `get_last_seen_at` function to cover situations where we've only heard about a target (and have never seen them)
	
	Factions
		[ ] Each camp has a set of alignments towards other camps. "Factions" are just multiple camps with the same views.
		[ ] Chunk ownership
	
	Camps:
		[ ] Founder should give out jobs (patrol, etc)
		[ ] Founder can hire people to work under him
		[ ] Claim to be Founder

	Jobs:
		[ ] Consider moving logic (like finding targets, etc) to own file
	
	Misc:
		[ ] ID vs. dictionary reference mismatch