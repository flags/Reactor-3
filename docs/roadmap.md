Reactor 3 - Roadmap
===================

This is the roadmap for Reactor 3. Rules are as follows:

	* Each milestone must focus on a similar technical aspect (maps, AI, etc)
	* Only features from the current milestone can be completed
	* If a feature has to be bumped up a milestone, it instantly becomes top priority

Milestone 1 - Data
==================

Goal
----
To find a way to properly store and retrieve data without falling back on complicated
solutions most likely using OOP. Data should be easy to manipulate and remove, along
with being easy to store to disk.

Tasks
-----
{x} Structure of Tiles
{x} Structure of Maps

Structure of Tiles
------------------
Items and Tiles will be using dictionaries. To lower data cost, Tiles will specifically
have two parts: static and dynamic. Static parts will be referenced and not stored
locally to that Tile, and will contain things such as movement cost and icon.
The dynamic portion covers changing values, like items contained at that position
or the depth of water.

Structure of Maps
-----------------
Maps will be in the format of {x}{y}{z}, the last of which will hold the array of Tiles
for a position's Z-levels. There is no need to treat this data any differently than
a container for Tiles, so maps can easily be dumped to the disk using `JSON.dumps()`

Milestone 2-1 - Structure and Layout
==================================

Goal
----
To organize the general structure of the engine's core features - meaning that each
piece of the engine has its own file and are all properly named. In addition, basic
functions like libtcod setup and input handling should be created in a general class.

Milestone 2-2 - Core Functions
============================

Goal
----
Create and establish the inner-workings of the engine, like tile drawing and other
helper functions to make development easier. Functions should be readable outside
the context of their respective files if the programmer should choose to use the
functions without the filename prepended.

Get all the complicated systems in place first, like fast drawing and lighting.
These have been an issue in the past, so it's better to get them working optimally
now rather than later.

Milestone 2-3 - Terraform Development - Part 1
==============================================

Goal
----
Establish the basics for the level editor, Terraform. Since mouse input is currently
inoperable just hang on to keyboard input. Tiles should be selectable, placeable, and
removable. Selecting tiles should just be assigned to a set of keys until the mouse
issues are worked out.

Milestone 3-1 - The Beginning of Life - Part 1
==============================================

Goal
----
Life is an extremely complicated mess of variables all interacting at once. Sometimes
creating life is the hardest part, as dictionaries need to be connected to other
dictionaries, all while being somewhat easy to access and modify.

Structure
---------
						   head
						   neck
				lshoulder	 	rshoulder
			upperleftarm	     	upperrightarm
				lelbow	  chest		relbow
			lforearm				  rforearm
			lhand		   hip			 rhand
						  groin
					lthigh		rthigh
					lknee		 rknee
				llowerleg		 rlowerleg
				lfoot				 rfoot

Milestone 3-2 - The Material Things - Part 2
==============================================

Goal
----
Like in any game, items are extremely important and often introduce a lot of new,
interesting features. Regardless of what the item is (be it a weapon, food, or clothing,)
it's important to make them just as easy to modify as any other object in the game.

Right now every character is in the nude! We'll remedy that by creating clothes, which
despite sounding very simple, are actually one of the more complex objects we'll be adding.
This is because clothes aren't just attached to one part of the body, are are technically
attached to the arms, legs, whatever...

Clothes can also hold items themselves, so that also needs to be covered.

Example
-------

    jacket = add_item(player,'jacket')
    equip_item(player,jacket)

    #This function is then called...
    def equip_item(player,item):
        #TODO: Faster way to check this with sets
        for limb in item['attaches_to']:

Post-Mortem
----------
Milestone 3 was completed without much regard to this document. Fortunately, the issue
tracker was cleared without much trouble, although there were definitely a few problems
along the way that pushed back the completion date slightly.

As we move into Milestone 4, it's time to take into hard consideration how the core gameplay
mechanics will be conveyed to the user. This involves building the character's relationship
with items scattered throughout the world.

Milestone 4-1 - Interaction
=========================
Items currently have no individual behaviors, sans sneakers which provide the user with
increased speed. This is a good sign that player <-> item interactions are possible with
the current method of storing item data, and provides a ground for adding in more possibilities.

