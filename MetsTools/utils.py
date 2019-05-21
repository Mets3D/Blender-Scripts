

def flip_name(from_name):
	print("")
	print("flipping: " + from_name)
	# based on BLI_string_flip_side_name in https://developer.blender.org/diffusion/B/browse/master/source/blender/blenlib/intern/string_utils.c
	
	l = len(from_name)	# Number of characters from left to right, that we still care about. At first we care about all of them.
	
	# Handling .### cases
	if("." in from_name):
		# Make sure there are only digits after the last period
		after_last_period = from_name.split(".")[-1]
		before_last_period = from_name.replace("."+after_last_period, "")
		print("before last period: " + before_last_period)
		all_digits = True
		for c in after_last_period:
			if( c not in "0123456789" ):
				all_digits = False
				break
		# If that is so, then we don't care about the characters after this last period.
		if(all_digits):
			print("ends in .###")
			l = len(before_last_period)
	
	# Case: Suffix or prefix R r L l separated by . - _
	name = from_name[:l]
	new_name = name
	separators = ".-_"
	for s in separators:
		# Suffixes
		if(s+"L" == name[-2:]):
			new_name = name[:-1] + 'R'
			break
		if(s+"R" == name[-2:]):
			new_name = name[:-1] + 'L'
			break
			
		if(s+"l" == name[-2:]):
			new_name = name[:-1] + 'r'
			break
		if(s+"r" == name[-2:]):
			new_name = name[:-1] + 'l'
			break
		
		# Prefixes
		if("L"+s == name[:2]):
			new_name = "R" + name[1:]
			break
		if("R"+s == name[:2]):
			new_name = "L" + name[1:]
			break
		
		if("l"+s == name[:2]):
			new_name = "r" + name[1:]
			break
		if("r"+s == name[:2]):
			new_name = "l" + name[1:]
			break
	
	print("new name: " + new_name)
	
	if(new_name != name):
		print("returning " + new_name + from_name[l:])
		return new_name + from_name[l:]
	
	# Case: "left" or "right" with any case found anywhere in the string.
	
	left = ['left', 'Left', 'LEFT']
	right = ['right', 'Right', 'RIGHT']
	
	lists = [left, right, left]	# To get the opposite side, we just get lists[i-1]. No duplicate code, yay!
	
	# Trying to find any left/right string.
	for list_idx in range(1, 3):
		for side_idx, side in enumerate(lists[list_idx]):
			if(side in name):
				# If it occurs more than once, only replace the last occurrence.
				before_last_side = "".join(name.split(side)[:-1])
				after_last_side = name.split(side)[-1]
				opp_side = lists[list_idx-1][side_idx]
				return before_last_side + opp_side + after_last_side + from_name[l:]
	
	# If nothing was found, return the original string.
	return from_name