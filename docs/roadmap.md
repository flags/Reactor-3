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
[x] Structure of Tiles
[x] Structure of Maps

Structure of Tiles
------------------
Items and Tiles will be using dictionaries. To lower data cost, Tiles will specifically
have two parts: static and dynamic. Static parts will be referenced and not stored
locally to that Tile, and will contain things such as movement cost and icon.
The dynamic portion covers changing values, like items contained at that position
or the depth of water.

Structure of Maps
-----------------
Maps will be in the format of [x][y][z], the last of which will hold the array of Tiles
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
functions without the filename prepended (graphics.init_libtcod() vs.
init_libtcod()).

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

