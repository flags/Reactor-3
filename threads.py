from globals import *

import threading

def register_worker(thread):
	WORKER_THREADS.append(thread)

def unregister_worker(thread):
	WORKER_THREADS.remove(thread)


class Worker(threading.Thread):
	def __init__(self, jobs):
		self.jobs = jobs
		
		threading.Thread.__init__(self)
		register_worker(self)
	
	def run(self):
		for job in self.jobs:
			job()
		
		unregister_worker(self)


def create_worker(jobs):
	return Worker(jobs).start()
