from globals import *

import numbers

import random

_HISTORY = {'life': {},
            'groups': {},
            'camps': {}}

def create_background(life):
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
	
	#1 - 6 (POOR - SPOILED)
	CHILDHOOD_QUALITY = numbers.roll(2, 3)
	
	#1 - 6 (ABSENT - STRICT)
	PARENTING_QUALITY = numbers.roll(2, 3)
	
	#BOOL (HAS BIRTH PARENTS)
	HAS_BIRTH_PARENTS = (random.randint(0, 1) == 1)
	
	#BOOL (WAS ADOPTED)
	WAS_ADOPTED = ((random.randint(0, 1) * (not HAS_BIRTH_PARENTS)) == 1)
	
	#BOOL (WAS BULLIED)
	BULLIED = (random.randint(0, 1) == 1)
	
	#BOOL (FOUGHT BACK)
	FOUGHT_BACK = (random.randint(0, 1) == 1)
	
	#1 - 10 (DROP OUT < 5, GRADUATED)
	GRADUATED = (numbers.roll(HAS_BIRTH_PARENTS+WAS_ADOPTED, 5)<5)
	
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
	TRADING = numbers.roll(MAX_STREET_SMARTS+MAX_BOOK_SMART, 2)
	
	print 'Childhood quality:', CHILDHOOD_QUALITY
	print 'Parenting quality:', PARENTING_QUALITY
	print 'Birth parents:', HAS_BIRTH_PARENTS
	print 'Adopted:', WAS_ADOPTED
	print 'Bullied:', BULLIED
	print 'Fought back:', FOUGHT_BACK
	print 'Graduated:', GRADUATED
	print 'Street smart:', STREET_SMART
	print 'Math:', MATHEMATICS
	print 'Reading:', READING
	print 'Engineering:', ENGINEERING
	print 'Firearms:', FIREARMS
	print 'Melee:', MELEE
	print 'Trading:', TRADING

if __name__ == '__main__':
	create_background({})