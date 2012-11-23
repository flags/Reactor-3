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

Clothes can also hold items themselves, so that also needs to be covered to some extent.
