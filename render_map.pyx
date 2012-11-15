from tiles import *
import graphics as gfx

def render_map(map):
	cdef int _CAMERA_POS[2]
	
	cdef int _X_MAX = CAMERA_POS[0]+MAP_WINDOW_SIZE[0]
	cdef int _Y_MAX = CAMERA_POS[1]+MAP_WINDOW_SIZE[1]
	cdef int _X_START = CAMERA_POS[0]
	cdef int _Y_START = CAMERA_POS[1]
	cdef int _RENDER_X = 0
	cdef int _RENDER_Y = 0
	
	DARK_BUFFER[0] = numpy.zeros((MAP_WINDOW_SIZE[1], MAP_WINDOW_SIZE[0]))
	LIGHT_BUFFER[0] = numpy.zeros((MAP_WINDOW_SIZE[1], MAP_WINDOW_SIZE[0]))

	if _X_MAX>MAP_SIZE[0]:
		_X_MAX = MAP_SIZE[0]

	if _Y_MAX>MAP_SIZE[1]:
		_Y_MAX = MAP_SIZE[1]

	for x in range(_X_START,_X_MAX):
		_RENDER_X = x-CAMERA_POS[0]
		for y in range(_Y_START,_Y_MAX):
			_RENDER_Y = y-CAMERA_POS[1]
			_drawn = False
			for z in range(MAP_SIZE[2]):
				if map[x][y][z]:
					if z > CAMERA_POS[2] and SETTINGS['draw z-levels above']:
						gfx.blit_tile(_RENDER_X,_RENDER_Y,map[x][y][z])
						gfx.lighten_tile(_RENDER_X,_RENDER_Y,abs((CAMERA_POS[2]-z))*30)
						_drawn = True
					elif z == CAMERA_POS[2]:
						if (x,y,z) in SELECTED_TILES and time.time()%1>=0.5:
							gfx.blit_char(_RENDER_X,_RENDER_Y,'X',darker_grey,black)
						else:
							gfx.blit_tile(_RENDER_X,_RENDER_Y,map[x][y][z])
							gfx.lighten_tile(_RENDER_X,_RENDER_Y,0)
							gfx.darken_tile(_RENDER_X,_RENDER_Y,0)
						_drawn = True
					elif z < CAMERA_POS[2]:
						if SETTINGS['draw z-levels below']:
							gfx.blit_tile(_RENDER_X,_RENDER_Y,map[x][y][z])
							gfx.darken_tile(_RENDER_X,_RENDER_Y,abs((CAMERA_POS[2]-z))*30)
							_drawn = True
			
			if not _drawn:
				gfx.blit_tile(_RENDER_X,_RENDER_Y,BLANK_TILE)