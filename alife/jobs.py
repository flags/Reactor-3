#Let's do this the right way...
from globals import *

import life as lfe

#import judgement
#import dialog
#import speech
#import brain
import action

import logging

def get_job(job_id):
	if not job_id in WORLD_INFO['jobs']:
		raise Exception('Job with id \'%s\' does not exist.' % job_id)
	
	return WORLD_INFO['jobs'][job_id]

def get_task(job_id, task_id):
	return get_job(job_id)['tasks'][task_id]

def create_job(creator, name, tier=TIER_WORK, description='Job description needed.'):
	_job = {'id': str(WORLD_INFO['jobid'])}
	_job['name'] = name
	_job['tier'] = tier
	_job['description'] = description
	_job['tasks'] = {}
	_job['workers'] = []
	_job['flags'] = {}
	_job['creator'] = creator['id']
	_job['completed'] = False
	
	WORLD_INFO['jobid'] += 1
	WORLD_INFO['jobs'][_job['id']] = _job
	
	logging.debug('%s created new job: %s' % (' '.join(creator['name']), name))
	
	return _job['id']

def reset_job(job_id):
	_job = get_job(job_id)
	_job['workers'] = []
	_job['completed'] = False
	
	for task in _job['tasks'].values():
		task['completed'] = False
		task['requires'] = _task['_required'][:]
		
	logging.debug('Job with ID \'%s\' reset.' % job_id)

def add_task(job_id, task_id, name, action, description='Task description needed.', requires=[], max_workers=1, delete_on_finish=False):
	_job = get_job(job_id)
	
	_task = {'id': str(task_id)}
	_task['name'] = name
	_task['description'] = description
	_task['action'] = action
	_task['requires'] = requires
	_task['_required'] = []
	_task['max_workers'] = max_workers
	_task['completed'] = False
	
	if delete_on_finish:
		_task['max_workers'] = -1
	else:
		_task['max_workers'] = max_workers
	
	_job['tasks'][str(task_id)] = _task
	
	return str(task_id)

def remove_worker_from_task(job_id, task_id, worker_id):
	_job = get_job(job_id)
	
	if LIFE[worker_id]['task'] == task_id:
		LIFE[worker_id]['task'] = None
		
		logging.debug('Removed worker \'%s\' from task \'%s\' of job \'%s\'.' % (' '.join(LIFE[worker_id]['name']), task_id, worker_id))

def complete_task(life, job_id, task_id):
	_job = get_job(job_id)
	_task = get_task(job_id, task_id)
	
	if _task['max_workers'] == -1:
		life['completed_tasks'].append(task_id)
		life['task'] = None
		
		if not get_next_task(life, life['job']):
			life['completed_jobs'].append(job_id)
		
		return False
	
	_task['completed'] = True
	
	for task in _job['tasks']:
		if task_id in _job['tasks'][task]['requires']:
			_job['tasks'][task]['requires'].remove(task_id)
			_job['tasks'][task]['_required'].append(task_id)
	
	for worker in _job['workers']:
		remove_worker_from_task(job_id, task_id, worker)
	
	logging.debug('Task \'%s\' of job \'%s\' complete.' % (task_id, job_id))

def get_workers_on_task(job_id, task_id):
	_task = get_task(job_id, task_id)
	_workers = []
	
	for worker_id in get_job(job_id)['workers']:
		if LIFE[worker_id]['task'] == task_id:
			_workers.append(worker_id)
	
	return _workers

def get_free_tasks(job_id, local_completed=[]):
	_job = get_job(job_id)
	_free_tasks = []
	
	for task in _job['tasks']:
		if local_completed:
			_req = _job['tasks'][task]['requires'][:]
			
			for completed_task in local_completed:
				if completed_task in _req:
					_req.remove(completed_task)
			
			if _req:
				continue
		else:
			if _job['tasks'][task]['completed'] or _job['tasks'][task]['requires']:
				continue
		
		if not _job['tasks'][task]['max_workers'] == -1 and len(get_workers_on_task(job_id, task)) >= _job['tasks'][task]['max_workers']:
			continue
		
		_free_tasks.append(task)
	
	return _free_tasks

