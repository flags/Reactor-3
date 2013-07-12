#This tool was rushed together over the course of an hour or so. Be gentle.

from flask import Flask, render_template, request

import threading
import socket
import json

app = Flask(__name__)

def request(request, value=None):
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.settimeout(5)
	sock.connect(('127.0.0.1', 3335))
	sock.sendall(json.dumps({'type': 'get', 'what': request, 'value': value}))
	data = json.loads(sock.recv(9048))
	sock.close()
	
	return data

@app.route('/memory/<life_id>')
def memory(life_id):
	memories = request('memory', value=int(life_id))
	
	return render_template('memory.html', life_id=life_id, memories=memories)

@app.route('/life/<life_id>')
def life(life_id):
	life = request('life', value=int(life_id))
	knows = life['know'].values()
	
	return render_template('life.html', life=life, knows=knows)

@app.route('/camp/<camp_id>')
def camp(camp_id):
	camp = request('camp', value=int(camp_id))
	
	return render_template('camp.html', camp=camp)

@app.route('/group/<group_id>')
def group(group_id):
	groups = request('groups')
	group = groups[group_id]
	
	return render_template('group.html', group_id=group_id, group=group)

@app.route('/')
def index():
	groups = request('groups')
	
	life = request('life_list')
	life.sort()
	
	camps = request('camp_list')
	camps.sort()
	
	stats = request('stats')
	
	return render_template('index.html', stats=stats, life=life, groups=groups, camps=camps)

if __name__ == '__main__':
	app.run(debug=True, port=3336)