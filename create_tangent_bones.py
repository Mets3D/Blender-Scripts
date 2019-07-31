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
	name = ""
	direction = None
	if(bone_start):
		loc = bone_start.head
		name = bone_start.name.replace("DEF-", "TAN-")
		direction = (bone_start.tail-bone_start.head).normalized()
		if(bone_end):
			bone_end_direction = (bone_end.tail-bone_end.head).normalized()
			direction = (direction + bone_end_direction) * 1/2
	else:
		loc = bone_end.tail
		name = bone_end.name.replace("DEF-", "TAN-Tail-")
		direction = (bone_end.tail-bone_end.head).normalized()

	# Find a parent CTR bone
	nearby_bones = find_nearby_bones(loc, 0.0005)
	ctr_bones = [b for b in nearby_bones if b.name.startswith('CTR') and not b.name.startswith('CTR2')]
	if(len(ctr_bones) == 0): return
	
	ctr_bone = ctr_bones[0]
	tan_bone = bpy.context.object.data.edit_bones.new(name)
	tan_bone.parent = ctr_bone
	tan_bone.head = loc
	tan_bone.tail = tan_bone.head + direction*scale
	tan_bone.bbone_x = tan_bone.bbone_z = 0.001
	
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

def setup_rain_face_rig():
	ebones = bpy.context.selected_editable_bones
	for eb in ebones:
		if(eb.parent not in ebones):
			chain = get_chain(eb, [])
			create_tangent_bones_for_chain(chain)
	
	bpy.ops.armature.select_more()
	bpy.ops.object.mode_set(mode='POSE')
	for pb in bpy.context.selected_pose_bones:
		if(not pb.name.startswith('TAN-')): continue
		pb.custom_shape = arrow_shape
		pb.use_custom_shape_bone_size = False
		pb.custom_shape_scale = 1.5
		pb.bone_group = bpy.context.object.pose.bone_groups.active

setup_rain_face_rig()