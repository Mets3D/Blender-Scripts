import bpy

# For setting up BBone tangents.
# Before using:
# Make sure all previous TAN- bones are deleted
# Select all face DEF- bones in edit mode.

# If this script becomes often used in the future, it should probably be rewritten. Currently there's some duplicate code for handling bones that are at the tail of bones that don't have any children.
# And we start by duplicating selected bones, which is just kinda weird.
# Instead, all TAN- bones should be created in the same way, probably going through the DEF- bones in a chain by chain manner.

arrow_shape = bpy.data.objects['Shape_Arrow.001']
scale=0.01

def safe_create_bone(bonename):
	bone = bpy.context.object.data.edit_bones.get(bonename)
	if(not bone):
		bone = bpy.context.object.data.edit_bones.new(bonename)
	return bone

def find_nearby_bones(search_co, dist):
	# Bruteforce search for bones that are within a given distance of the given coordinates.
	ret = []
	for b in bpy.context.object.data.edit_bones:
		if( (b.head - search_co).length < dist):
			ret.append(b)
	return ret

def get_chain(bone, ret=[]):
	""" Recursively build a list of the first children. """
	ret.append(bone)
	if(len(bone.children) > 0):
		return get_chain(bone.children[0], ret)
	return ret

def create_tangent_bone(bone_start=None, bone_end=None):
	# Create a bone at the head of the start bone. (We assume the head of the start bone and the tail of the end bone are in the same place)
	# Place the tail such that this bone's orientation is the average of the start and end bones' orientations.
	# Assign arbitrary bone length, bbone scale, bone shape.
	# bone_start: The bone for which this tangent bone should be the start handle of.
	# bone_end: The bone for which this tangent bone should be the end handle of.
	# Usually bone_start.parent==bone_end

	assert bone_start or bone_end, "No bones passed for create_tangent_bone()"

	loc = None
	tan_name = ""
	direction = None
	pos_aim = None
	neg_aim = None
	roll = 0
	if(bone_start):	# If bone_start is passed
		loc = bone_start.head
		tan_name = bone_start.name.replace("DEF-", "TAN-")
		direction = (bone_start.tail-bone_start.head).normalized()
		roll = bone_start.roll

		# Finding neighbor CTR bone towards end of the bone chain.
		nearby_bones = find_nearby_bones(bone_start.tail, 0.0005)
		ctr_bones = [b for b in nearby_bones if b.name.startswith('CTR-') and not b.name.startswith('CTR-P-') and not b.name.startswith('CTR-CONST-')]
		if(len(ctr_bones) > 0):
			pos_aim = ctr_bones[0]
	
		if(bone_end):	# If both bone_start and bone_end are passed
			bone_end_direction = (bone_end.tail-bone_end.head).normalized()
			direction = (direction + bone_end_direction) * 1/2
	else:	# If only bone_end is passed
		loc = bone_end.tail
		tan_name = bone_end.name.replace("DEF-", "TAN-Tail-")
		direction = (bone_end.tail-bone_end.head).normalized()
		roll = bone_end.roll
	
	if(bone_end): # If bone_end is passed, we want to find the neighbor towards the beginning of the chain.
		nearby_bones = find_nearby_bones(bone_end.head, 0.0005)
		ctr_bones = [b for b in nearby_bones if b.name.startswith('CTR-') and not b.name.startswith('CTR-P-') and not b.name.startswith('CTR-CONST-')]
		if(len(ctr_bones) > 0):
			neg_aim = ctr_bones[0]

	# Find a parent CTR bone
	nearby_bones = find_nearby_bones(loc, 0.0005)
	ctr_bones = [b for b in nearby_bones if b.name.startswith('CTR-') and not b.name.startswith('CTR-P-') and not b.name.startswith('CTR-CONST-')]
	if(len(ctr_bones) == 0): return
	
	ctr_bone = ctr_bones[0]
	if(ctr_bone):
		user_ctr_node = safe_create_bone(ctr_bone.name.replace("CTR-", "Node_UserRotation_CTR-"))
		user_ctr_node.head = ctr_bone.head
		user_ctr_node.tail = ctr_bone.tail
		user_ctr_node.roll = ctr_bone.roll
		user_ctr_node.bbone_x = user_ctr_node.bbone_z = 0.001
		user_ctr_node.use_deform = False

		tan_bone = safe_create_bone(tan_name)
		aim_bone = safe_create_bone(tan_name.replace("TAN-", "AIM-TAN-"))
		tan_bone.parent = aim_bone
		aim_bone.parent = ctr_bone
		if(pos_aim):
			aim_bone['pos_aim'] = pos_aim.name
		if(neg_aim):
			aim_bone['neg_aim'] = neg_aim.name
		aim_bone['copy_loc'] = ctr_bone.name
		tan_bone.head = aim_bone.head = loc
		tan_bone.tail = aim_bone.tail = tan_bone.head + direction*scale
		tan_bone.bbone_x = tan_bone.bbone_z = aim_bone.bbone_x = aim_bone.bbone_z = 0.001
		tan_bone.roll = aim_bone.roll = roll
		tan_bone.use_deform = aim_bone.use_deform = False

		user_tan_node = safe_create_bone(tan_bone.name.replace("TAN-", "Node_UserRotation_TAN-"))
		user_tan_node.head = tan_bone.head
		user_tan_node.tail = tan_bone.tail
		user_tan_node.roll = tan_bone.roll
		user_tan_node.bbone_x = user_tan_node.bbone_z = 0.001
		user_tan_node.use_deform = False
		user_tan_node['parent'] = user_ctr_node.name
	
	return tan_bone

