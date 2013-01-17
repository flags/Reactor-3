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
that these should be be trivial things such as movement, but instead memorable events like engaging in
combat.

These memories play an important roll in the observing ALife's behavior.

Part 1.2: Judging
-----------------
*But first, a note:* It should be noted that this step is where optimization comes into play. Remember that
most functions relating to ALife are performed many times a second- the less we have to do in that second
the better.

When an event is observed, it is first "judged", resulting in a score ranging from negative infinity to
positive infinity. This score is then added to the ALife's impression of the target and the event is
filed away. The value is never recalculated.

Consider the following: The impression an ALife has of another ALife determines what action is taken by
the observing ALife, so heavy calculations are justified by only being executed once.

# First Appearance
Distance (or any variable that changes on a turn-by-turn basis) does not play a part in judgement.

First, the outward appearence is recorded. This is done by scanning all visible items and their quality:

	appearance = 0
	
	for limb in body:
		for item in limb:
			appearance += get_quality(item)

# Every turn
A rundown of the ALife's condition is performed, but only in situations where it is required.

	condition += 1
	
	for limb in body
		condition += get_condition(limb)