Stepping back, items need to exist in two contexts: The world and the player. In each, the item
should behave according to its in-game description, which should reflect the various effects it
has stored.

Items should also be able to interact with each other, maybe to combine and eventually form
a different item. The reverse should also be possible in some cases (tearing apart a shirt to
make bandages.)

A good example of this kind of interaction is between bullets and guns. Loading a gun is a 3-step
process that involves getting ammo, loading the bullets into the magazine, then inserting the
magazine into the gun. While some may argue that this is complexity for the sake of complexity,
I will point out that this type of process (loading your own gun) adds to the survival aspect
of the game, and also builds a deeper relationship with the player and the weapons he or she
chooses. It also encourages strict inventory management as a sort of metagame where the most
organized person succeeds, while the messy search through backpacks for the appropriate item.

This leads to inventory management: Items can be stored in several areas on the body. At first,
the player has a small backpack able to hold a handful of items, but can also store smaller items
in their pockets. In the above case, it would make more sense to stick a magazine in your pocket
rather than a backpack, which would require taking off in order to remove the item. Once again,
this adds to the inventory metagame discussed previously and puts the player in a position
to set themselves up for success or failure, depending on how accessible the item they require
is.

Example
------
A pistol may be holstered to someone's hip, allowing them easy access to it in dangerous
situations. Should the player predict a potentially deadly encounter from a distance, they have
the opportunity to shuffle their items as needed; holster the pistol, remove an SMG from their
backpack, and engage. Some weapons could also be outfitted with a strap, allowing them to simply
be swung around once the pistol is holstered.

Milestone 5-2 - ALife Revision 2
================================
The previous system for handling ALife functionalities like understanding and performing actions as a result will be replaced with the second iteration of ALife.
These changes will enforce a standard for all possible decisions, encouraging a common structure for current and future additions:

	brain-escape.py
		input:
			alife_seen
			alife_notseen
			targets

		qualifications (conditions):
			initial_state = 'vulnerable' #Previous needed ALife state
			attack <= 30%
			defense <= 30%

		actions:
			escape for targets
			state = 'panic' #State the ALife is now given

*Note*: These don't have to be required (like initial-state)

*Note*: Attack and defense are misleading (safety as just one variable)

Notice how this format puts a strict guideline on what variables are used and defined.
Previous implementations avoided this and as a result ended up with a variety of one-off terms and garbage variables.
This new structure defines when an action goes into effect and what conditions keep it active.
They are intended to work in certain cases and only be triggered when all conditions are met (in a descending order.)
Simply put, each condition is checked starting from the top, and if the ALife meets this then the function crawls down the list. If everything checks out OK then the function is run.

Milestone 5-3 - Traversing the Map
==================================
This sub-goal establishes the methods used by ALife to traverse the map in the most efficient way possible. Since pathfinding is a relatively intense operation, abstracted map data (chunks and reference maps) will be used instead of interpreting raw data.

Discovering the Map
-------------------
Currently, the biggest flaw in the ALife is its inability to discover the map by itself. As a general test, I've instructed the ALife to automatically go to and (roughly) path along the nearest road, but this isn't intended to be final in any sense.
For the sake of documentation, the offending fuction is `alife.survival.explore_unknown_chunks()`. The majority of the changes needed will be done in this file along with any files containing chunk functions.
We must also consider how often the ALife will be performing these tasks. With any luck, we should be able to have the ALife run any of these pathfinding operations once every 30 seconds or so, as the other ALife module for exploring interesting chunks will run automatically if needed then resume the discovery process when finished.

Since we are dealing with abstracted data, the amount of information to parse is much smaller than normal:

    Amount of tiles to parse in raw form: 22500
    Amount of tiles to parse in abstracted form: 900

This should give us access to just about every form of pathfinding that previous had to be avoided due to the sheer size of the current map. Granted, we'll still be using A* to find the actual paths, but these new functions will give us a vague idea of where the A* needs to be pointed at.

