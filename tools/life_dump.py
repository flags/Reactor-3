#Life Dump

import json
import sys

def dump(filename):
	with open(filename, 'r') as e:
		_life = json.loads(''.join(e.readlines()))
		
		print json.dumps(_life, indent=3)

if __name__ == '__main__':
	if len(sys.argv)>1:
		dump(sys.argv[1])