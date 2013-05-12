ALife cases:

	alife_camp.py
		Do we even want to help other ALife find the founder?
		Who do we think the founder is?
		Watch over camp
		
	damage.py
		Fix language output
		Blunt weapons
		Explosives
		Melee (?)
		
	judgement.py
		Placeholder: ALife now view someone positively just by saying hello to them (no response needed)
			This is just to help ju
	
	Conversations:
		Nothing is conveyed to the ALife/Player. Needs: trust, friendly/hostile actions
		When letting the player answer, only pick one response to show from multiple ones of the same gist.
		When told about a location, add to map
	
	Likes/Dislikes:
		Each ALife will have a set of likes/dislikes based on gists. These are measured in a float from 0.0 to 1.0.
			response['like'] *= life['likes'][gist]
