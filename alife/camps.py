import references
import speech

def find_nearest_unfounded_camp(life):
	_nearest_building = references.find_nearest_building(life)
	
	print _nearest_building

def found_camp(life, reference, announce=False):
	#speech.announce(life, 'founded_camp', reference=reference)
	pass

def unfound_camp(life, reference):
	pass

def get_all_alife_in_camp(life, reference):
	#TODO: We should write a function to do this for references, then filter the results here
	pass