Finding a Place to Be Safe
------------------------
Next comes the issue of finding a proper place for the ALife to camp. This subgoal involves finding an appropriate way to score chunks with an appropriate safety score. Calculating this score should factor in the any friendly ALife occupying that area in addition to any other factors that ensure the chunk(s) provide adequate protection.

Requirements:
	* Easily fortified
	* Either remote or in a central location
		* When scoring for remote chunks we can check the distance to the nearest buidling

New Conversations
----------------
We need to track the following for all ALife:

	* Their thoughts on other ALife
	* Any current or previous conversations
		* The state of any current conversations
	* Any interrupts that should occur and how to judge what conversations are more important
	* Overhearing conversations and how to handle second-hand information.

Also implement a proper matching system so a message can be broadcasted to more than one ALife based on certain criteria (faction, location, etc.)
This system will be used for all conversations.

The structure for messages will be as follows:

	Match: Series of requirements an ALife must have to be considered the target of a conversation.
	Gist: Same as in the first revision: A summary of the message.

ALife will maintain the following arrays in their `know` dictionary:

	* Asked: Things we asked the ALife
	* Answered: Responses given to the ALife

ALife will store the following in their memory:

	* The end result of any notable conversation event:
		* First met
		* Initial impression
		* Who told them certain information

In addition, we can pass along memories directly through conversation.

Thoughts:
So we can create one entity (result  of `create_conversation`) and  pass it around to all ALife involved or go about it the old way, where each ALife has a view of the converation and that's it. Obviously there are several advantages to each one, with passing around the same entity getting into some messy memory access stuff possibly ending in a fractured packet of info being sent around... the best method after thinking about that would be having a unique view for each person and hoping that the ALife can ensure everyone involved in the conversation is on the same page.

We must also consider that if someone says "Hello!" to a group of people not everyone responds. Usually if one person responds the rest of the group is considered to have had that same response also.

Timing: Some questions need to be asked more than once, like requesting chunk info. There should be a delay or a way for topics to decay and leave the list eventually. This can *probably* be done in `alife.talk`, but there will need to be definite changes in `sound.listen()` for handling this behavior.

Milestone 6 - Growing Content
=============================

Goal
----
With all the systems in place, we must now generate content to build up the game's depth. The UI will also be reworked and extended to give the player a better understanding of the world. We'll also start creating personalities for ALife and extending their logic.

Roadmap
-------
When the player enters the world there should be some kind of conflict between the starter camp and the bandits. We want there to be some kind of established "safe zone" so the player feels like they have to be somewhat careful about where they are going.

Take note that the player won't be aligned to a faction unless:

1) They are wearing a faction-specific item
2) There are known to be in that faction

Both things will be false for new players regardless of how the first job goes. However, it should be noted that Bandits are automatically aligned against non-bandits, so you will encounter combat if you run into them anyway.

The following should be playable:

	The player spawns in the northwest and is instructed to follow the road until they see the nearest camp. The player should then be able to enter the camp, find out who the operator is, and get assigned their first job: Get the documents off the body of a deceased soldier.
	
	Upon arrival it is apparent that the target is not dead, but just has a bad leg injury preventing them from running. You will encounter this person and go through a dialog determining whether you are on good terms or not. If not, you will enter combat.
	
	After resolving the conflict you will take the documents back to camp. You will then be told to talk to those hanging around the camp to find what to do next, but the decision is ultimately up to you whether or not you actually do that.

Problem 1: The UI
----------------
We'll attempt to give the player a better understanding of the world and the people inhabiting it with these changes.

Acknowledging the following issues:
	* The player's lack of situational awareness
		* Information not CLEARLY displayed on the map needs to be re-represented on the right
			* EX: Target name - (Status)

Problem 2: The Combat
---------------------
The damage model makes no sense in a lot of applications. While damage is handled, the appropriate reaction is not, so the ALife is only affected in the long-lasting negative effects and not the reaction (stumbling, twirling, etc)

Problem 3: Group Tasks
----------------------
Like deciding how to flank a target, etc. Engage them.

Problem 4: Misc Stuff
---------------------
Message boxes on map screen for conversations.

New(er) Conversations
-------------------
Conversations have been revamped and the old system has been axed (for the most part.) While there are still bits and pieces of it scattered about, I don't think there is a use for it anymore. As a result, all the features of the old system need to be ported to the new one.

