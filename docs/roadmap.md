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
Next comes the issue of finding a proper place for the ALife to camp.
