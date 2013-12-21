from globals import *

import life as lfe

import judgement
import movement

import logging


def tick(life):
	movement.find_target(life, judgement.get_target_to_follow(life), call=False)
