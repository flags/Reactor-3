![Reactor3](https://raw.github.com/flags/Reactor-3/master/art/pngs/minilogo.png)
Reactor 3
=========
Reactor 3 is an action roguelike in the same vein as IVAN - A Violent Road to Death and S.T.A.L.K.E.R.: Shadow of Chernobyl.

If You're Reading This...
-------------------------
This game has been in the works for roughly 9 months, but I chose to keep the repo private until I had at least something to show. The bad news is that there isn't much in the way of content yet (intentionally.) As I've said in the past, I wouldn't build content around a game that wasn't ready for it. I knew from the start that I would want to be able to make changes without fearing a breakage elsewhere, and having very little content has enabled that. What you're seeing here is an engine.

In addition, I am enamored with the idea of a game that generates its own stories and its own content, and much like other games in the genre, I feel like I can accomplish something similar, but it will take time and dedication before I might ever see the payoff from it.

I would wager that a large amount of the people reading this only have a passing interest with the game in its current state. That's entirely fine and I don't expect any of you to play the game at all - after all, a lot of the people I've sent this out to were involved in a game development group I was a part of, and I suppose you lot would just like to see (or hear) about the various inner-workings of this little project that have changed since you've last seen it.

Features
========

ALife
-----
* Dialog with ALife is now possible.
* ALife maintain a list of needs. They will ask you and other ALife for food/drinks if none are around.
* ALife will invite you to join squads (this is mostly untested)
* ALife will explore the map somewhat intelligently (following roads, checking buildings, etc)
* ALife understand the concepts of: Trust, Danger, Willpower, Extroversion/Introversion, Leadership/Influence/Charisma.
* ALife are capable of forming groups and camps.
* ALife will fight in groups (but you have to instigate it.)
* Groups have and understand leaders, in addition to succession when the leader is lost
* ALife understand the world without needing specially designed levels (they react dynamically.)

General
-------
* Fully working "realistic" inventory system. You must wear a backpack/other clothing item in order to carry more than two items (Pants have pockets, for example.)
* all Life entities can (and will!) be damaged in realistic ways. Worn and carried items can be torn, dented, pierced, and ripped during combat. Limbs can also be injured or removed entirely.
* Weapons must be loaded as they would normally (Obtain ammo -> fill magazine/clip -> Load mag/clip into weapon)

Installing
==========
Reactor 3 requires Python 2.7, Cython, Numpy, and [libtcod](http://doryen.eptalys.net/libtcod/download/). The following instructions are aimed at Linux users:

    git clone https://github.com/flags/Reactor-3.git
    cd Reactor-3
    python compile_cython_modules.py build_ext --inplace
    
Next, download the libtcod library and move the `.so` files from the archive to the Reactor 3 directory.

Run `python reactor-3.py` to play.

See the section `flags` below for more info.

Tools
=====
While these applications are stable, they are not as well-developed as Reactor 3.

* Terraform - `terraform.py` - Level editor. Very much in development.
* ReactorWatch - `tools/ReactorWatch.py` - Web-based debugger. Connects to the currently running instance of Reactor 3 and displays debug information via a web interface. Requires Reactor 3 to be running with the `--debug` argument.

Controls
========
* `Arrow keys` - Move (no 8-key movement yet)/Navigate menus
* `Enter` - Select
* `e` - Equip/hold item
* `E (Shift-e)` - Unequip item
* `,` - Pick up item
* `d` - Drop item
* `r` - Reload / fill mag or clip
* `f` - Enter targeting mode (shoot)
* `v` - Enter targeting mode (talk)
* `C (Shift-c)` - Stand up
* `c` - Crouch
* `Z (Shift-z)` - Prone
* `P (Shift-P)` - Pause
* `-` - Debug console

Tips
====
You can build relationships by asking people how they're doing. This will improve trust.

Flags
-----
`reactor-3.py` can be run with a few arguments:

* `--debug` - Allows ReactorWatch (`tools/ReactorWatch.py`) to access debug data across the network while the game is running.
* `--profile` - Dumps a profile to `profile.dat`. `tools/show_profile.py` can be used to view the profile (use the argument `highest` to show the most time consuming functions)

Issues
------
* Throwing does not work
* Freezes sometimes occur when group leaders begin searching for open camp sites
* Pathfinding is very unstable.
	It's the oldest part of the game and is being revised in the next milestone to make use of reference maps and chunks.

Credits
-------
Reactor 3 is made possible by the `libtcod` library. All other work was done by flags, a member of the ASCII Worlds Collective.
