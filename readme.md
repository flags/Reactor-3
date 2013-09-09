![Reactor3](https://raw.github.com/flags/Reactor-3/master/art/pngs/minilogo.png)
Reactor 3
=========
Reactor 3 is an action roguelike in the same vein as IVAN - A Violent Road to Death and S.T.A.L.K.E.R.: Shadow of Chernobyl.

What is Reactor 3?
-------------------
Reactor 3 (R3) is a roguelike. You might be familiar with a few games in the genre, like Dwarf Fortress, NetHack, or DCSS, while also borrowing elements from Fallout and S.T.A.L.K.E.R..

R3 is a game about survival in a hostile, unforgiving environment. It takes place in the Chernobyl Exclusion Zone, where (in an alternate timeline) another disaster occurs, further corrupting the area. It is rumored that the items formed from the spike of radiation can be sold for high amounts of money on the black market.

At its core, R3 is less about combat and more about reputation. The NPCs maintain their own interpretation of the world based on randomly generated personality traits and stats, and can act independently or in groups to accomplish tasks based on this intepretation. Bandits will attack on sight, while others will ask deeper questions before confrontation begins (Am I in danger? What have I heard about this person? etc)

Combat is a last resort, but it is by no means neglected in terms of development. A full damage model is simulated, ranging from minor cuts and scrapes to full dismemberment depending on the type of injury. For example, a bullet fired towards someone wearing a backback will result in either the bullet tearing through it, or possibly colliding and causing damage to an item inside of it.

The game is developed in two parts: Engine and content. The engine still currently houses *some* content-specific features (for now), but forms most of its functionality by parsing external files that can be thought of as mods. Anything from controlling the body structure of an entity to its AI can be done outside of the game's code entirely.

Screenshots
-----------
[Imgur gallery.]()

If You're Reading This...
-------------------------
This game has been in the works for roughly 10 months, but I chose to keep the repo private until I had at least something to show. The bad news is that there isn't much in the way of content yet (intentionally.) As I've said in the past, I wouldn't build content around a game that wasn't ready for it. I knew from the start that I would want to be able to make changes without fearing a breakage elsewhere, and having very little content has enabled that. What you're seeing here is an engine.

In addition, I am enamored with the idea of a game that generates its own stories and its own content, and much like other games in the genre, I feel like I can accomplish something similar, but it will take time and dedication before I might ever see the payoff from it.

Features
========

ALife
-----
* A dialog system.
* ALife maintain a list of needs. They will ask you and other ALife for food/drinks if none are around.
* ALife will invite you to join squads.
* ALife will explore the map somewhat intelligently (following roads, checking buildings, etc)
* ALife understand the concepts of: Trust, Danger, Willpower, Extroversion/Introversion, Leadership/Influence/Charisma.
* ALife are capable of forming groups and camps.
* ALife will fight in groups.
* Groups have and understand leaders, in addition to succession when the leader is lost
* ALife understand the world without needing "hints" (they react dynamically.)

General
-------
* A work-in-progress world generator.
* Fully working "realistic" inventory system. You must wear a backpack/other clothing item in order to carry more than two items (Pants have pockets, for example.)
* All Life entities can (and will!) be damaged in realistic ways. Worn and carried items can be torn, dented, pierced, and ripped during combat. Limbs can also be injured or removed entirely.
* Weapons must be loaded as they would normally (Obtain ammo -> fill magazine/clip -> Load mag/clip.)

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
* `V (Shift-v)` - Use radio
* `k` - Open crafting menu
* `w` - Open medical menu
* `C (Shift-c)` - Stand up
* `c` - Crouch
* `Z (Shift-z)` - Prone
* `P (Shift-P)` - Pause
* `o` - Options
* `-` - Debug console

Tips
====
You can build relationships by asking people how they're doing. This will improve trust.

Flags
-----
`reactor-3.py` can be run with a few arguments:

* `--debug` - Allows ReactorWatch (`tools/ReactorWatch.py`) to access debug data across the network while the game is running.
* `--profile` - Dumps a profile to `profile.dat`. `tools/show_profile.py` can be used to view the profile (use the argument `highest` to show the most time consuming functions)

Credits
-------
Reactor 3 is made possible by the `libtcod` library. All other work was done by flags, a member of the ASCII Worlds Collective.
