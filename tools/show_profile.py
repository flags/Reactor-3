#Reads profile, prints sorted output
import pstats
import sys

if len(sys.argv)>=2 and sys.argv[1].count('.dat'):
	profile = sys.argv[1]
else:
	profile = 'profile.dat'

stats = pstats.Stats(profile)

if 'highest' in sys.argv:
	stats.sort_stats('cumulative').print_stats(20)
else:
	stats.strip_dirs().sort_stats(-1).print_stats()
