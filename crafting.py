import life as lfe

import scripting
import items

def get_items_for_dismantle(life):
	return [i for i in life['inventory'] if 'CANDISMANTLE' in items.get_item_from_uid(i)['flags']]

def dismantle_item(life, item_id):
	_item = lfe.get_inventory_item(life, item_id)
	
	scripting.execute(_item['flags']['CANDISMANTLE'], owner=life, item_uid=item_id)