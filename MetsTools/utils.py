# Collection of functions that are either used by other parts of the addon, or random code snippets that I wanted to include but aren't actually used.

def assign_object_and_material_ids(start=1):
	counter = start

	for o in bpy.context.selected_objects:
		if(o.type=='MESH'):
			o.pass_index = counter
			counter = counter + 1

	counter = start
	for m in bpy.data.materials:
		m.pass_index = counter
		counter = counter + 1

def connect_parent_bones():
	# If the active object is an Armature
	# For each bone
	# If there is only one child
	# Move the tail to the child's head
	# Set Child's Connected to True

	armature = bpy.context.object
	if(armature.type != 'ARMATURE'): return
	else:
		bpy.ops.object.mode_set(mode="EDIT")
		for b in armature.data.edit_bones:
			if(len(b.children) == 1):
				b.tail = b.children[0].head
				#b.children[0].use_connect = True

def uniform_scale():
	for o in bpy.context.selected_objects:
		o.dimensions = [1, 1, 1]
		o.scale = [min(o.scale), min(o.scale), min(o.scale)]

def flip_name(from_name):
	# based on BLI_string_flip_side_name in https://developer.blender.org/diffusion/B/browse/master/source/blender/blenlib/intern/string_utils.c
	
	l = len(from_name)	# Number of characters from left to right, that we still care about. At first we care about all of them.
	
	# Handling .### cases
	if("." in from_name):
		# Make sure there are only digits after the last period
		after_last_period = from_name.split(".")[-1]
		before_last_period = from_name.replace("."+after_last_period, "")
		all_digits = True
		for c in after_last_period:
			if( c not in "0123456789" ):
				all_digits = False
				break
		# If that is so, then we don't care about the characters after this last period.
		if(all_digits):
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
	
	if(new_name != name):
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