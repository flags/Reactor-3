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

#At 45 degrees we are sending out 8 feelers
#If they don't find anything then we'll scale down

def check_dirs(intensity=45, already_checked={}):
	_check_dirs = already_checked
	#print 'Vals',already_checked
	_checked_quads = [deg/90 for deg in already_checked]
	
	for deg in range(0, 360, intensity):
		if deg/90 in _checked_quads:
			continue
		
		_end_x,_end_y = numbers.velocity(deg, sight)[:2]
		end_point = (int(start_point[0]+_end_x), int(start_point[1]+_end_y))
		_line = drawing.diag_line(start_point, end_point)
		_i = 0
		for pos in _line:
			_i += 1
			if source_map[pos[1], pos[0]]:
				_check_dirs[deg] = _line[:_i]
				break
	
	#print check_dirs
	return _check_dirs

#if check_
_check_dirs = {}
intensity = 45

while 1:
	_check_dirs = check_dirs(intensity=intensity, already_checked=_check_dirs)
	quads_to_check = [entry for entry in _check_dirs if _check_dirs[entry]]
	intensity /= 2
	
	if quads_to_check:
		break

print quads_to_check

print time.time()-_stime

#for entry in to_check:
#	print entry
