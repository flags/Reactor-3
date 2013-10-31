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

def get_job_via_name(name):
	for job_id in WORLD_INFO['jobs']:
		if WORLD_INFO['jobs'][job_id]['name'] == name:
			return job_id
	
	return False

def get_task(job_id, task_id):
	return get_job(job_id)['tasks'][task_id]

def get_creator(job_id):
	return get_job(job_id)['creator']

def create_job(creator, name, gist='', tier=TIER_WORK, description='Job description needed.', ignore_dupe=False, requirements=[], **kwargs):
	if not ignore_dupe and get_job_via_name(name):
		return False
	
	_job = {'id': str(WORLD_INFO['jobid'])}
	_job['name'] = name
	_job['gist'] = gist
	_job['tier'] = tier
	_job['description'] = description
	_job['tasks'] = {}
	_job['workers'] = []
	_job['flags'] = {}
	_job['creator'] = creator['id']
	_job['completed'] = False
	_job['flags'] = kwargs
	_job['cancel_on'] = []
	_job['requirements'] = requirements
	
	WORLD_INFO['jobid'] += 1
	WORLD_INFO['jobs'][_job['id']] = _job
	
	logging.debug('%s created new job: %s' % (' '.join(creator['name']), name))
	
	return _job['id']

def delete_job(job_id):
	_job = get_job(job_id)
	
	for worker in _job['workers']:
		if LIFE[worker]['job'] == job_id:
			LIFE[worker]['job'] = None
			LIFE[worker]['task'] = None
		
		LIFE[worker]['jobs'].remove(job_id)
	
	del WORLD_INFO['jobs'][job_id]

def cancel_on(job_id, action):
	_job = get_job(job_id)
	
	_job['cancel_on'].append(action)

def get_flag(job_id, flag):
	_job = get_job(job_id)
	
	return _job['flags'][flag]

def reset_job(job_id):
	_job = get_job(job_id)
	_job['workers'] = []
	_job['completed'] = False
	
	for task in _job['tasks'].values():
		task['completed'] = False
		task['requires'] = _task['_required'][:]
		
	logging.debug('Job with ID \'%s\' reset.' % job_id)

def add_task(job_id, task_id, name, action, player_action=None, description='Task description needed.', requires=[], max_workers=1, delete_on_finish=False):
	_job = get_job(job_id)
	
	_task = {'id': str(task_id)}
	_task['name'] = name
	_task['description'] = description
	_task['action'] = action
	_task['player_action'] = player_action
	_task['requires'] = requires
	_task['_required'] = []
	_task['max_workers'] = max_workers
	_task['completed'] = False
	
	if delete_on_finish:
		_task['max_workers'] = max_workers
	else:
		_task['max_workers'] = -1
	
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
		_old_task = life['task']
		life['task'] = get_next_task(life, life['job'])
		
		if not life['task']:
			life['job'] = None
			life['completed_jobs'].append(job_id)
			leave_job(job_id, life['id'])

		logging.debug('Task \'%s\' of job \'%s\' completed by %s.' % (task_id, job_id, ' '.join(life['name'])))	
		return False
	
	_task['completed'] = True
	
	for task in _job['tasks']:
		if task_id in _job['tasks'][task]['requires']:
			_job['tasks'][task]['requires'].remove(task_id)
			_job['tasks'][task]['_required'].append(task_id)
	
	for worker in _job['workers']:
		remove_worker_from_task(job_id, task_id, worker)
	
	logging.debug('Task \'%s\' of job \'%s\' completed by %s.' % (task_id, job_id, ' '.join(life['name'])))

def get_workers_on_task(job_id, task_id):
	_task = get_task(job_id, task_id)
	_workers = []
	
	for worker_id in get_job(job_id)['workers']:
		if LIFE[worker_id]['task'] == task_id:
			_workers.append(worker_id)
	
	return _workers

#def meets_job_requirements(life, job_id):
#	_job = get_job(job_id)
#	
#	for req in _job['requirements']:
#		if not action.execute_small_script(life, req):
#			return False
#	
#	return True

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

def has_completed_or_rejected_job(life, job_id):
	if job_id in life['completed_jobs'] or job_id in life['rejected_jobs']:
		return True
	
	return False

def is_candidate(job_id, life_id):
	if job_id in LIFE[life_id]['jobs']:
		return True
	
	return False

def add_job_candidate(job_id, life_id):
	_job = get_job(job_id)
	
	if is_candidate(job_id, life_id):
		raise Exception('\'%s\' is already a candidate for job %s.' % (' '.join(LIFE[life_id]['name']), job_id))
	
	LIFE[life_id]['jobs'].append(job_id)

def join_job(job_id, life_id):
	_job = get_job(job_id)
	
	if life_id in _job['workers']:
		raise Exception('\'%s\' is already a member of job %s.' % (' '.join(LIFE[life_id]['name']), job_id))
	
	_job['workers'].append(life_id)
	LIFE[life_id]['job'] = job_id
	
	logging.debug('%s joined job with ID \'%s\'.' % (' '.join(LIFE[life_id]['name']), job_id))
	
	return job_id

def leave_job(job_id, life_id, reject=False):
	_job = get_job(job_id)
	
	if not life_id in _job['workers']:
		raise Exception('\'%s\' is not a member of job %s.' % (' '.join(LIFE[life_id]['name']), job_id))
	
	_job['workers'].remove(life_id)
	
	if job_id == LIFE[life_id]['job']:
		LIFE[life_id]['job'] = None
	
	if reject:
		reject_job(job_id, life_id)
	
	logging.debug('%s left job with ID \'%s\'.' % (' '.join(LIFE[life_id]['name']), job_id))

def reject_job(job_id, life_id):
	LIFE[life_id]['jobs'].remove(job_id)
	LIFE[life_id]['rejected_jobs'].append(job_id)

def alife_has_job(life):
	return life['job']

def meets_job_requirements(life, job_id):
	for requirement in get_job(job_id)['requirements']:
		if not action.execute_small_script(life, requirement):
			return False
	
	return True

def _work(life):
	if not life['task']:
		return False
	
	_job = get_job(life['job'])
	
	for cancel_on_action in _job['cancel_on']:
		if not action.execute_small_script(life, _task['player_action']):
			delete_job(life['job'])
			return False
	
	_task = get_task(life['job'], life['task'])
	
	if 'player' in life:
		return action.execute_small_script(life, _task['player_action'])
	
	return action.execute_small_script(life, _task['action'])

def work(life):
	if _work(life):
		return complete_task(life, life['job'], life['task'])
	
	return False