def get_next_task(life, job_id):
	#_job = get_job(job_id)
	
	for task in get_free_tasks(job_id, local_completed=life['completed_tasks']):
		if not task in life['completed_tasks']:
			return task
		
	return None

def join_job(job_id, life_id):
	_job = get_job(job_id)
	_job['workers'].append(life_id)
	
	LIFE[life_id]['jobs'].append(job_id)
	
	logging.debug('%s joined job with ID \'%s\'.' % (' '.join(LIFE[life_id]['name']), job_id))

def alife_has_job(life):
	return life['job']

def work(life):
	if not life['task']:
		return True
	_task = get_task(life['job'], life['task'])
	
	return action.execute_small_script(life, _task['action'])

#def tick(job):
#	if job['tick_callback']:
#		if job['tick_callback']['callback'](**job['tick_callback']['args']):
#			cancel_job(job, completed=True)

#def tick_all_jobs():
#	for job in JOBS.values():
#		tick(job)

#def add_tick_callback(job, callback, **kwargs):
#	job['tick_callback']['callback'] = callback
#	job['tick_callback']['args'] = kwargs

#def add_job_completed_callback(job, callback):
#	job['completed_callback'] = callback
#	
#	logging.debug('Job completed callback set for: %s' % job['gist'])

#def add_leave_job_callback(job, callback):
#	job['leave_job_callback'] = callback
#	
#	logging.debug('Added leave job callback for: %s' % job['gist'])

#def add_task_callback(job, task, callback):
#	job[task]['callback'] = callback
#	
#	logging.debug('Callback set for task \'%s\' in job \'%s\'' % (task, job['gist']))

#def cancel_job(job, completed=False):
#	if completed:
#		job['completed_callback'](job)
#	
#	for worker in [LIFE[i] for i in job['workers']]:
#		worker['job'] = None
#		worker['task'] = None
#		lfe.create_and_update_self_snapshot(worker)
#	
#	del JOBS[job['id']]
#	
#	logging.debug('Job canceled: %s' % job['gist'])

#def process_cancel_if(life, job):
#	for callback in job['cancel_if']:
#		if callback(life):
#			cancel_job(job)
#			return True
#	
#	return False

#def cancel_if(job, callback):
#	job['cancel_if'].append(callback)

#def complete_task(life):
	#life['job']['tasks'].remove(life['task'])
	
	#if not life['job']['tasks']:
		#if not life['job']['id'] in JOBS:
			#logging.error('Job was #%s was deleted already.' % life['job']['id'])
		#else:
			#del JOBS[life['job']['id']]
		
		#logging.debug('Job completed: %s' % life['job']['gist'])
		#life['job']['workers'].remove(life['id'])
		#life['job'] = None
		#life['task'] = None
		#lfe.create_and_update_self_snapshot(life)
	#else:
		#logging.debug('Task \'%s\' for job \'%s\' completed.' % (life['task']['task'], life['job']['gist']))
		#_open_task = find_open_task(life, life['job'])
		
		#if _open_task:
			#take_job(life, life['job'], _open_task)
		#else:
			#if life['job']['leave_job_callback']:
				#life['job']['leave_job_callback'](life)
			
			#life['job']['workers'].remove(life['id'])			
			#life['job'] = None
			#life['task'] = None	
			#lfe.create_and_update_self_snapshot(life)

#def job_has_task(job, task, is_open=True):
	#for _task in job['tasks']:
		#if task == _task['task'] and not _task['workers']:
			#return _task
	
	#return False

#def add_job_factor(job, factor_type, value):
	#_factor = {'type': factor_type,
		#'value': value}
	
	#if factor_type == 'alife':
		#_factor['value'] = value['id']
	
	#job['factors'].append(_factor)
	
	#logging.debug('Added factor to job: %s' % factor_type)

