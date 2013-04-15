import drawing
import numbers
import numpy
import time

_stime = time.time()
sight = 30
start_point = (45, 45)
source_map = numpy.zeros((100, 100))
source_map[46,46] = 1
source_map[55,35] = 1
source_map[47,40] = 1
source_map[39,43] = 1
source_map[39,49] = 1
los = numpy.ones((60, 60))

#At 45 degrees we are sending out 8 feelers
#If they don't find anything then we'll scale down

def check_dirs(intensity=45, already_checked={}, scan=(0, 360), quad_check=True):
	_check_dirs = already_checked
	_checked_quads = [deg/90 for deg in already_checked]
	
	for deg in range(scan[0], scan[1], intensity):
		if quad_check and deg/90 in _checked_quads:
			continue
		
		_end_x,_end_y = numbers.velocity(deg, sight)[:2]
		end_point = (int(start_point[0]+_end_x), int(start_point[1]+_end_y))
		_line = drawing.diag_line(start_point, end_point)
		_i = 0
		_wall = False
		for pos in _line:
			_x,_y = pos
			_x -= 30
			_y -= 30
			_i += 1
			
			if source_map[pos[1], pos[0]]:
				_check_dirs[deg] = _line[:_i]
				_wall = True
				continue
			
			if _wall:
				los[_y, _x] = 0
	
	return _check_dirs

_check_dirs = {}
intensity = 45

while 1:
	_check_dirs = check_dirs(intensity=intensity, already_checked=_check_dirs)
	quads_to_check = [entry/90 for entry in _check_dirs if _check_dirs[entry]]
	intensity /= 2
	
	if intensity<=8:
		break

for quad in quads_to_check:
	_scan = scan=(numbers.clip(quad*90, 0, 360), (numbers.clip((quad+1)*90, 0, 360)))
	#print _scan
	check_dirs(intensity=2, scan=_scan, quad_check=False)

print time.time()-_stime
#print _check_dirs.keys()
print quads_to_check

for _y in range(30):
	for _x in range(30):
		if los[_y, _x]:
			print int(los[_y, _x]),
		else:
			print ' ',
	print

#for entry in to_check:
#	print entry
