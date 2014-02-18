import random
import numpy
import json
import math


_weapon = {'recoil': 0.3,
           'accuracy': 0.9}
stance_mod = 1.0
aim_difficulty = 1.3
firearms_skill_mod = 0.55
hit_certainty_mod = 0.6
bullets = 100
simulaton_ticks = 8

def load_weapon(weapon_file):
	with open(weapon_file, 'r') as wfile:
		_weapon.update(json.loads(''.join(wfile.readlines())))

def velocity(direction, speed):
	rad = direction*(math.pi/180)
	velocity = numpy.multiply(numpy.array([math.cos(rad), math.sin(rad)]), speed)
	
	return [velocity[0], -velocity[1], 0]

def clip(number,start,end):
	return max(start, min(number, end))

def bullet_trajectory(bullet_pos, bullet_direction, ticks=simulaton_ticks):
	bullet_velocity = velocity(bullet_direction, 5)
	
	for i in range(ticks):
		bullet_pos[0] += bullet_velocity[0]
		bullet_pos[1] += bullet_velocity[1]
	
	return bullet_pos

def simulate(firearms_skill):
	recoil = 0.0
	bullet_direction = 0
	bullet_pos = [0, 0]
	bullet_velocity = [0, 0]
	_deviations = []
	_hits = 0
	
	print 'Skill:', firearms_skill
	
	for i in range(bullets):
		bullet_velocity = [0, 0]
		bullet_pos = [0, 0]
		bullet_deviation = (1-_weapon['accuracy'])+recoil
		deviation_mod = aim_difficulty*(1-((firearms_skill/10.0)*firearms_skill_mod))
		deviation = (bullet_deviation*aim_difficulty)*deviation_mod
		bullet_direction = random.uniform(-deviation, deviation)
		
		#print 'Shot #%s (dev_mod=%0.4f, rec=%0.3f, ticks=%s)' % (i+1, deviation_mod, recoil, simulaton_ticks)
		recoil = clip(recoil+(_weapon['recoil']*stance_mod), 0.0, 1.0)
		
		_end_pos = bullet_trajectory(bullet_pos, bullet_direction)
		_direction_deviation = abs(bullet_direction)
		_target_hit_certainty = _direction_deviation/hit_certainty_mod
		_hits += _target_hit_certainty<=1
		_deviations.append(_direction_deviation)
	
	print 'Deviations: mean=%0.4f, min=%0.4f, max=%0.4f' % (sum(_deviations)/len(_deviations), min(_deviations), max(_deviations))
	print 'Accuracy:', _hits/float(bullets), '\n'
	
	#print 'Trajectory deviation: %0.4f' % _direction_deviation
	#print 'Non-certainty: %s (hit=%s)' % (_target_hit_certainty, _target_hit_certainty<=1)
	#print 'Limb accuracy: %0.4f' % (1-(_target_hit_certainty/1.0))*int(_target_hit_certainty<=1)
	#print
	#print 'dir', bullet_direction, 'dev', bullet_deviation, 'rec', recoil
	
	return _hits/float(bullets)

_path = 'C:\\cygwin\\home\\Luke\\code\\Reactor-3\\data\\items\\glock.json'
load_weapon(_path)

_accuracies = []
for i in range(1, 10+1):
	_accuracies.append(simulate(i))
	
	print 'Total accuracy: %0.4f' % (sum(_accuracies)/float(len(_accuracies)))
