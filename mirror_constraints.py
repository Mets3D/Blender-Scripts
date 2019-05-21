import bpy

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

def copy_attributes(from_thing, to_thing):
	bad_stuff = ['__doc__', '__module__', '__slots__', 'active', 'bl_rna', 'error_location', 'error_rotation']
	for prop in dir(from_thing):
		if(prop in bad_stuff): continue
		if(hasattr(to_thing, prop)):
			value = getattr(from_thing, prop)
			try:
				setattr(to_thing, prop, value)
			except AttributeError:	# Read Only properties
				continue

for b in bpy.context.selected_pose_bones:
	#TODO: Should also make sure constraints are in the correct order.
	#TODO: Make a name flipping function
	flipped_name = flip_name(b.name)
	opp_b = bpy.context.object.pose.bones.get(flipped_name)
	for c in b.constraints:
		opp_c = opp_b.constraints.get(c.name)
		if(not opp_c): 
			opp_c = opp_b.constraints.new(type=c.type)
		
		if(c.type=='COPY_ROTATION'):
			copy_attributes(c, opp_c)
			
		# Targets
		opp_c.target = c.target
		opp_subtarget = flip_name(c.subtarget)
		opp_c.subtarget = opp_subtarget
		
		# Visibility
		opp_c.mute = c.mute
		
		# Influnce
		opp_c.influence = c.influence
		
		if(c.type=='TRANSFORM'):
			# Source->Destination mapping
				opp_c.map_from = c.map_from
				opp_c.map_to = c.map_to
				
				opp_c.map_to_x_from = c.map_to_x_from
				opp_c.map_to_y_from = c.map_to_y_from
				opp_c.map_to_z_from = c.map_to_z_from
			
			# Spaces
				opp_c.target_space = c.target_space
				opp_c.owner_space = c.owner_space
			
			# Extrapolate
				opp_c.use_motion_extrapolate = c.use_motion_extrapolate
			
			#########################
			###### TRANSFORMS #######
			#########################
			
			###### SOURCES #######
			
			### Source Rotations
			
			# X Rot: same
				opp_c.from_max_x_rot = c.from_max_x_rot
				opp_c.from_min_x_rot = c.from_min_x_rot
			
			# Y Rot: Todo
			
			# Z Rot: flipped and inverted
				opp_c.from_max_z_rot = c.from_min_z_rot * -1
				opp_c.from_min_z_rot = c.from_max_z_rot * -1
			
			### Source Locations (Everything is the same I think)
				opp_c.from_min_x = c.from_min_x
				opp_c.from_max_x = c.from_max_x
				
				opp_c.from_min_y = c.from_min_y
				opp_c.from_max_y = c.from_max_y
				
				opp_c.from_min_z = c.from_min_z
				opp_c.from_max_z = c.from_max_z
			
			###### DESTINATIONS #######
			
			### Destination Rotations
			
			### Destination Rotations when source is Rotation
				if(c.map_from == 'ROTATION'):
					if(c.map_to_x_from == 'X'):		# If the source is X rotation
						# X Rot: same
						opp_c.to_max_x_rot = c.to_max_x_rot
						opp_c.to_min_x_rot = c.to_min_x_rot
						
						# Y Rot: TODO
						
						# Z Rot: TODO
					
					if(c.map_to_x_from == 'Z'):		# If the source is Z rotation
						# X Rot: flipped
						opp_c.to_max_x_rot = c.to_min_x_rot
						opp_c.to_min_x_rot = c.to_max_x_rot
						
						# Y Rot: flipped and inverted
						opp_c.to_max_y_rot = c.to_min_y_rot * -1
						opp_c.to_min_y_rot = c.to_max_y_rot * -1
						
						# Z Rot: flipped and inverted
						opp_c.to_max_z_rot = c.to_min_z_rot * -1
						opp_c.to_min_z_rot = c.to_max_z_rot * -1
				
				### Destination Locations
				
				### Destination Locations when source is Rotation
				if(c.map_from == 'ROTATION'):
					if(c.map_to_x_from == 'X'):		# If the source is X rotation
						# X Loc: inverted
						opp_c.to_min_x = c.to_min_x * -1
						opp_c.to_max_x = c.to_max_x * -1
						
						# Y Loc: same
						opp_c.to_min_y = c.to_min_y
						opp_c.to_max_y = c.to_max_y
						
						# Z Loc: same
						opp_c.to_min_z = c.to_min_z
						opp_c.to_max_z = c.to_max_z
					elif(c.map_to_x_from == 'Z'):	# If the source is Z rotation
						# X Loc: flipped and inverted
						opp_c.to_min_x = c.to_max_x * -1
						opp_c.to_max_x = c.to_min_x * -1
						
						# Y Loc: flipped
						opp_c.to_min_y = c.to_max_y
						opp_c.to_max_y = c.to_min_y
						
						# Z Loc: TODO
						opp_c.to_min_z = c.to_min_z
						opp_c.to_max_z = c.to_max_z
				
				### Destination Locations when source is Location
				if(c.map_from == 'LOCATION'):
					if(c.map_to_x_from == 'X'):		# If the source is X rotation
						# X Loc: inverted
						opp_c.to_min_x = c.to_min_x
						opp_c.to_max_x = c.to_max_x
						
						# Y Loc: same
						opp_c.to_min_y = c.to_min_y
						opp_c.to_max_y = c.to_max_y
						
						# Z Loc: same
						opp_c.to_min_z = c.to_min_z
						opp_c.to_max_z = c.to_max_z
			