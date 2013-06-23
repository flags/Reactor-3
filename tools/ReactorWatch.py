#This tool was rushed together over the course of an hour or so. Be gentle.

from flask import Flask, render_template

import threading
import socket

app = Flask(__name__)


class DebugClient(threading.Thread):
	def __init__(self, lock):
		self.lock = lock
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		
		threading.Thread.__init__(self)
	
	def run(self):
		_net_lock.acquire()
		self.socket.connect(('', 3333))
		self.socket.sendall('Hello, world')
		data = self.socket.recv(1024)
		self.socket.close()
		_net_lock.release()


@app.route('/')
def index():
	return render_template('index.html', life=life)

if __name__ == '__main__':
	_net_lock = threading.Lock()
	_net_lock.acquire()
	
	try:
		DebugClient(_net_lock).start()
	except socket.error:
		sys.exit(1)
	
	app.run(debug=True)