from globals import *

import life as lfe
import alife
import zones
import fov as _fov

import time
import pp

def init():
	SETTINGS['smp'] = pp.Server() 

def test(life, key=None):
	return (life, key)

def process(callback, life, **kwargs):
	return [life, callback(life, **kwargs)]
