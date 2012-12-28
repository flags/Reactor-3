from globals import *
import graphics as gfx
import drawing

def create_bullet(pos,velocity,owner_id):
	bullet = {'pos': list(pos),
		'realpos': list(pos),
		'velocity': list(velocity),
		'owner': owner_id}
	
	BULLETS.append(bullet)

def tick_bullets(MAP):
	for bullet in BULLETS:
		bullet['realpos'][0] += bullet['velocity'][0]
		bullet['realpos'][1] += bullet['velocity'][1]
		
		for pos in drawing.diag_line(bullet['pos'],(int(bullet['realpos'][0]),int(bullet['realpos'][1]))):
			if 0>pos[0] or pos[0]>=MAP_SIZE[0] or 0>pos[1] or pos[1]>=MAP_SIZE[1]:
				BULLETS.remove(bullet)
				break
			
			for life in LIFE:
				if life['pos'][0] == pos[0] and life['pos'][1] == pos[1]:
					bullet['velocity'][0] = 0
					bullet['velocity'][1] = 0
			
			if MAP[pos[0]][pos[1]][bullet['pos'][2]]:
				bullet['velocity'][0] = 0
				bullet['velocity'][1] = 0
				bullet['velocity'][2] = 0
		
		bullet['pos'][0] = int(bullet['realpos'][0])
		bullet['pos'][1] = int(bullet['realpos'][1])

def draw_bullets():
	for bullet in BULLETS:
		if bullet['pos'][0] >= CAMERA_POS[0] and bullet['pos'][0] < CAMERA_POS[0]+MAP_WINDOW_SIZE[0] and\
			bullet['pos'][1] >= CAMERA_POS[1] and bullet['pos'][1] < CAMERA_POS[1]+MAP_WINDOW_SIZE[1]:
			_x = bullet['pos'][0] - CAMERA_POS[0]
			_y = bullet['pos'][1] - CAMERA_POS[1]
			
			if not LOS_BUFFER[0][_y,_x]:
				continue
			
			gfx.blit_char(_x,
				_y,
				'o',
				white,
				None,
				char_buffer=MAP_CHAR_BUFFER,
				rgb_fore_buffer=MAP_RGB_FORE_BUFFER,
				rgb_back_buffer=MAP_RGB_BACK_BUFFER)
