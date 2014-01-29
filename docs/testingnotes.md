Tracking duplicate weapons is difficult
Wounds don't disappear from medical menu
Item access times should be higher for retrieving items from containers that are full
	obviously number of items doesn't matter if the container only holds 4 or 5 of them
	Large cotainers (10+ items)
de/highlight_position() to get rid of complete screen refresh
The visible targets list appears to grow larger (pushes debug text down) but shows no names
	Might be dead agents
Outposts are too close to player spawn.
Limit on number of duplicate cell types in certain radius
Need multiple zone entry points
Crash on equipping storage item from storage
Some military NPCs aren't reloading

Alife wants group at night

Put more space between buildings (maybe on a per-type basis.
	Space for stores (parking lot, etc)
	Space for houses (small yard, fenced-in backyard

Message box colors?
Sort inventory (or equip menu) by category?

Worldgen: item spawns
Having buildings generated on the side of the roads?
	If we have to seed this, judge based on the location of the lighest color of the road tiles (BROKEN_*)

Global radio messages
	PDA (press tab?)

Factor weather into visiblity

"Scan" mode. Over a number of ticks, a heatmap is generated of the
	best places to hide in the surrounding area

When weapons are dropped, the magazines inside the guns are not disowned.

healed_by memory to boost leadership?
	then "Thanks!"
	Changes in relationships after memories
		Would make combat affect ALife behavior more
		
When rendering items, render the most important one on top (gun -> health kit -> ammo)
		
AI: What should I do?



Content:
	Lock weapon crates: Use small explosives to open them, etc
		It's a "task" to open them. Gives the player something to do



Do not clear orders until group leader allows it
	i.e., when the AI hits a guard point it should not be cleared (they should wait there)