#def add_detail_to_job(job, detail, value):
	#if not detail in job['details']:
		#logging.debug('Added detail to job: %s' % detail)
	
	#job['details'][detail] = value

#def get_job_detail(job, detail):
	#if detail in job['details']:
		#return job['details'][detail]
	
	#return None

#def add_job_task(job, task, required=False, callback=None, depends_on=[]):
	#_task = {'task': task,
		#'workers': [],
		#'required': required,
		#'callback': callback,
		#'depends_on': depends_on}
	#job['tasks'].append(_task)
	
	#logging.debug('Added task to job: %s' % task)

#def add_job_candidate(job, life):
	#job['candidates'].append(life['id'])
	
	#logging.debug('Added candidate to job: %s' % ' '.join(life['name']))

#def is_job_candidate(job, life):
	#if life['id'] in job['candidates']:
		#return True
	
	#return False

#def take_job(life, job, task):
	#if not life['id'] in job['workers']:
		#job['workers'].append(life['id'])
	
	#task['workers'].append(life['id'])
	#life['job'] = job
	#life['task'] = task
	
	#logging.debug('%s joined task \'%s\' in job \'%s\'' % (' '.join(life['name']), task['task'], job['gist']))

#def is_working_job(life, job):
	#if life['id'] in job['workers']:
		#return True
	
	#return False

#def alife_is_factor_of_job(life, job):
	#for factor in job['factors']:
		#if not factor['type'] == 'alife':
			#continue
		
		#if factor['value'] == life['id']:
			#return True
	
	#return False

#def alife_is_factor_of_any_job(life):
	#for job in [JOBS[i] for i in JOBS]:
		#if alife_is_factor_of_job(life, job):
			#return True
	
	#return False

#def announce_job(life, job):
	#speech.announce(life, 'job', job=job)
	
	#logging.debug('%s announced job: %s' % (' '.join(life['name']), job['gist']))

#def find_jobs_of_type(gist):
	#_jobs = []
	
	#for job in [JOBS[i] for i in JOBS]:
		#if not job['gist'] == gist:
			#continue
		
		#_jobs.append(job)
	
	#return _jobs

#def find_open_task(life, job):
	#_task_to_take = None
	
	#for task in job['tasks']:
		##TODO: How many workers are needed?
		#if not task['workers']:
			#if task['depends_on']:
				#if life['task'] and life['task']['task'] == task['depends_on']:
					#return task
			
			#if task['required']:
				#return task
				
			#_task_to_take = task
	
	#return _task_to_take

#def process_job(job):
	#_scores = {}
	#for candidate in job['candidates']:
		#_score = judgement.judge_job(LIFE[candidate], job)
		#_scores[_score] = candidate
		
		#logging.debug('%s judged job \'%s\' with score %s' % (' '.join(LIFE[candidate]['name']), job['gist'], _score))
	
	#job['candidates'].remove(_scores[_scores.keys()[0]])
	
	#_task = find_open_task(LIFE[_scores[_scores.keys()[0]]], job)
	#if _task:
		#take_job(LIFE[_scores[_scores.keys()[0]]], job, _task)
	#else:
		#logging.warning('No open tasks for job: %s' % job['gist'])

#def ask_for_job(life):
	#_target = get_job_detail(life['job'], 'target')
	#if not brain.retrieve_from_memory(life, 'current_job'):
		#brain.store_in_memory(life, 'current_job', life['job']['gist'])
	#else:
		#_old_job = brain.retrieve_from_memory(life, 'current_job')
		#if not _old_job == life['job']['gist']:
			#brain.store_in_memory(life, 'current_job', None)
			#return True
		
		#return False
	
	#_dialog = {'type': 'dialog',
		#'from': life,
		#'enabled': True,
		#'gist': 'jobs'}
	#_dialog = dialog.create_dialog_with(life, _target, _dialog)
	
	#if _dialog:
		#life['dialogs'].append(_dialog)
	
	#return False
