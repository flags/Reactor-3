from globals import *

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
		pass


class DebugHost(threading.Thread):
	def __init__(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.bind((SETTINGS['debug host'], SETTINGS['debug port']))
		self.socket.listen(1)
		self.socket.settimeout(3)
		
		threading.Thread.__init__(self)
	
	def run(self):
		logging.debug('DebugHost up.')

		while SETTINGS['running']:
			try:
				self.conn, self.addr = self.socket.accept()
				logging.error('Debug: Connected.')
			except socket.timeout:
				logging.error('Debug: Timeout.')
				break
				
			data = self.conn.recv(1024)
			self.conn.sendall(data)
			self.conn.close()