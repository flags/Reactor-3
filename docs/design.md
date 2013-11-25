Reactor 3: Design Document
=========

Section 1: Engine
---------

### Preface

Throughout the first phase of Reactor 3's development, a number of techinical
limitations were identified and addressed. These were undocumented and largely
added after the problems they corrected became too big to ignore. Of course,
this type of design is not really design, but instead more of a reaction to bad
design. While the problem of Python's performance has always been an issue,
there have been a few recently developments that have shown the language
beginning to crack.

The idea of this document is to address a number of concerns I have with both
the game and the technology backing it; Reactor 3 suffers from a lack of
uniform structure, and the engine is breaking under the pressure of similar
mistakes, both of which I feel can be fixed.

With the engine still mutable and open to change, now is the time to take action
and do a bit of corrective surgery on what could potentially be a very good
piece of tech. To help make the difference between the game side of Reactor 3
and its engine, an official name will be attached to it: Terraform.

### Addressing Big Data

Reactor 3's world size is currently set to 250x450, meaning 112500 tiles are
being processed at any given time on the main z-level. They do not pose that big
of a threat performance-wise since they are static - however, during December of
2012 I decided to create the "chunk map", which divides the map into 5x5 groups
of tiles on the X and Y axis. Each of these chunks provides a number of useful
traits about the tiles it contains, including the highest Z-level and building
information. Reference maps are an extension of the chunk map, representing
links of similarly-typed chunks for use in ALife. Later, the "zone map" was
added, which helps find sections of the map disconnected from other sections,
useful for pathfinding. All of these work in conjunction to improve performance
and the speed of development.

The world's size was a non-issue early in development; without a large amount of
data to parse, it appeared that most code was ready to scale as needed. This did
not hold true as the game grew and the world was populated with a larger amount
of information. At this point in time, the aforementioned 250x450 world causes
significant issues on hardware that should not have any issues to begin with.

To find potential problem areas, the following tests were conducted:

Active ALife: 0
Items: Parsing
FPS: 100+

Active ALife: 3
Items: Parsing
FPS: 40-45 (Groups settling)
	 80~   (Groups settled)

Active ALife: 3
Items: Skipping
FPS: 40-45 (Groups settling)
	 80~   (Groups settled)

### Technical Limitations
