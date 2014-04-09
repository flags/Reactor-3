from globals import *

import numbers

import random

_HISTORY = {'life': {},
            'groups': {},
            'camps': {}}

def create_background(life):
	HISTORY = []
	
	#This will decide who the person is and what their deal is...
	#i.e., we already roll their stats, but this is building up some
	#credibility behind all that (via implanting memories.)
	#All memories created here will have times in the negatives, with 0
	#being the moment they enter the map.
	#This will at least give me some control over how the initial world
	#develops because atm it's completely random.
	#Onwards... initial behaviors gen
	
	#Just going to start listing things that I believe play a role in
	#someone's development. Don't take these too seriously...
	
	#BOOL (HAS BIRTH PARENTS)
	HAS_BIRTH_PARENTS = (random.randint(0, 1) == 1)
	
	#BOOL (WAS ADOPTED)
	WAS_ADOPTED = ((random.randint(0, 1) * (not HAS_BIRTH_PARENTS)) == 1)
	
	#1 - 6 (ABSENT - STRICT)
	PARENTING_QUALITY = numbers.roll(2, 3) * (HAS_BIRTH_PARENTS or WAS_ADOPTED)
	
	#BOOL (WAS BULLIED)
	BULLIED = (random.randint(0, 1) == 1)
	
	#BOOL (FOUGHT BACK)
	FOUGHT_BACK = (random.randint(0, 1) == 1)
	
	#1 - 10 (DROP OUT < 5, GRADUATED)
	GRADUATED = (numbers.roll(HAS_BIRTH_PARENTS+WAS_ADOPTED, 5)>=5)
	
	#BOOL (STREET SMART)
	STREET_SMART = ((random.randint(0, 1) * (not GRADUATED)) == 1)
	
	MAX_BOOK_SMART = 1 + (not STREET_SMART)
	MAX_STREET_SMARTS = 1 + STREET_SMART
	
	#1 - 10 (NUMBERS??? - MATHEMATICIAN)
	MATHEMATICS = numbers.roll(MAX_BOOK_SMART, 5)
	
	#1 - 10 (CAN'T READ - SPEEDREADER)
	READING = numbers.roll(MAX_BOOK_SMART, 5)
	
	#1 - 10 (CLUELESS - DIY MASTER)
	ENGINEERING = numbers.roll(MAX_BOOK_SMART, 5)
	
	#1 - 10 (SCARY GUNS - I LOVE GUNS)
	FIREARMS = numbers.clip(numbers.roll(MAX_STREET_SMARTS, 5), 5, 10)
	
	#1 - 10 (SLAPPER - MMA CHAMPION)
	MELEE = numbers.roll(FOUGHT_BACK+STREET_SMART, 5)
	
	#1 - 10 (CLUELESS - WALL STREET)
	TRADING = numbers.roll((MAX_STREET_SMARTS+MAX_BOOK_SMART) - (MATHEMATICS<5), 2)
	
	#BOOL (IS LEADER)
	IS_LEADER = (numbers.roll((2<PARENTING_QUALITY<=4 or FOUGHT_BACK)+(GRADUATED or STREET_SMART), 4)>=4)
	
	#BOOL (SELF ABSORBED)
	SELF_ABSORBED = (numbers.roll((PARENTING_QUALITY>=5)+(MAX_BOOK_SMART==1), 5)>=7)
	
	#BOOL (LONE WOLF)
	LONE_WOLF = ((numbers.roll(SELF_ABSORBED+STREET_SMART, 5) * (not IS_LEADER))>=5)
	
	#1 - 10 (ADHD - PATIENCE OF A SAINT)
	PATIENCE = numbers.roll((GRADUATED or STREET_SMART)+(READING>=5 or PARENTING_QUALITY>=3), 5)

	#0 - 3 (PERSONALITY TOTALS)
	INTROVERSION = LONE_WOLF+(not HAS_BIRTH_PARENTS and not WAS_ADOPTED)+(not STREET_SMART)+(BULLIED and not FOUGHT_BACK)
	EXTROVERSION = 3-INTROVERSION
	
	#1 - 10 (INNOCENT - GANG LEADER)
	MOTIVE_FOR_CRIME = numbers.roll((READING<7)+(FIREARMS>6 or MELEE>5)+(TRADING>5 or SELF_ABSORBED)+(not LONE_WOLF)+(BULLIED or IS_LEADER), 2)
	
	#1 - 9 (BARRY - DAVE)
	MOTIVE_FOR_WEALTH = numbers.roll((TRADING>4)+(MATHEMATICS>4)+(PATIENCE>5 or IS_LEADER), 3)
	
	#1 - 9 (BARRY - DAVE)
	MOTIVE_FOR_SURVIVAL = numbers.roll((FIREARMS>5 or MOTIVE_FOR_WEALTH<5)+(MELEE>5 or PATIENCE>5)+(ENGINEERING>5 or IS_LEADER), 3)
	
	#1 - 10 (ANTISOCIAL FREAK - "A REAL RAGER")
	SOCIABILITY = numbers.roll((not SELF_ABSORBED) + (not LONE_WOLF)+(EXTROVERSION>0)+(IS_LEADER*2), 2)
	
	#1 - 10 (TALKS TO STRANGERS - FORT KNOX)
	TRUSTINESS = numbers.roll((LONE_WOLF)+(TRADING>4)+(MOTIVE_FOR_WEALTH>4)+(not SELF_ABSORBED)+(EXTROVERSION>1), 2)
	
	#STRING (INTENTION)
	# FORTUNE
	# GREED
	# 
	#INTENTION = 
	
	#print 'Birth parents:', HAS_BIRTH_PARENTS
	#print 'Adopted:', WAS_ADOPTED
	#print 'Parenting quality:', PARENTING_QUALITY
	#print 'Bullied:', BULLIED
	#print 'Fought back:', FOUGHT_BACK
	#print 'Graduated:', GRADUATED
	#print 'Street smart:', STREET_SMART
	#print 'Math:', MATHEMATICS
	#print 'Reading:', READING
	#print 'Engineering:', ENGINEERING
	#print 'Firearms:', FIREARMS
	#print 'Melee:', MELEE
	#print 'Trading:', TRADING
	#print 'Leader:', IS_LEADER
	#print 'Self-absorbed:', SELF_ABSORBED
	#print 'Lone wolf:', LONE_WOLF
	#print 'Patience:', PATIENCE
	#print 'Introversion:', INTROVERSION
	#print 'Extroversion:', EXTROVERSION
	#print 'Charisma:', CHARISMA
	#print 'Sociability:', SOCIABILITY
	#print 'Motive for crime:', MOTIVE_FOR_CRIME
	#print 'Motive for wealth:', MOTIVE_FOR_WEALTH
	#print 'Motive for survival:', MOTIVE_FOR_SURVIVAL
	
	if not HAS_BIRTH_PARENTS:
		HISTORY.append('Lost his parents in late childhood')
	
	if WAS_ADOPTED:
		HISTORY[len(HISTORY)-1] += ', but was later adopted'
	
	if PARENTING_QUALITY>=3:
		HISTORY.append('Was raised well')
	elif PARENTING_QUALITY:
		HISTORY.append('Was raised poorly')
	
	if BULLIED:
		if 'well' in HISTORY[len(HISTORY)-1]:
			HISTORY[len(HISTORY)-1] += ', but was bullied'
		elif 'poorly' in HISTORY[len(HISTORY)-1]:
			HISTORY[len(HISTORY)-1] += ', and was bullied'
		else:
			HISTORY.append('He was bullied')
		
		if FOUGHT_BACK:
			if ',' in HISTORY[len(HISTORY)-1]:
				HISTORY[len(HISTORY)-1] += ' (he fought back)'
	
	if GRADUATED:
		HISTORY.append('Graduated')
	elif STREET_SMART:
		HISTORY.append('Is street smart')
		
	if MATHEMATICS>=5:
		HISTORY.append('Is good at math')
	elif MATHEMATICS <= 2:
		HISTORY.append('Is bad with numbers')
	
	if READING>=5:
		HISTORY.append('Can read very well')
	elif READING <= 3:
		HISTORY.append('Was not hooked on phonics')
	
	if ENGINEERING>=5:
		HISTORY.append('Is proficient at engineering')
	elif ENGINEERING <= 3:
		HISTORY.append('Has poor engineering skills')
	
	if FIREARMS>=5:
		HISTORY.append('Knows his way around a gun')
	elif FIREARMS <= 3:
		HISTORY.append('Has shaky aim')
		
	if MELEE>=5:
		HISTORY.append('Can fight very well')
	elif MELEE<=3:
		if 'gun' in HISTORY[len(HISTORY)-1]:
			HISTORY[len(HISTORY)-1] += ', but can\'t hold his own in a fist fight'
		else:
			HISTORY[len(HISTORY)-1] += ' and can\'t fight'
	
	if IS_LEADER:
		if SELF_ABSORBED:
			HISTORY.append('Would rather lead than follow')
		else:
			HISTORY.append('Is a fine leader')
	elif LONE_WOLF:
		HISTORY.append('Prefers to work alone')
	
	if PATIENCE>=7:
		HISTORY.append('Patient')
	elif PATIENCE<=3:
		HISTORY.append('Very impatient')
	
	#print '. '.join(HISTORY)+'.'	
	
	return {'mathematics': MATHEMATICS,
		'reading': READING,
		'engineering': ENGINEERING,
		'firearms': FIREARMS,
		'melee': MELEE,
		'trading': TRADING,
		'is_leader': IS_LEADER,
		'self_absorbed': SELF_ABSORBED,
		'lone_wolf': LONE_WOLF,
		'patience': PATIENCE,
		'trustiness': TRUSTINESS,
		'sociability': SOCIABILITY,
		'psychotic': False,
		'description': '. '.join(HISTORY)+'.',
		'motive_for_crime': MOTIVE_FOR_CRIME,
		'motive_for_wealth': MOTIVE_FOR_WEALTH,
		'motive_for_survival': MOTIVE_FOR_SURVIVAL}

if __name__ == '__main__':
	create_background({})