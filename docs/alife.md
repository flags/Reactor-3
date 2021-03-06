ALife - Version 2
=================

# What is "ALife"?
"Artificial Life", in technical terms, is artificial intelligence with a focus on emulating actions
similar to those a player would make. Its goal is to make the single player experience more stimulating
by creating companions or opponents that behave as humans would.

# The Laws of ALife
ALife is defined by the following specifications:

* Random does not mean intelligent. Given that all facts about a situation are known, the action taken should be predictable.

# Realizing Limitations
The catch is that true "ALife" is not possible due to the need of heavy processing power and optimization
that would end up being too situation-specific. The real

Part 1: Thinking and Understanding
----------------------------------
An ALife should be able to look at its surroundings and determine its interest in all visible "targets."
The word "targets" represents all ALifes and Items in the ALife's LOS. Upon being spotted for the first
time, a snapshot of the target is created and logged into the ALife's memory. This snapshot contains the
target's outward appearance, including any defining traits (injury, equipped weapon, etc) for later
identification.

Once a snapshot has been created, the ALife can start remembering events this target performs. Take note
that these should not be trivial things such as movement, but instead memorable events like engaging in
combat.

These memories play an important roll in the observing ALife's behavior.

Part 1.2: Judging
-----------------
**But first, a note**: It should be noted that this step is where optimization comes into play. Remember that
most functions relating to ALife are performed many times a second- the less we have to do in that second
the better.

When an event is observed, it is first "judged", resulting in a score ranging from negative infinity to
positive infinity. This score is then added to the ALife's impression of the target and the event is
filed away. The value is never recalculated.

Consider the following: The impression an ALife has of another ALife determines what action is taken by
the observing ALife, so heavy calculations are justified by only being executed once.

**Note**:
Distance (or any variable that changes on a turn-by-turn basis) does not play a part in judgement.

# Every Turn
A rundown of the ALife's condition is performed, but only in situations where it is required.

	snapshot = {'condition': 0,
		'appearance': 0,
		'visible_items': []}
	
	for limb in body
		snapshot['condition'] += get_condition(limb)
		
		for item in limb:
			snapshot['appearance'] += get_quality(item)
			snapshot['visible_items].append(item['name'])
	
	update_snapshot(life,target['id'],snapshot)

Part 2: Pathfinding
-------------------
Regardless of how complicated the rest of the ALife becomes, pathfinding will almost always be the biggest
bottleneck. This is due to the way most algorithms react when handed a larger map to parse, and since the
level size for most Reactor 3 maps will be much, much larger than 1000x1000, certain precautions must taken.

Consider the following needs for different pathing types:

* The most intense pathfinding will done in combat when using cover mechanics or fleeing from an opponent
* An algorithm must take path costs similar to the dijkstra approach (which does not work due to map size)
* When the ALife is not in combat, straight lines can be used to path

Algorithm 1: Weighted A*

