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

def find_or_create_bone(armature, bonename, select=True):
	assert armature.mode=='EDIT', "Armature must be in edit mode"

	bone = armature.data.edit_bones.get(bonename)
	if(not bone):
		bone = armature.data.edit_bones.new(bonename)
	bone.select = select
	return bone

def find_or_create_constraint(pb, ctype, name=None):
	""" Create a constraint on a bone if it doesn't exist yet. 
		If a constraint with the given type already exists, just return that.
		If a name was passed, also make sure the name matches before deeming it a match and returning it.
		pb: Must be a pose bone.
	"""
	for c in pb.constraints:
		if(c.type==ctype):
			if(name):
				if(c.name==name):
					return c
			else:
				return c
	c = pb.constraints.new(type=ctype)
	if(name):
		c.name = name
	return c

def bone_search(armature, search=None, start=None, end=None, edit_bone=False, selected=True):
	""" Convenience function to get iterators for our for loops. """ #TODO: Could use regex.
	bone_list = []
	if(edit_bone):
		bone_list = armature.data.edit_bones
	else:
		bone_list = armature.pose.bones
	
	filtered_list = []
	if(search):
		for b in bone_list:
			if search in b.name:
				if selected:
					if edit_bone:
						if b.select:
							filtered_list.append(b)
					else:
						if b.bone.select:
							filtered_list.append(b)
				else:
					filtered_list.append(b)
	elif(start):
		for b in filtered_list:
			if not b.name.startswith(start):
				filtered_list.remove(b)
	elif(end):
		for b in filtered_list:
			if not b.name.endswith(end):
				filtered_list.remove(b)
	else:
		assert False, "Nothing passed."
	
	return filtered_list

def find_nearby_bones(armature, search_co, dist, ebones=None):
	""" Bruteforce search for bones that are within a given distance of the given coordinates. """
	""" Active object must be an armature. """	# TODO: Let armature be passed, maybe optionally. Do some assert sanity checks.
	""" ebones: Only search in these bones. """
	
	assert armature.mode=='EDIT'	# TODO: Could use data.bones instead so we don't have to be in edit mode?
	ret = []
	if not ebones:
		ebones = armature.data.edit_bones
	
	for eb in ebones:
		if( (eb.head - search_co).length < dist):
			ret.append(eb)
	return ret

def get_bone_chain(bone, ret=[]):
	""" Recursively build a list of the first children. 
		bone: Can be pose/data/edit bone, doesn't matter. """
	ret.append(bone)
	if(len(bone.children) > 0):
		return get_bone_chain(bone.children[0], ret)
	return ret

def flip_name(from_name, only=True, must_change=False):
	# based on BLI_string_flip_side_name in https://developer.blender.org/diffusion/B/browse/master/source/blender/blenlib/intern/string_utils.c
	# If only==True, only replace the first occurrence of a side identifier in the string, eg. "Left_Eyelid.L" would become "Right_Eyelid.L". With only==False, it would instead return "Right_Eyelid.R"
	# if must_change==True, raise an error if the string couldn't be flipped.

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
	
	new_name = from_name[:l]
	
	left = 				['left',  'Left',  'LEFT', 	'.l', 	  '.L', 		'_l', 				'_L',				'-l',	   '-L', 	'l.', 	   'L.',	'l_', 			 'L_', 			  'l-', 	'L-']
	right_placehold = 	['*rgt*', '*Rgt*', '*RGT*', '*dotl*', '*dotL*', 	'*underscorel*', 	'*underscoreL*', 	'*dashl*', '*dashL', '*ldot*', '*Ldot', '*lunderscore*', '*Lunderscore*', '*ldash*','*Ldash*']
	right = 			['right', 'Right', 'RIGHT', '.r', 	  '.R', 		'_r', 				'_R',				'-r',	   '-R', 	'r.', 	   'R.',	'r_', 			 'R_', 			  'r-', 	'R-']
	
	def flip_sides(list_from, list_to, new_name):
		for side_idx, side in enumerate(list_from):
			opp_side = list_to[side_idx]
			if(only):
				# Only look at prefix/suffix.
				if(new_name.startswith(side)):
					new_name = new_name[len(side):]+opp_side
					break
				elif(new_name.endswith(side)):
					new_name = new_name[:-len(side)]+opp_side
					break
			else:
				if("-" not in side and "_" not in side):	# When it comes to searching the middle of a string, sides must Strictly a full word or separated with . otherwise we would catch stuff like "_leg" and turn it into "_reg".
					# Replace all occurences and continue checking for keywords.
					new_name = new_name.replace(side, opp_side)
					continue
		return new_name
	
	new_name = flip_sides(left, right_placehold, new_name)
	new_name = flip_sides(right, left, new_name)
	new_name = flip_sides(right_placehold, right, new_name)
	
	# Re-add trailing digits (.###)
	new_name = new_name + from_name[l:]

	if(must_change):
		assert new_name != from_name, "Failed to flip string: " + from_name
	
	return new_name

def copy_attributes(from_thing, to_thing, skip=[""], recursive=False):
	"""Copy attributes from one thing to another. I guess I just re-implemented shallow and deep copy, which is fine by me."""
	#print("\nCOPYING FROM: " + str(from_thing))
	#print(".... TO: " + str(to_thing))
	
	bad_stuff = skip + ['__doc__', '__module__', '__slots__', 'active', 'bl_rna', 'error_location', 'error_rotation']
	for prop in dir(from_thing):
		if "__" in prop: continue
		if(prop in bad_stuff): continue
		if(hasattr(to_thing, prop)):
			from_value = getattr(from_thing, prop)
			if recursive and type(from_value) not in [str]:
				# Iterables should be copied recursively.
				# Determine if the property is iterable.
				warn = False
				try:
					iter(from_value)
					to_value = getattr(to_thing, prop)
					# The thing we are copying to must therefore be an iterable as well. If this fails though, we should throw a warning.
					warn = True
					iter(to_value)
					count = min(len(to_value), len(from_value))
					for i in range(0, count):
						copy_attributes(from_value[i], to_value[i], skip, recursive)
				except TypeError: # Not iterable.
					if False and warn:
						print("WARNING: Could not copy attributes from iterable to non-iterable field: " + prop + 
							"\nFrom object: " + str(from_thing) + 
							"\nTo object: " + str(to_thing)
						)
			try:
				setattr(to_thing, prop, from_value)
				#print(prop + ": " + str(from_value))
			except AttributeError:	# We ignore read-only properties without a warning.
				continue