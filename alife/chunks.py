import life as lfe

import time

def find_best_chunk(life):
	_interesting_chunks = {}
	
	for chunk_key in life['known_chunks']:
		_chunk = life['known_chunks'][chunk_key]
		
		if _chunk['last_visited'] == 0 or time.time()-_chunk['last_visited']>=900:
			_interesting_chunks[chunk_key] = life['known_chunks'][chunk_key]
	
	_current_known_chunk = lfe.get_current_known_chunk(life)
	if _current_known_chunk:
		_initial_score = _current_known_chunk['score']
	else:
		_initial_score = 0
	
	_best_chunk = {'score': _initial_score, 'chunk_key': None}
	for chunk_key in _interesting_chunks:
		chunk = _interesting_chunks[chunk_key]
		
		if chunk['score']>_best_chunk['score']:
			_best_chunk['score'] = chunk['score']
			_best_chunk['chunk_key'] = chunk_key
		
	if not _best_chunk['chunk_key']:
		return False
	
	return _best_chunk['chunk_key']
