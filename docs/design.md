Reactor 3: Design Document
=========

Section 1: Engine
---------

### Preface

Throughout the first phase of Reactor 3's development, a number of techinical
limitations were identified and addressed. These were undocumented and largely
added after the problems they corrected became too big to ignore. Of course,
this type of design is not really design, but instead more of a reaction to bad
design. While the problem of Python's performance has always been an issue,
there have been a few recently developments that have shown the language
beginning to crack.

The idea of this document is to address a number of concerns I have with both
the game and the technology backing it; Reactor 3 suffers from a lack of
uniform structure, and the engine is breaking under the pressure of similar
mistakes, both of which I feel can be fixed.

With the engine still mutable and open to change, now is the time to take action
and do a bit of corrective surgery on what could potentially be a very good
piece of tech. To help make the difference between the game side of Reactor 3
and its engine, an official name will be attached to it: Terraform.

### Addressing Big Data

Reactor 3's world size is currently set to 250x450, meaning 112500 tiles are
being processed at any given time on the main z-level. They do not pose that big
of a threat performance-wise since they are static - however, during December of
2012 I decided to create the "chunk map", which divides the map into 5x5 groups
of tiles on the X and Y axis. Each of these chunks provides a number of useful
traits about the tiles it contains, including the highest Z-level and building
information. Reference maps are an extension of the chunk map, representing
links of similarly-typed chunks for use in ALife. Later, the "zone map" was
added, which helps find sections of the map disconnected from other sections,
useful for pathfinding. All of these work in conjunction to improve performance
and the speed of development.

The world's size was a non-issue early in development; without a large amount of
data to parse, it appeared that most code was ready to scale as needed. This did
not hold true as the game grew and the world was populated with a larger amount
of information. At this point in time, the aforementioned 250x450 world causes
significant issues on hardware that should not have any issues to begin with.

To find potential problem areas, the following tests were conducted:

Active ALife: 0
Items: Parsing
FPS: 100+

Active ALife: 3
Items: Parsing
FPS: 40-45 (Groups settling)
	 80~   (Groups settled)

Active ALife: 3
Items: Skipping
FPS: 40-45 (Groups settling)
	 80~   (Groups settled)

### How I Addressed Big Data (for Now)

After the last tests were ran, a deeper profile of the game's code was
conducted:

	* Large amount of rays were being cast every frame to determine LOS.
	* The FOV algorithm was checking tiles multiple times in some areas.
	* Drops in performance were related to large amounts of items spawning LOS
		rays each frame.

Alternatives to the FOV code I had were explored, and I discovered recursive
shadowcasting, which ensures that no one tile is checked more than once. After
implementing it, I discovered I could then use the results from the FOV call to
determine LOS, eliminating the bulk of LOS calls.

Improvements can still be made. Any bit of LOS-related code can be replaced
with `alife.sight.is_in_fov` just so long as it is not walking the ray being
cast.

Section 2: Principal Design
---------

### Initial Thoughts

Reactor 3 can be summed up as the simulation of survival in a hostile world,
similar to that of S.T.A.L.K.E.R. and Fallout, but with a slightly more grounded
and open-ended approach.

The result of the various tests I've conducted is that strictly Player vs NPC
gameplay is uninteresting. While entertaining at times, the interaction with
NPCs in the early game ruins the impression that the world is a barren
wasteland. This is fine - in S.T.A.L.K.E.R. you are immediately dropped into a
living world, but that is not the impression I'm able to convey. An alternative
way to introduce the player to the world must be found.

A goal for the player must also be set in order to force exploration and
discovery. Without one, the player is left lost and confused, and is more likely
to become confused and unwilling to push forward.

Currently the player is spawned near a road leading to a town, or in the town
itself, with a working weapon. I am happy with the spawn point, but not the
equipment given. If a character creator is implemented, it needs to cover the
starting set of items. Otherwise, I am proposing that the player spawn with a
weak pistol and a few rounds.

I am interested in the following solutions to the lack of a goal:

#### Imminent Threat

