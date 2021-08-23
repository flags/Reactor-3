#All of this code is awful and needs to be re-written at some point.
#The line drawing functions have been reimplemented in other modules,
#so I'm not entirely sure how often these are called.

class line_diag:
	def __init__(self, start, end):
		self.path = []
		if start == end: return None
		
		self.start = list(start)
		self.end = list(end)
		
		self.steep = abs(self.end[1]-self.start[1]) > abs(self.end[0]-self.start[0])
		
		if self.steep:
			self.start = self.swap(self.start[0],self.start[1])
			self.end = self.swap(self.end[0],self.end[1])
		
		if self.start[0] > self.end[0]:
			self.start[0],self.end[0] = self.swap(self.start[0],self.end[0])		
			self.start[1],self.end[1] = self.swap(self.start[1],self.end[1])
		
		dx = self.end[0] - self.start[0]
		dy = abs(self.end[1] - self.start[1])
		error = 0
		
		try:
			derr = dy/float(dx)
		except:
			return None
		
		ystep = 0
		y = self.start[1]
		
		if self.start[1] < self.end[1]: ystep = 1
		else: ystep = -1
		
		for x in range(self.start[0],self.end[0]+1):
			if self.steep:
				self.path.append((y,x))
			else:
				self.path.append((x,y))
			
			error += derr
			
			if error >= 0.5:
				y += ystep
				error -= 1.0
		
		if not self.path[0] == (start[0],start[1]):
			self.path.reverse()
	
	def swap(self,n1,n2):
		return [n2,n1]

def diag_line(start, end):
	_l = line_diag(start,end)
	
	return _l.path

def draw_3d_line(pos1,pos2):
	_xchange = pos2[0]-pos1[0]
	_ychange = pos2[1]-pos1[1]
	_zchange = pos2[2]-pos1[2]
	
	_line = [tuple(pos1)]	
	
	if abs(_xchange) >= abs(_ychange) and abs(_xchange) >= abs(_zchange):
		_xnegative = False
		_ynegative = False
		_znegative = False
		
		if _ychange < 0:
			_ynegative = True
		
		if _xchange < 0:
			_xnegative = True
		
		if _zchange < 0:
			_znegative = True
		
		_x = pos1[0]
		_y = pos1[1]
		_z = pos1[2]
		
		try:
			_ystep = abs(_ychange/float(_xchange))
		except:
			_ystep = abs(_ychange)
		
		try:
			_zstep = abs(_zchange/float(_xchange))
		except:
			_zstep = abs(_zchange)
		
		for x in range(1,abs(_xchange)):
			if _xnegative:
				x = -x
			
			if _ynegative:
				_y -= _ystep
			else:
				_y += _ystep
			
			if _znegative:
				_z -= _zstep
			else:
				_z += _zstep
			
			_line.append((_x+x,int(round(_y)),int(round(_z))))
	
	elif abs(_ychange) >= abs(_xchange) and abs(_ychange) >= abs(_zchange):
		_xnegative = False
		_ynegative = False
		_znegative = False
		
		if _ychange < 0:
			_ynegative = True
		
		if _xchange < 0:
			_xnegative = True
		
		if _zchange < 0:
			_znegative = True
		
		_x = pos1[0]
		_y = pos1[1]
		_z = pos1[2]
		_xstep = abs(_xchange/float(_ychange))
		_zstep = abs(_zchange/float(_ychange))
		
		for y in range(1,abs(_ychange)):
			if _ynegative:
				y = -y
			
			if _xnegative:
				_x -= _xstep
			else:
				_x += _xstep
			
			if _znegative:
				_z -= _zstep
			else:
				_z += _zstep
			
			_line.append((int(round(_x)),_y+y,int(round(_z))))

	elif abs(_zchange) > abs(_xchange) and abs(_zchange) > abs(_ychange):
		_xnegative = False
		_ynegative = False
		_znegative = False
		
		if _zchange < 0:
			_znegative = True
		
		if _xchange < 0:
			_xnegative = True
		
		if _ychange < 0:
			_ynegative = True
		
		_x = pos1[0]
		_y = pos1[1]
		_z = pos1[2]
		_xstep = abs(_xchange/float(_zchange))
		_ystep = abs(_ychange/float(_zchange))
		
		for z in range(1,abs(_zchange)):
			if _znegative:
				z = -z
			
			if _xnegative:
				_x -= _xstep
			else:
				_x += _xstep
			
			if _ynegative:
				_y -= _ystep
			else:
				_y += _ystep
			
			_line.append((int(round(_x)),int(round(_y)),_z+z))
	
	_line.append(tuple(pos2))
	
	return _line

def draw_circle(at, size):
	Circle = 0
	width=size
	height=size
	CenterX=(width/float(2))
	CenterY=(height/float(2))
	circle = []

	for i in range(height+1):
		for j in range(width+1):
			Circle = (((i-CenterY)*(i-CenterY))/((float(height)/2)*(float(height)/2)))+((((j-CenterX)*(j-CenterX))/((float(width)/2)*(float(width)/2))));
			if Circle>0 and Circle<1.1:
				circle.append((at[0]+(j-(width//2)),at[1]+(i-(height//2))))
	
	if not at in circle:
		circle.append(at)
	
	return circle