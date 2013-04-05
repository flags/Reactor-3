#Let's do this the right way...
from globals import *

import judgement
import speech

import logging

def create_job(creator, gist):
	_job = {'creator': creator}
	_job['gist'] = gist
	_job['score'] = 0
	_job['callback'] = None
	_job['tasks'] = []
	_job['factors'] = []
	_job['workers'] = []
	_job['candidates'] = []
	_job['id'] = len(JOBS)
	JOBS[_job['id']] = _job
	
	logging.debug('%s created new job: %s' % (' '.join(creator['name']), gist))
	
	return _job

def add_job_callback(job, callback):
	job['callback'] = callback
	
	logging.debug('Job callback set for: %s' % job['gist'])

def add_task_callback(job, task, callback):
	job[task]['callback'] = callback
	
	logging.debug('Callback set for task \'%s\' in job \'%s\'' % (task, job['gist']))

def complete_task(life):
	life['job']['tasks'].remove(life['task'])	
	life['job']['workers'].remove(life['id'])
	
	if not life['job']['tasks']:
		del JOBS[life['job']['id']]
		
		logging.debug('Job completed: %s' % life['job']['gist'])
	else:
		logging.debug('Task \'%s\' for job \'%s\' completed.' % (life['task']['task'], life['job']['gist']))

def add_job_factor(job, factor_type, value):
	_factor = {'type': factor_type,
		'value': value}
	
	if factor_type == 'alife':
		_factor['value'] = value['id']
	
	job['factors'].append(_factor)
	
	logging.debug('Added factor to job: %s' % factor_type)

def add_job_task(job, task, required=False, callback=None):
	_task = {'task': task,
		'workers': [],
		'required': required,
		'callback': callback}
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
	
	life['job'] = job
	life['task'] = _task
	
	logging.debug('%s joined task \'%s\' in job \'%s\'' % (' '.join(life['name']), task, job['gist']))

def is_working_job(life, job):
	if life['id'] in job['workers']:
		return True
	
	return False

def alife_is_factor_of_job(life, job):
	for factor in job['factors']:
		if not factor['type'] == 'alife':
			continue
		
		if factor['value'] == life['id']:
			return True
	
	return False

def alife_is_factor_of_any_job(life):
	for job in [JOBS[i] for i in JOBS]:
		if alife_is_factor_of_job(life, job):
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
		_score = judgement.judge_job(LIFE[candidate], job)
		_scores[_score] = LIFE[candidate]
		
		logging.debug('%s judged job \'%s\' with score %s' % (' '.join(LIFE[candidate]['name']), job['gist'], _score))
	
	take_job(_scores[_scores.keys()[0]], job, 'disarm')
