#Let's do this the right way...
from globals import *

import life as lfe

import judgement
import dialog
import speech
import brain

import logging

def create_job(creator, gist, description='Job description needed.'):
	_job = {'creator': creator}
	_job['gist'] = gist
	_job['description'] = description
	_job['score'] = 0
	_job['completed_callback'] = None
	_job['leave_job_callback'] = None
	_job['tasks'] = []
	_job['factors'] = []
	_job['workers'] = []
	_job['candidates'] = []
	_job['details'] = {}
	_job['id'] = len(JOBS)
	JOBS[_job['id']] = _job
	
	logging.debug('%s created new job: %s' % (' '.join(creator['name']), gist))
	
	return _job

def add_job_completed_callback(job, callback):
	job['completed_callback'] = callback
	
	logging.debug('Job completed callback set for: %s' % job['gist'])

def add_leave_job_callback(job, callback):
	job['leave_job_callback'] = callback
	
	logging.debug('Added leave job callback for: %s' % job['gist'])

def add_task_callback(job, task, callback):
	job[task]['callback'] = callback
	
	logging.debug('Callback set for task \'%s\' in job \'%s\'' % (task, job['gist']))

def cancel_job(job, completed=False):
	if completed:
		job['completed_callback'](job)
	
	for worker in [LIFE[i] for i in job['workers']]:
		worker['job'] = None
		worker['task'] = None
		lfe.create_and_update_self_snapshot(worker)
	
	del JOBS[job['id']]
	
	logging.debug('Job canceled: %s' % job['gist'])

def complete_task(life):
	life['job']['tasks'].remove(life['task'])
	
	if not life['job']['tasks']:
		if not life['job']['id'] in JOBS:
			logging.error('Job was #%s was deleted already.' % life['job']['id'])
		else:
			del JOBS[life['job']['id']]
		
		logging.debug('Job completed: %s' % life['job']['gist'])
		life['job']['workers'].remove(life['id'])
		life['job'] = None
		life['task'] = None
		lfe.create_and_update_self_snapshot(life)
	else:
		logging.debug('Task \'%s\' for job \'%s\' completed.' % (life['task']['task'], life['job']['gist']))
		_open_task = find_open_task(life, life['job'])
		
		if _open_task:
			take_job(life, life['job'], _open_task)
		else:
			if life['job']['leave_job_callback']:
				life['job']['leave_job_callback'](life)
			
			life['job']['workers'].remove(life['id'])			
			life['job'] = None
			life['task'] = None	
			lfe.create_and_update_self_snapshot(life)

def job_has_task(job, task, is_open=True):
	for _task in job['tasks']:
		if task == _task['task'] and not _task['workers']:
			return _task
	
	return False

def add_job_factor(job, factor_type, value):
	_factor = {'type': factor_type,
		'value': value}
	
	if factor_type == 'alife':
		_factor['value'] = value['id']
	
	job['factors'].append(_factor)
	
	logging.debug('Added factor to job: %s' % factor_type)

def add_detail_to_job(job, detail, value):
	if not detail in job['details']:
		logging.debug('Added detail to job: %s' % detail)
	
	job['details'][detail] = value

def get_job_detail(job, detail):
	if detail in job['details']:
		return job['details'][detail]
	
	return None

def add_job_task(job, task, required=False, callback=None, depends_on=[]):
	_task = {'task': task,
		'workers': [],
		'required': required,
		'callback': callback,
		'depends_on': depends_on}
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
	if not life['id'] in job['workers']:
		job['workers'].append(life['id'])
	
	task['workers'].append(life['id'])
	life['job'] = job
	life['task'] = task
	
	logging.debug('%s joined task \'%s\' in job \'%s\'' % (' '.join(life['name']), task['task'], job['gist']))

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

def find_open_task(life, job):
	_task_to_take = None
	
	for task in job['tasks']:
		#TODO: How many workers are needed?
		if not task['workers']:
			if task['depends_on']:
				if life['task'] and life['task']['task'] == task['depends_on']:
					return task
			
			if task['required']:
				return task
				
			_task_to_take = task
	
	return _task_to_take

def process_job(job):
	_scores = {}
	for candidate in job['candidates']:
		_score = judgement.judge_job(LIFE[candidate], job)
		_scores[_score] = candidate
		
		logging.debug('%s judged job \'%s\' with score %s' % (' '.join(LIFE[candidate]['name']), job['gist'], _score))
	
	job['candidates'].remove(_scores[_scores.keys()[0]])
	
	_task = find_open_task(LIFE[_scores[_scores.keys()[0]]], job)
	if _task:
		take_job(LIFE[_scores[_scores.keys()[0]]], job, _task)
	else:
		logging.warning('No open tasks for job: %s' % job['gist'])

def ask_for_job(life):
	_target = get_job_detail(life['job'], 'target')
	if not brain.retrieve_from_memory(life, 'current_job'):
		brain.store_in_memory(life, 'current_job', life['job']['gist'])
	else:
		_old_job = brain.retrieve_from_memory(life, 'current_job')
		if not _old_job == life['job']['gist']:
			brain.store_in_memory(life, 'current_job', None)
			return True
		
		return False
	
	print life['id'],_target
	_dialog = {'type': 'dialog',
		'from': life,
		'enabled': True,
		'gist': 'jobs'}
	_dialog = dialog.create_dialog_with(life, _target, _dialog)
	print _dialog.keys()
	if _dialog:
		life['dialogs'].append(_dialog)
		print 'ADDED'
	
	return False