However, I am still unsure if these features can be recreated properly in the new code. The only real advantage of the old structure was that there wasn't any real structure at all- just a way for ALife to "hear" things and react accordingly. I'm hoping that what I have now can emulate that, because otherwise a lot of code is now obsolete (for the greater good.) To test, I've written the proper dialog for learning about camps and asking camp-related questions. This is still in its infancy, but it's interesting to see that it works rather well, so I'm inclined to believe that the old code should work too.

To explain, this new system is very centralized, so about 90% of all dialog-related code is contained in a single file. I guess that isn't much different than the previous code, but I think the big difference here is that the back-and-forth nature of certain conversations is a lot more organized and open to expansion than before. I really did feel like getting ALife to talk before was probably my least favorite thing to do, but if I am able to apply this to ALife vs. ALife situations instead of just Player vs. ALife, I think I might be on to something.

Another advantage is that I'll no longer need to write separate dialog menus for the player since this code generates these for us. I made a somewhat risky decision and wrote a new, less-complicated menu structure to use instead. There isn't anything wrong with the menus I use across the rest of the game, but I wanted to do some very specific things and knew I would just be bloating up a working system if decided to extend existing code to satisfy one case.

Questions
---------
Now there is a need for ALife to ask about certain topics. This could be done in one fell swoop when beginning dialog, but we specifically want the ALife to know they have questions to ask beforehand so they can pursue dialogs by themselves.

Example case: An ALife joins a camp but is unaware of who the founder is. After running out of people to ask, the ALife simply idles in the camp until someone can help them (during this time they are always broadcasting the request for founder info.) I won't say it's easier, but I'd like to get this behavior into the dialog tree instead, giving me an opportunity to implement dialogs started with the player by the ALife.

I think the main idea here is just attaching the ALife to the dialog tree and hoping they are able to figure it out. After all, it should solve the issue of having multiple conversations active (but not running) at once, in addition to giving me some amount of context to deal with instead of just having a random phrase in an array I have to parse to find its origin (and even then I can't be sure what the context is.)

Lies
----
In an effort to move the ALife's intelligence into the next level of complexity, it's time to start processing memories to find out what makes sense and what doesn't.

The obvious first thing to check will be looking at camp founders. The immediate issue is the fact that the ALife does nothing but reference the camp founder when doing some tasks; how could we possible interject this information into a phrase to get a response out of someone? In the case of the camp founder, should we just out-right ask everyone who the founder is?

I guess the real question is how to make the ALife discover lies without forcing it on them during dialog; i.e., it should occur naturally and through the `memory.detect_lies()` routine.

First order of business will be having the ALife walk around and get to know everyone.

Routines
---------
Each ALife has a selection of wants and needs. Needs include eating, sleeping, and general survival gear. Wants include non-essential items like radios (almost a need, but not quite) and high-end weapon attachments that aren't otherwise crucial.

Needs establish the base behavior for all ALife, while wants define their unique logic.

[x] Hunger
------
Operates on a simple timer that decreases each tick. Eating adds a variable amount to this timer. When this timer is half of its maximum a person is considered hungry. At a fourth they are starving.

Food can be found scattered about the Zone, usually in cans.

Thirst works on a similar timer but is a lot shorter, so you'll need to drink more frequently.

Squads Before Camps
------------------
Squads form when it is more convenient to fulfill these kinds of needs together, so ALife that need food might find themselves scavenging the same area, resulting in a confrontation that leads to a working relationship.

These groups will grow larger and larger as similar people are encountered while out adventuring.

Conflicts
----------
A difficult part of this is getting the ALife to disagree and begin conflicts. While it is easy to simulate what happens after a conflict starts, developing one that feels natural is many times harder. We simply cannot have "they're from a different squad" as a valid reason for starting fights. Whatever it is, it must be natural and make some amount of sense.

	* I would like to avoid "they're armed, so they must be dangerous."
		This isn't always true. After all, we'd have to ask them what their stance is, which involves coming up with a reason for being friendly or hostile.
			This is easy for the player to do because their reasoning is up to them.

Developing Friction
------------------
I want to avoid "good" and "bad" factions. I'll focus on camps right now since they will eventually develop into factions as relationships grow:

	Camps are most concerned with land ownership, i.e, they want to be in control of certain spots on the map.
		We will call these areas landmarks and they will have some kind of strategic importance or resource.
	
		Camps have certain needs. A need for weapons will result in a raid of an ammo depo.
	
[x] Advanced Life Flags
------------------
I'll start using flags in the race .XML to help better tweak how ALife behave. Examples include:
	
	CAN_COMMUNICATE: ALife can speak and understand what is trying to be conveyed
	HUNGER/THIRSTY: Has requirement for food/water
	CAN_GROUP: Ability to develop squads/work in groups
	
New Judgement and Combat Scoring
------------------------------
One of the oldest parts of the codebase is `judgement.py`. It is a relic from a previous time in development where scoring was looked at from a very different point of view. It was intended to be all-encompassing, but as the game grew it remained the same.

Currently, the actual `judge` function returns a numerical value that indicates how much an ALife likes a target. Any value at or above zero indicates that the target is neutral. Anything less than that is considered hostile.

New system ideas:

	1) Like/dislike scoring can stay since it appears to be working so far.
		However, it should *not* be the deciding factor in whether combat is started
	2) Trust needs to play a clearer role in judgement (it also needs to be defined)
		Adding it on to `like` is incorrect since trust does not represent how much someone likes another
	3) Scoring must change once a target is identified as hostile
		Furthermore, this must be mutual if either ALife has made its hostile intentions clear

