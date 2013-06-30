![Reactor3](https://raw.github.com/flags/Reactor-3/master/art/pngs/minilogo.png)
# Reactor 3
-----------
Reactor 3 is an action roguelike in the same vein as IVAN - A Violent Road to Death and S.T.A.L.K.E.R.: Shadow of Chernobyl.

If You're Reading This...
-------------------------
My name is Luke Martin, and I am the creator of Reactor 3.

This game has been in the works for roughly 9 or 10 months, but I chose to keep the repo private until I had at least something to show. The bad news is that there isn't much in the way of content yet (intentionally.) As I've said in the past, I wouldn't build content around a game that wasn't ready for it. I knew from the start that I would want to be able to make changes without fearing a breakage elsewhere, and having very little content has enabled that.

In addition, I am enamored with the idea of a game that generates its own stories and its own content, and much like other games in the genre, I feel like I can accomplish something similar, but it will take time and dedication before I might ever see the payoff from it.

I would wager that a large amount of the people reading this only have a passing interest with the game in its current state. That's entirely fine and I don't expect any of you to play the game at all - after all, a lot of the people I've sent this out to were involved in a game development group I was a part of, and I suppose you lot would just like to see (or hear) about the various inner-workings of this little project that have changed since you've last seen it. With that said...

Features
--------

# ALife
* Dialog with ALife is now possible
* ALife maintain a list of needs
	They will ask you and other ALife for food/drinks if none are around.
	ALife will invite you to join squads (this is mostly untested)
* ALife will explore the map somewhat intelligently (following roads, checking buildings, etc)
* ALife understand the concepts of: Trust, Danger, Willpower, Extroversion/Introversion, Leadership/influence/Charisma, Believing one person over another
	
	...in addition to several functions which involve combining the above to achieve more complex results
* ALife are capable of forming groups
* Groups have and understand leaders, in addition to succession when the leader is lost
* ALife understand the world without needing specially designed levels (they react dynamically.)

# General
* Terraform - Level editor.
* ReactorWatch - Web-based debugger.
* Fully working "realistic" inventory system
	You must wear a backpack/other clothing item in order to carry more than two items.
		Pants have pockets, for example
* Weapons must be loaded as they would normally
	Obtain ammo -> fill magazine/clip -> Load mag/clip into weapon

Tips
----
You can build relationships by asking people how they're doing. This will improve trust.

Issues
------
* Throwing does not work
* Freezes sometimes occur when group leaders begin searching for open camp sites
* Pathfinding is very unstable.
	It's the oldest part of the game and is being revised in the next milestone to make use of reference maps and chunks.
