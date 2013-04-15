import drawing
import numbers
import numpy
import time

_stime = time.time()
sight = 30
start_point = (45, 45)
source_map = numpy.zeros((100, 100))
source_map[30,31] = 1
los = numpy.zeros((30, 30))

def check_dirs(intensity=45, already_checked={}):
	check_dirs = {}
	
	for deg in range(0, 360, intensity):
		if deg in already_checked:
			continue
		
		_end_x,_end_y = numbers.velocity(deg, sight)[:2]
		end_point = (int(start_point[0]+_end_x), int(start_point[1]+_end_y))
		
		_line = drawing.diag_line(start_point, end_point)
		_i = 0
		for pos in _line:
			_i += 1
			if source_map[pos[1], pos[0]]:
				check_dirs[deg] = {'line': _line[:_i]}
				break
			
			check_dirs[deg] = {'line': None}
	
	return check_dirs

#if check_
check_dirs = check_dirs()

for entry in [check_dirs:
	print entry
