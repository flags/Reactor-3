import graphics as gfx
import life as lfe

import scripting
import numbers
import items


def get_items_for_crafting(life):
	return [i for i in life['inventory'] if 'craft' in items.get_item_from_uid(i)]

def get_recipe_difficulty(life, item, recipe):
	_difficulty = 0
	
	for skill in recipe['difficulty']:
		if skill in life['stats']:
			_difficulty += recipe['difficulty'][skill]-life['stats'][skill]
	
	return _difficulty

#TODO: stub
def meets_requirements(life, requirements):
	return True

def perform_recipe(life, item, recipe):
	lfe.add_action(life, {'action': 'craft',
	                      'item_uid': item['uid'],
	                      'recipe_id': item['craft'].index(recipe)},
	               99999,
	               delay=recipe['time'])

def execute_recipe(life, item, recipe):
	_difficulty = get_recipe_difficulty(life, item, recipe)
	_dice_percentage = numbers.roll(2, 5)/(10.0+_difficulty)
	
	if _dice_percentage >= .75:
		_recipe_quality = 'success'
	elif _dice_percentage >= .5:
		_recipe_quality = 'partial_success'
	else:
		_recipe_quality = 'failure'
	
	if recipe['type'] == 'create_item':
		for create_item in recipe['create_item']:
			if not _recipe_quality in recipe['create_item'][create_item]:
				continue
			
			for i in range(recipe['create_item'][create_item][_recipe_quality]['amount']):
				_created_item = items.create_item(create_item)
				lfe.add_item_to_inventory(life, _created_item)
	
	if _recipe_quality in recipe['strings']:
		gfx.message(recipe['strings'][_recipe_quality])
	else:
		gfx.message('You finish crafting.')
