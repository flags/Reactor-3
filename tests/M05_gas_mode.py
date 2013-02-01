import numpy
import time
import sys

if not len(sys.argv)==3:
	print 'Expects: python gas_mode.py <width> <height>'
	sys.exit(1)

X_SIZE = int(sys.argv[1])
Y_SIZE = int(sys.argv[2])

SOURCE_MAP = numpy.zeros((X_SIZE,Y_SIZE))

def simulate():
	NEXT_MAP = map.copy()

	for MOD_X in range(X_SIZE):
		for MOD_Y in range(Y_SIZE):
			for X_OFFSET in range(-1,2):
				for Y_OFFSET in range(-1,2):

