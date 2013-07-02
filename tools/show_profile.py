#Reads profile, prints sorted output
import pstats
import sys

profile = 'profile.dat'
stats = pstats.Stats(profile)

if 'highest' in sys.argv:
	stats.sort_stats('cumulative').print_stats(10)
else:
	stats.strip_dirs().sort_stats(-1).print_stats()
