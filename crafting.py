import life as lfe

import scripting

def get_items_for_dismantle(life):
	return [i for i in life['inventory'].values() if 'CANDISMANTLE' in i['flags']]

def dismantle_item(life, item_id):
	_item = lfe.get_inventory_item(life, item_id)
	
	scripting.execute(_item['flags']['CANDISMANTLE'], owner=life, item=item_id)