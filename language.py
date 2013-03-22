import random

def prettify_string_array(array,max_length):
	"""Returns a human readable string from an array of strings."""
	_string = ''
	
	_i = 0
	for entry in array:
		if len(_string) > max_length:
			_string += ', and %s more.' % (_i+1)
			
			break
		
		if _i == 0:
			_string += entry
		elif 0<_i<len(array)-1:
			_string += ', %s' % entry
		elif _i == len(array)-1:
			_string += ' and %s.' % entry
		
		_i += 1
	
	return _string

def get_name(life):
	if random.randint(0, 1):
		return ' '.join(life['name'])
	else:
		return 'He'
