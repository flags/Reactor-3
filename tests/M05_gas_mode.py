import numpy
import time
import sys

if not len(sys.argv)==3:
	print('Expects: python gas_mode.py <width> <height>')
	sys.exit(1)

X_SIZE = int(sys.argv[1])
Y_SIZE = int(sys.argv[2])

SOURCE_MAP = numpy.zeros((X_SIZE,Y_SIZE))

#print SOURCE_MAP.shape,X_SIZE,Y_SIZE

def simulate(MAP):
	NEXT_MAP = numpy.zeros((X_SIZE,Y_SIZE))
	
	_i = 0
	while 1:
		_i += 1
		NEXT_MAP = MAP.copy()

		
		for MOD_Y in range(X_SIZE-1):
			for MOD_X in range(Y_SIZE-1):
				if MAP[MOD_Y,MOD_X] == -1:
					continue
				
				#NEIGHBOR_COUNT = 0
				LARGEST_SCORE = MAP[MOD_Y,MOD_X]+.90
				
				for X_OFFSET in range(-1,2):
					for Y_OFFSET in range(-1,2):
						x = MOD_X+X_OFFSET
						y = MOD_Y+Y_OFFSET
						
						#print Y_SIZE-1
						if 0>x or 0>y or x>=X_SIZE-1 or y>=Y_SIZE-1 or MAP[y,x]<=-1:
							continue
						
						if MAP[y,x] > LARGEST_SCORE:
							LARGEST_SCORE = MAP[y,x]
						
				NEXT_MAP[MOD_Y,MOD_X] = LARGEST_SCORE-(0.95)
				
				if NEXT_MAP[MOD_Y,MOD_X]<0:
					NEXT_MAP[MOD_Y,MOD_X] = 0
		
		draw_map(NEXT_MAP)
		
		if numpy.array_equal(MAP,NEXT_MAP):
			print('Took: ',_i)
			return NEXT_MAP
		
		MAP = NEXT_MAP.copy()

def dissolve(MAP):
	for MOD_Y in range(Y_SIZE):
		for MOD_X in range(X_SIZE):
			if MAP[MOD_X,MOD_Y] <= 0:
				continue
			
			

def draw_map(MAP):
	for MOD_Y in range(Y_SIZE):
		for MOD_X in range(X_SIZE):
			NEIGHBOR_COUNT = 0
			LARGEST_SCORE = 0
			if MAP[MOD_X,MOD_Y] == -1:
				print('x', end=' ')
			else:
				print(MAP[MOD_X,MOD_Y], end=' ')
		
		print('')


SOURCE_MAP[5,5]=8
SOURCE_MAP[5,4]=-1
SOURCE_MAP[5,3]=-1
SOURCE_MAP[6,4]=-1

for x in range(3):
	SOURCE_MAP[7+x,4]=-1

START_TIME = time.time()
SOURCE_MAP = simulate(SOURCE_MAP)

print(time.time()-START_TIME)

draw_map(SOURCE_MAP)
