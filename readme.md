Reactor 3
=========

Note
----

Please grab the `unstable` branch of the game when cloning. Some changes to
Numpy have rendered the game unplayable due to a file conflict and I've renamed
that file on that branch only. Also, **delete all instances of `numbers.pyc`**.

I stopped working on this in 2014, but a successor is being privately developed
using a new framework written in C. I will post on Reddit's `roguelike` or
`roguelikedev` subforums eventually.

Please do not use this game's code as a guide for working with Python / libtcod.
I had never developed a project this size before and was learning along the way.
R3 accomplished what it did via brute force and creative engineering. I don't
recommend that way of working.

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

Join a faction and take over the Zone, or simply exist on your own.

Installing
==========
Reactor 3 requires Python 3.6+ on a platform which can compile Python extensions.

    git clone https://github.com/flags/Reactor-3.git
    cd Reactor-3
    python -m pip install -r requirements.txt
    python compile_cython_modules.py build_ext --inplace

Run `python reactor-3.py` to play.

See the section `flags` below for more info.

Controls
========
* `Arrow keys` - Move (4-way movement)/Navigate menus
* `Numpad` - Moe (8-way movement)
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
* `Tab` - Group communication
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
* `?` - Record mode (**This will dump potentially hundreds of .BMP files in the game's directory**)

Flags
-----
`reactor-3.py` can be run with a few arguments:

* `--quick` - Load latest game.
* `--profile` - Dumps a profile to `profile.dat`. `tools/show_profile.py` can be used to view the profile (use the argument `highest` to show the most time consuming functions)

Credits
-------
Reactor 3 is made possible by the `libtcod` library. All other work was done by flags, a member of the ASCII Worlds Collective.
