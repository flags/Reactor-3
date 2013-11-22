Programming Style Guide
-----------------------
A quick note: Throughout development my programming style changed somewhat, so you will see code that does not follow the rules below. All new code obeys these rules.

**This is not a primer on writing effective Python. I am also not a World Famous Superstar Master Python Coder.**

* Use tabs for line indents. Spaces can be used AFTER tabs to help improve readability or for stylistic reasons if needed.
* Variable names should be prefixed with an underscore (`_chunk_key`) if they are defined outside of a `for` loop. Variables used to iterate through lists/are created in the for loop's definition should omit the underscore. Arguments should never start with an underscore unless keyword arguments (`kwargs`) are expected to clash with them.

Abusing Lambdas
-------------
Throughout the code you'll see opportunites to filter results of certain functions by passing a function to keyword argument `filter_if`. However, `filter_if` is usually only called with one argument, rendering the majority of possible filters that need extra arguments completely useless. Instead of filtering the results after they are returned, we can pack the variables we need to access later inside the lambda's definition.

	def manage_combat(life, group_id):
		if get_stage(life, group_id) == STAGE_RAIDING:
			prepare_for_raid(life, group_id)
			return False
		
		for known_group_id in life['known_groups']:
			if group_id == known_group_id:
				continue
			
			if not get_group_memory(life, known_group_id, 'alignment') == 'hostile':
				announce(life, group_id, 'inform_of_known_group', group_id=known_group_id,
						 filter_if=lambda alife: group_exists(alife, known_group_id))
				
				_known_group_members = get_group_memory(life, known_group_id, 'members')

In the above example we can see that `known_group_id` is created in the local scope, but can still be referenced and used inside of the lambda when it is called later. Another example, this time showing an entire `life` structure being passed:

	announce(life, group_id, 'combat_ready', ignore_if_said_in_last=1000, filter_if=lambda alife: brain.get_alife_flag(life, alife['id'], 'combat_ready'))

Note that the lambda's argument was renamed to `alife` to prevent conflicts with `life`.
