from globals import *

import life as lfe

import judgement
import survival

import logging

def conditions(life):
	RETURN_VALUE = STATE_UNCHANGED
	
	if not lfe.execute_raw(life, 'state', 'managing'):
		return False
	
	return True

def tick(life):
	return survival.manage_inventory(life)
