#This tool was rushed together over the course of an hour or so. Be gentle.

from flask import Flask, render_template, request

import threading
import socket

app = Flask(__name__)
net_lock = threading.Lock()
net_lock.acquire()

class DebugClient(threading.Thread):
	def __init__(self, lock):
		self.lock = lock
		
		self.running = True
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.settimeout(2)
		
		threading.Thread.__init__(self)
		
	def run(self):
		while self.running:
			self.lock.acquire()
			
			try:
				self.socket.connect(('', 3333))
			except:
				continue
			
			self.socket.sendall('Hello, world')
			data = self.socket.recv(1024)
			self.lock.release()
			print 'CONNECTED OK'
		
		self.socket.close()


debug_client = DebugClient(net_lock)
debug_client.start()

def shutdown_server():
	func = request.environ.get('werkzeug.server.shutdown')
	if func is None:
		raise RuntimeError('Not running with the Werkzeug Server')

	func()

def request():
	net_lock.release()
	debug_client.command = 'derp'
	net_lock.acquire()

@app.route('/')
def index():
	request()
	
	return render_template('index.html', life=life)

@app.route('/shutdown')
def shutdown():
	shutdown_server()
	return 'Server shutting down...'

if __name__ == '__main__':
	app.run(debug=True, port=3335)

debug_client.running = False