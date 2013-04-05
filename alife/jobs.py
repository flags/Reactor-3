#Let's do this the right way...
from globals import *

import judgement
import speech

import logging

def create_job(creator, gist):
	_job = {'creator': creator}
	_job['gist'] = gist
	_job['score'] = 0
	_job['tasks'] = []
	_job['factors'] = []
	_job['workers'] = []
	_job['candidates'] = []
	JOBS[len(JOBS)] = _job
	
	logging.debug('%s created new job: %s' % (' '.join(creator['name']), gist))
	
	return _job

def add_job_factor(job, factor_type, value):
	_factor = {'type': factor_type,
		'value': value}
	
	if factor_type == 'alife':
		_factor['value'] = value['id']
	
	job['factors'].append(_factor)
	
	logging.debug('Added factor to job: %s' % factor_type)

def add_job_task(job, task, required=False):
	_task = {'task': task,
		'workers': [],
		'required': required}
	job['tasks'].append(_task)
	
	logging.debug('Added task to job: %s' % task)

def add_job_candidate(job, life):
	job['candidates'].append(life['id'])
	
	logging.debug('Added candidate to job: %s' % ' '.join(life['name']))

def is_job_candidate(job, life):
	if life['id'] in job['candidates']:
		return True
	
	return False

def take_job(life, job, task):
	job['workers'].append(life['id'])
	
	for _task in job['tasks']:
		if not _task['task'] == task:
			continue
		
		_task['workers'].append(life['id'])
		break
	
	logging.debug('%s joined job: %s' % (' '.join(life['name']), job['gist']))

def is_working_job(life, job):
	if life['id'] in job['workers']:
		return True
	
	return False

def alife_is_factor_of_job(life, job):
	if life['id'] in job['factors']:
		return True
	
	return False

def announce_job(life, job):
	speech.announce(life, 'job', job=job)
	
	logging.debug('%s announced job: %s' % (' '.join(life['name']), job['gist']))

def find_jobs_of_type(gist):
	_jobs = []
	
	for job in [JOBS[i] for i in JOBS]:
		if not job['gist'] == gist:
			continue
		
		_jobs.append(job)
	
	return _jobs

def process_job(job):
	_scores = {}
	for candidate in job['candidates']:
		_score = judgement.judge_job(candidate, job)
		
		logging.debug('%s judged job \'%s\' with score %s' % (' '.join(candidate['name']), job['gist'], _score))
