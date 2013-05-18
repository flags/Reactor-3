from globals import *

import life as lfe

import logging

def process_questions(life):
	for question in lfe.get_questions(life):
		if not question['text'] in QUESTIONS_ANSWERS:
			logging.error('%s not in QUESTIONS_ANSWERS' % question['text'])
			continue
		
		_answered = False
		_matches = {requirement: '*' for requirement in QUESTIONS_ANSWERS[question['text']]}
		print lfe.get_memory(life, matches=_matches)
		for memory in lfe.get_memory(life, matches=_matches):
			if not memory['id'] in question['answered']:
				question['answered'].append(memory['id'])
				_answered = True
		
		if _answered:
			if len(question['answered']) == 1:
				logging.debug('%s answered question: %s' % (' '.join(life['name']), memory['text']))
			else:
				logging.debug('%s added more detail to question: %s' % (' '.join(life['name']), memory['text']))

def process(life):
	process_questions(life)
