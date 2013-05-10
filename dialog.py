#A note before we start...
#It's impossible to summarize conversations into a single word,
#so we'll be passing around dictionaries that contain details
#of it so we can perform fuzzy matches across memories when
#finding responses.

from globals import *

import life as lfe

def create_dialog_with(life, target, **kwargs):
	_topics = []
	
	#If we're getting a gist then the conversation has already been started in some respect...
	#we'll get responses for now
	if gist:
		_responses = get_all_responses_to(life, kwargs)
		#_topics.extend(get_all_relevant_gist_topics(life, gist)
	else:
		_topics.extend(get_all_relevant_target_topics(life, target))

def get_all_relevant_gist_topics(life, gist):
	#TODO: We'll definitely need to extend this for fuzzy searching
	return [memory for memory in lfe.get_memory(life, matches={'text': gist})]

def get_all_relevant_target_topics(life, target):
	return [memory for memory in lfe.get_memory(life, matches={'target': target})]

def get_all_responses_to(life, **kwargs):
	for memory in lfe.get_memory(life, matches=kwargs):
		print memory
