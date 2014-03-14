from globals import *

import life as lfe

import judgement
import survival

import logging

def conditions(life):
	RETURN_VALUE = STATE_UNCHANGED
	
	if lfe.execute_raw(life, 'state', 'managing'):
		return True
	
	return False

def tick(life):
	return survival.manage_inventory(life)