The player is given a message upon entering the world that warns of an upcoming
world event that could lead to their demise. There are a few scenarios, but the
following seems the most promising:

	* Military invasion: North of the first town are the military bases. They
		are occupied by soliders who occasionally need more supplies to carry
		out operations. Supplies are delivered on foot by soldiers from outside
		the world, who travel through the town. Non-military personnel are
		shot on sight. With their superior firepower and larger numbers, the
		town is deemed highly dangerous. Once resupplied, the military patrols
		the town. Those using the town as shelter are forced to fight or make
		the dangerous trip north, where mutants and more dangerous threats
		await.

### The Dead World

The world that Reactor 3 takes place in is generic and unappealing. A game that
wants to have survival elements must first create situations that pose a threat
to the player. However, I am unsure of how to properly convey these situations.
Aesthetics might play a very important role in convincing the player that the
threat is real, but I am assuming it is one of the later steps in this process.

#### Telling the Player

Currently the player is not given any information on the status of the world
except the time of day. There are many more elements that the player should be
aware of. Work is halted on this until the player's stats are defined.

### The Structure of Life

Right now we tracking a very basic set of variables. One of the most important
aspects of a survival game is introducing elements that must be managed by the
player, which we see right now in the hunger/thirst mechanic. However, this is
really something that can get out of hand if not planned correctly, and can be
too real to the point that the player feels annoyed for frustrated.

Some of these elements are influenced by the world (and will be marked as such)

	* General health: The combination of each limbs' status.

The proposed set of variables

### The Behavior of Life

Terraform features an extensive set of AI-related functions. Over the past year
they have been painstakingly written and rewritten to work in conjunction with
the various flaws described in "Addressing Big Data." One of the shortcuts taken
to improve the current state-based implementation was to limit the amount of
times ALife reconsider their current state. This solution exposes the following
issues:

	* Reaction times are slow if the ALife's think rate is too high.
	* Lower think rates cause idle ALife to reconsider all possible states more
		often than needed. Not doing so means ALife take more time to become
		active again.

A better system, I've found, is to change the entity's think rate based on
their distance from the player. This puts the ALife on relatively equal footing
while saving CPU time.

### The (Finite State) Machine

The current implementation of ALife used a finite state machine, where roughly
15-20 states are evaluated at any given time. This way of handling their logic
is extremely easy to work with, until large amounts of complexity come into
play, after which the system begins to crumble under the load.

A "planning" phase was tossed around, in which the ALife would plan which states
they'd enter in the next X ticks, after which their think rate would be lowered
until coming into contact with the player or another enemy.

After some research, GOAP (Goal-Oriented Action Planning) was brought to my
attention. In GOAP, there are three core ideas:

* The Goal: A condition (or set of conditions) the AI desires. For example,
	"Kill Target" or "Eat"
* Actions: AKA states, like "Reload," "Shoot," or "Walk." Each Action must
	satisfy their preconditions in order to execute. These can take a specified
	or infinite amount of time.
* The Plan: A series of Actions that satisfy the Goal.

With GOAP, a large amount of the work needed to get a state working now can be
eliminated. To do this, the existing ALife states must be translated to either
Actions or Goals.

#### Moving to GOAP

    `alife_combat` -> `action_ranged` and `action_melee`
    `alife_cover` -> `goal_cover`
    `alife_discover` -> `goal_discover`
    `alife_explore` -> RM
    `alife_follow` -> `goal_follow`
    `alife_guard` -> `goal_guard`
    `alife_hidden` -> MERGE INTO `goal_cover`
    `alife_hide` -> MERGE INTO `goal_cover`
    `alife_needs` -> `goal_needs` -> `action_eat`, `action_sleep` etc
    `alife_search` -> `goal_search`
    `alife_shelter` -> `goal_shelter`
    `alife_talk` -> `goal_talk`, `action_talk`


Task: Discovering
Tier: RELAXED
Desire: has_non_relaxed_goal
Action Set:
	wander (inf.)
		Cond: Nothing.

Task: Looting
Tier: RELAXED
Desire: has_item_group
Action Set:
	wander (inf.)
		Cond: None
	pick_up_item (>=1)
		Cond: Sees item

Task: Find Shelter
Tier: RELAXED
Desire: has_shelter
Action Set:
	claim_shelter (1)
		Cond: Sees shelter

### Issues with Current Implementation

Currently, only the cost of the action that directly solves the goal desire is
taken into account. In the future, A* or another seach algo. should be used.