def create_tangent_bones_for_chain(chain):
	for i, def_bone in enumerate(chain):
		if(i==0):
			# Tangent control for the first bone in each chain needs to be created based on only start bone.
			def_bone.bbone_custom_handle_start = create_tangent_bone(bone_start=chain[0], bone_end=None)
			if(len(chain)==1):
				# If there is exactly one bone in the chain, it's both the first and last bone, so we also need to create its tail tangent here.
				def_bone.bbone_custom_handle_end = create_tangent_bone(bone_start=None, bone_end=chain[0])
			continue

		chain[i].bbone_custom_handle_start = chain[i-1].bbone_custom_handle_end = create_tangent_bone(chain[i], chain[i-1])

		if(i==len(chain)-1):
			# Tangent control for the last bone in each chain needs to be created based on only end bone.
			chain[i].bbone_custom_handle_end = create_tangent_bone(bone_start=None, bone_end=chain[i])
			continue

def face_tangent_setup():
	ebones = bpy.context.selected_editable_bones
	for eb in ebones:
		if(eb.parent not in ebones
		or eb.parent.children[0] != eb):	# This is not the 1st child of the bone, so it won't be included in the chain returned by get_chain()  # Handle this as a separate chain - TODO: First start tangent bone is going to be a duplicate in this case I think. We should detect if the TAN bone exists before we create them, and if they do, just offset them accordingly if possible.
			chain = get_chain(eb, [])
			create_tangent_bones_for_chain(chain)
	
	def safe_create_constraint(pb, ctype, name=None):
		# Only create a constraint on this bone of a given type if a bone with that type or name does not already exist.
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

	bpy.ops.armature.select_more()
	bpy.ops.object.mode_set(mode='POSE')
	for pb in bpy.context.object.pose.bones:
		if("Node_UserRotation_CTR-" in pb.name):
			copy_rotation = safe_create_constraint(pb, 'COPY_ROTATION')
			copy_rotation.target = bpy.context.object
			copy_rotation.subtarget = pb.name.replace("Node_UserRotation_CTR-", "CTR-")
			copy_rotation.target_space = copy_rotation.owner_space = 'LOCAL'
		if("Node_UserRotation_TAN-" in pb.name):
			pb.custom_shape = arrow_shape
			pb.use_custom_shape_bone_size = False
			armature_const = safe_create_constraint(pb, 'ARMATURE')
			target = armature_const.targets.new()
			target.target = bpy.context.object
			db = bpy.context.object.data.bones.get(pb.name)
			target.subtarget = db['parent']
		
		if('TAN-' not in pb.name): continue
		
		pb.custom_shape = arrow_shape
		pb.use_custom_shape_bone_size = False
		if(pb.name.startswith('TAN')):
			pb.bone_group = bpy.context.object.pose.bone_groups.get('Face: TAN - BBone Tangent Handle Helpers')
			pb.custom_shape_scale = 1.4
			copy_rotation = safe_create_constraint(pb, 'COPY_ROTATION')
			copy_rotation.target = bpy.context.object
			copy_rotation.subtarget = pb.name.replace("TAN-", "Node_UserRotation_TAN-")
			copy_rotation.target_space = copy_rotation.owner_space = 'LOCAL'
			copy_rotation.use_offset = True

		if(pb.name.startswith('AIM')):
			pb.bone_group = bpy.context.object.pose.bone_groups.get('Face: TAN-AIM - BBone Automatic Handle Helpers')
			pb.custom_shape_scale = 1.6
			db = bpy.context.object.data.bones.get(pb.name)
			copy_location = safe_create_constraint(pb, 'COPY_LOCATION')
			copy_location.target = bpy.context.object
			copy_location.subtarget = db['copy_loc']
			if('pos_aim' in db):
				damped_pos = safe_create_constraint(pb, 'DAMPED_TRACK', "Damped Track +Y")
				damped_pos.target = bpy.context.object
				damped_pos.subtarget = db['pos_aim']
				damped_pos.track_axis = 'TRACK_Y'
			if('neg_aim' in db):
				damped_neg = safe_create_constraint(pb, 'DAMPED_TRACK', "Damped Track -Y")
				damped_neg.target = bpy.context.object
				damped_neg.subtarget = db['neg_aim']
				damped_neg.track_axis = 'TRACK_NEGATIVE_Y'
				if('pos_aim' in db):
					damped_neg.influence = 0.5

face_tangent_setup()
#Todo: Recalc global +Y axis.