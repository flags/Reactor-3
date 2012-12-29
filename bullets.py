from globals import *
import graphics as gfx
import drawing
import numpy
import life
import math

def create_bullet(pos,direction,speed,owner):
	rad = direction*(math.pi/180)
	
	velocity = numpy.array([math.cos(rad),math.sin(rad)])
	_xvel,_yvel = numpy.multiply(velocity,speed)
	velocity = [_xvel,-_yvel]
	
	bullet = {'pos': list(pos),
		'realpos': list(pos),
		'spos': list(pos),
		'maxvelocity': list(velocity),
		'velocity': velocity,
		'sharp': True,
		'damage': 60,
		'fallspeed': 0.05,
		'owner': owner}
	
	BULLETS.append(bullet)

def tick_bullets(MAP):
	for bullet in BULLETS:
		if not bullet['velocity'][0] and not bullet['velocity'][1]:
			continue
		
		bullet['realpos'][0] += bullet['velocity'][0]
		bullet['realpos'][1] += bullet['velocity'][1]
		_break = False
		
		for pos in drawing.diag_line(bullet['pos'],(int(bullet['realpos'][0]),int(bullet['realpos'][1]))):
			if 0>pos[0] or pos[0]>=MAP_SIZE[0] or 0>pos[1] or pos[1]>=MAP_SIZE[1]:
				BULLETS.remove(bullet)
				break
			
			for _life in LIFE:
				if _life == bullet['owner']:
					continue
				
				if _life['pos'][0] == pos[0] and _life['pos'][1] == pos[1]:
					bullet['pos'] = pos
					life.damage(_life,bullet)
					_break = True
					
					BULLETS.remove(bullet)
					break
				
			if _break:
				break
					
			
			if MAP[pos[0]][pos[1]][bullet['pos'][2]+1]:
				bullet['velocity'][0] = 0
				bullet['velocity'][1] = 0
				#bullet['velocity'][2] = 0
				bullet['pos'] = list(pos)
				
				_break = True
				break
		
		if _break:
			continue
		
		bullet['pos'][0] = int(bullet['realpos'][0])
		bullet['pos'][1] = int(bullet['realpos'][1])
		
		#TODO: Min/max
		bullet['velocity'][0] -= (bullet['velocity'][0]*bullet['fallspeed'])
		bullet['velocity'][1] -= (bullet['velocity'][1]*bullet['fallspeed'])

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
