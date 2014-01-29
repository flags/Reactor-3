Reactor 3
=========

What is Reactor 3?
------------------
Reactor 3 is best described as a mix S.T.A.L.K.E.R. and Fallout with the additon of procedurally generated elements.
There is a heavy emphasis on NPC interaction, squad tactics, and survival, with each action you make shaping the Zone,
an unstable area surrounding the Chernobyl Nuclear Power Plant. The Zone itself is a living entity, causing erratic
weather events and transforming the local wildlife into hostile mutants.

R3 is brutally difficult and unforgiving, punishing those who choose a run-'n-gun playstyle over non-combat solutions.
Combat is heavily grounded in reality, modeling minor injuries like scrapes and cuts to full dismemberment. The player's
inventory is also treated as it should; each item must be either held, worn, or stored away in a container (backpack,
pocket, etc,) which encourages the player to not only pick and choose between what they carry, but also how they carry
it (a pistol would be stored in a holster for quicker access, for example.)

Join a faction and take over the Zone

Features
========

* Huge randomized world. Explore military bases, abandoned towns,
* Full ballistics system.
* 

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
* `F (Shift-f)` - Set fire mode
* `v` - Enter targeting mode (talk)
* `V (Shift-v)` - Use radio
* `k` - Open crafting menu
* `w` - Open medical menu
* `W (Shift-w)` - Open medical menu (heal someone)
* `C (Shift-c)` - Stand up
* `c` - Crouch
* `Z (Shift-z)` - Prone
* `P (Shift-P)` - Pause
* `l` - Look
* `O (Shift-o)` - Options
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