Variables:
	Fondness (-inf, +inf)
		Definition: Decides how well someone is liked based on neutral actions.
		Based on: friendly/unfriendly memories (first and second-hand)
	
	Danger (0, +inf):
		Definition: Represents how much of a threat someone poses.
		Based on: visible weapons WITH hostile memories (first and second-hand) to prove it.
			(invalid otherwise)
	
	Trust (-inf, +inf):
		Definition: Value used to define how believable someone's word is
		Based on: Dialog.
		Affects:
			This value comes into play during `determine_truth`, a memory seach function that simply picks the most "trusted" memory from the list.

New Pathing
------------
Structure: dict
Keys:
	Start		...
	End			...
	path_type	['

Operation:
	First a "chunk path" is generated. The chunk map sees if it can path to the destination chunk.
		If it cannot, it gets as close as it can
	The ALife then follows that path chunk to chunk
	If we arrive at the end of the chunk path and can see the target, then stop.
	Otherwise use A* to find the destination.

Tech:
	The map is scanned and the following taken into account:
		1) Areas we can walk (can be unconnected.)
		2) Z-levels we can travel to
	
Combat Fix #1
--------------
First in a series of fixes.
All of the logic that decides when combat is entered needs to be scrapped.

Proposing: `is_safe()`
	This function checks a variety of ALife memories and values to determine if they are safe.
	It would replace the majority (all?) of the calls to individual calculate_safety() functions.
	In addition, we can have this run once at the start of the tick.

Proposing: `calculate_safety()`
	Runs before ALife modules.
	Inspects all variables checked by `is_safe()` for changes.
		For example, when `combat_targets` become invalid.

Combat Fix #2
--------------
We need a way to determine who our targets are. Proposing the following categories:

Visible: In the ALife's LOS.
Non-visible: Inverse of previous.
Visible threats: In the ALife's LOS. Possibly dangerous.
Non-visible threats: Not in the ALife's LOS. Possibly Dangerous.


Crafting
---------
Used for dismantling in this milestone.

State Overrides
---------------
Each ALife module has rules for modules it will not take over for (i.g., 'camping' will not take over for 'combat' if it is in effect.) While this works, each module has to explictly list what modules it will ignore. This provides the following disadvantages:

	1) Adding new modules involves finding what modules will not be overridden and listing them.
		In addition, we must also modify modules if the new module needs to be ignored by any of them
	2) Won't work from a modders point of view since it involves modifying code outside of the modders' scope
		(Mods are designed to work alongside the codebase- not over it.)

We now need a general structure to handle this.

Alternative 1: Priority Levels
	
	
