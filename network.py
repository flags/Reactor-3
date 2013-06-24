from globals import *

import life as lfe

import threading
import logging
import socket
import json

def parse_packet(packet):
	try:
		_packet = json.loads(packet.strip())
	except:
		logging.error('Debug: Invalid packet.')
		return json.dumps({'type': 'text', 'text': 'Invalid packet from this client.'})
	
	if _packet['type'] == 'get':
		if _packet['what'] == 'stats':
			_stats = {'total_memories': sum([len(l['memory']) for l in LIFE.values()])}
			
			return json.dumps(_stats)
		elif _packet['what'] == 'groups':
			return json.dumps(GROUPS)
		elif _packet['what'] == 'life':
			_life = LIFE[_packet['value']]
			
			_knows = {}
			for entry in _life['know'].values():
				_knows[entry['life']['id']] = {}
				for key in entry:
					if key == 'heard':
						continue
					
					if key == 'life':
						_knows[entry['life']['id']][key] = entry['life']['id']
						continue
					
					_knows[entry['life']['id']][key] = _life['know'][entry['life']['id']][key]
			
			_sent_life = {'name': _life['name'],
				'know': _knows}
			
			return json.dumps(_sent_life)
		elif _packet['what'] == 'memory':
			return json.dumps(LIFE[_packet['value']]['memory'])
		elif _packet['what'] == 'life_list':
			return json.dumps(LIFE.keys())


class DebugHost(threading.Thread):
	def __init__(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.socket.bind((SETTINGS['debug host'], SETTINGS['debug port']))
		self.socket.listen(1)
		self.socket.settimeout(3)
		
		threading.Thread.__init__(self)
	
	def quit(self):
		try:
			self.conn.close()
		except:
			pass
		
		self.socket.close()
		self.socket.shutdown(socket.SHUT_RDWR)
		logging.error('Debug: Quit.')
	
	def run(self):
		logging.debug('DebugHost up.')

		while SETTINGS['running']:
			try:
				self.conn, self.addr = self.socket.accept()
				logging.error('Debug: Connected.')
			except socket.timeout:
				continue
				
			data = self.conn.recv(1024)
			self.conn.sendall(parse_packet(data))
			self.conn.close()