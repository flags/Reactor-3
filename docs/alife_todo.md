KEY:

(blank)	:	Incomplete
x		:	Complete
/		:	Partially complete
?		:	Potentially a non-issue
U		:	Unclear (for entries written too early in the morning)

alife_camp.py
	[ ] Do we even want to help other ALife find the founder?
	[x] Watch over camp

alife_talk.py
	[ ] Score _potential_talking_targets
	
damage.py
	[ ] Fix language output
	[ ] Blunt weapons
	[ ] Explosives
	[ ] Melee (?)
	
judgement.py
	[x] Placeholder: ALife now view someone positively just by saying hello to them (no response needed)
	[x] Finish `alife.brain.can_trust`

Conversations:
	[/] Nothing is conveyed to the ALife/Player. Needs: trust, friendly/hostile actions
	[x] When letting the player answer, only pick one response to show from multiple ones of the same gist.
	[ ] When told about a location, add to map
	[x] Could ALife use new conversation system to talk?
			How would the whole "find founder" situation be done in the new system? Just through topics?
	[x] Spotting lies (lying about being the camp founder, giving wrong info, etc)
	[ ] Dialogs are still controlled by one entity. Check to make sure the other involved entity is even awake/existing in dialog.tick()
	[?] Multiple ALife hearing a response. Only general topics, like introductions, etc.
		Accomplished by sounds
	[ ] Red text on responses indicating lying is no longer working

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
	[x] Founder should give out jobs (patrol, etc)
	[ ] Founder can hire people to work under him
	[/] Claim to be Founder
		Done for player
	[ ] `has_camp()` or `get_preferred_camp()`
	[ ] Proper `get_camp_founder` function for determining who the founder is believed to be

Jobs:
	[ ] Consider moving logic (like finding targets, etc) to own file
	[ ] Jobs ("quests") dialog
	[ ] "Repeat" flag so ALife can switch between tasks in a job without deleting them

Combat:
	[ ] Add `can_engage` function
	[ ] ALife fight for food/will attack others for food if starving
			Could randomize hunger on zone entry to create friction at worldgen

Judgement:
	[/] Remove all references to `judgement.judge`, `score` or any other variation
		[/] Replace with calls to get_fondness(), is_target_dangerous(), and can_trust().
	[x] Rewrite `brain.understand()` to support new scoring variables
	[x] ENTRY_SCORE for all ALife modules are now invalid
	[x] When calculating anything, we can just do a memory search for `danger` and `fondness`
		Differentiate between first-hand and second-hand. Let trust play a factor.
	[x] `Start conflict` doesn't add to danger, so no conflict is started
	[U] Identifying targets via memories. Not knowing people until you had enough info on them

Misc:
	[ ] ID vs. dictionary reference mismatch in function arguments
	[?] When choosing to not answer a question, chances are that person will never ask you again.
		Fixed?
	[x] Items need `is_being_picked_up`
	[U] `set_hunger_to_percentage` (also for thirst)
	[ ] General dictionary match function
	[x] Have `aim_at` refer to ID instead of raw entity
	[x] Fix crash on menu left/right
	[ ] `alife_collect_items.py` refers to item scores (line 34), which are outdated
	[x] Calls to `numbers.distance()` still use default for `old` keyword (True)
		In doing this, diagonal movement costs 2
	[ ] In the target list show `Dead (<cause of death>)` instead of `Dead (Indentified)`
	[ ] Mod docs

Optimization:
	[x] `WORLD_INFO['pause_ticks'] = 2` in logic.py can be decreased to 1 or 0 to speed up combat phase
		Can we base this off average FPS?

Pathing:
	[ ] Account for Z-levels
	[ ] Chunks need to have a listing of what Z-levels they contain for the chunk pathing

Survival:
	[x] A system for creating needs and tracking them. Similar to questions so we can easily find what meets a need.
		[ ] Can we get rid of the old needs that use flags?

Worldgen:
	[/] Randomize hunger/thirst on entry
	[ ] Spawn ALife in various locations around the outside of the map

Combat:
	[x] `calculate_safety()` in all ALife modules needs to refer to an outside function.
		`targets_not_seen` is not taken into account. Some targets might still be relevant
		Consider that `alife_combat` stores identified targets into memory as `combat_targets`
			We are never truly safe until this is cleared.
	[ ] When leaving cover, do we know the interval of the targets gunshots?

Complexity:
	[ ] `judgement.can_trust` minimum value for when function returns true

Cycles:
	[/] Food:
			Has food?
				[x] eat it
			else:
				remember food location OR can see food
					[x] gather it
				else:
					[ ] search for food
