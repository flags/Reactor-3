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

Structure
---------
Items and Tiles will be using dictionaries. To lower data cost, Tiles will specifically
have two parts: static and dynamic. Static parts will be referenced and not stored
locally to that tile, and will contain things such as movement cost and icon.
The dynamic portion covers changing values, like items contained at that position
or the depth of water.


