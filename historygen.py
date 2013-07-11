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
	FIREARMS = numbers.roll(MAX_STREET_SMARTS, 5)
	
	#1 - 10 (SLAPPER - MMA CHAMPION)
	MELEE = numbers.roll(FOUGHT_BACK+STREET_SMART, 5)
	
	#1 - 10 (CLUELESS - WALL STREET)
	TRADING = numbers.roll((MAX_STREET_SMARTS+MAX_BOOK_SMART) - (MATHEMATICS<5), 2)
	
	print 'Birth parents:', HAS_BIRTH_PARENTS
	print 'Adopted:', WAS_ADOPTED
	print 'Parenting quality:', PARENTING_QUALITY
	print 'Bullied:', BULLIED
	print 'Fought back:', FOUGHT_BACK
	print 'Graduated:', GRADUATED
	print 'Street smart:', STREET_SMART
	print 'Math:', MATHEMATICS
	print 'Reading:', READING
	print 'Engineering:', ENGINEERING
	print 'Firearms:', FIREARMS
	print 'Melee:', MELEE,FOUGHT_BACK+STREET_SMART
	print 'Trading:', TRADING
	
	if not HAS_BIRTH_PARENTS:
		HISTORY.append('lost his parents in late childhood')
	
	if WAS_ADOPTED:
		HISTORY.append('and was later adopted')
	
	if PARENTING_QUALITY>=3:
		HISTORY.append('Was raised well')
	elif PARENTING_QUALITY:
		HISTORY.append('Was raised poorly')
	
	if BULLIED:
		HISTORY.append('Was bullied')
		
		if FOUGHT_BACK:
			HISTORY[len(HISTORY)-1] += ', but he fought back'
	
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
		HISTORY.append('Can\'t hold his own in a fist fight')
	
	print '. '.join(HISTORY)+'.'

if __name__ == '__main__':
	create_background({})