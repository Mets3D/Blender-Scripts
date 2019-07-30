import bpy

# For setting up BBone tangents.
# Before using:
# Make sure all previous TAN- bones are deleted
# Select all face DEF- bones in edit mode.

def find_nearby_bones(search_co, dist):
	# Bruteforce search for bones that are within a given distance of the given coordinates.
	ret = []
	for b in bpy.context.object.data.edit_bones:
		if( (b.head - search_co).length < dist):
			ret.append(b)
	return ret

# Duplicating all bones
bpy.ops.armature.duplicate_move()

scale=0.01

# Unparenting and disconnecting
bpy.ops.armature.parent_clear(type='CLEAR')
bpy.ops.armature.select_more()

for eb in bpy.context.selected_editable_bones:
	# Clear BBone settings
	eb.bbone_segments 	= 0
	eb.bbone_curveinx 	= 0
	eb.bbone_curveiny 	= 0
	eb.bbone_curveoutx 	= 0
	eb.bbone_curveouty 	= 0
	eb.bbone_rollin 	= 0
	eb.bbone_rollout 	= 0
	
	# Rename bones
	def_name = eb.name.replace(".001", "")
	eb.name = def_name.replace("DEF", "TAN")
	
	# Disable Deform
	eb.use_deform = False
	
	# Finding a nearby CTR bone and parenting to it
	nearby_bones = find_nearby_bones(eb.head, 0.0005)
	ctr_bones = [b for b in nearby_bones if b.name.startswith('CTR') and not b.name.startswith('CTR2')]
	ctr_bone = None
	if(len(ctr_bones) > 0):
		ctr_bone = ctr_bones[0]
		eb.parent = ctr_bone
	
	# Scale down the selected bones by setting them to an absolute scale
	direction = (eb.tail-eb.head).normalized()
	eb.tail = eb.head+direction*scale

	# Set BBone targets
	def_bone = bpy.context.object.data.edit_bones.get(def_name)
	if(def_bone):
		def_bone.bbone_handle_type_start = 'TANGENT'
		def_bone.bbone_handle_type_end = 'TANGENT'
		def_bone.bbone_custom_handle_start = eb
		if(def_bone.parent and def_bone.parent.name.startswith("DEF")):
			parent_bone = def_bone.parent
			parent_bone.bbone_handle_type_start = 'TANGENT'
			parent_bone.bbone_handle_type_end = 'TANGENT'
			parent_bone.bbone_custom_handle_end = eb
			
			# Set rotation so that it's... uh.. good.
			def_bone_vec = (def_bone.head - def_bone.tail).normalized()
			parent_bone_vec = (parent_bone.head - parent_bone.tail).normalized()
			tan_eb_vec = (def_bone_vec + parent_bone_vec) * 1/2 *-1
			eb.tail = eb.head + tan_eb_vec * scale
			eb.roll = (def_bone.roll + parent_bone.roll) / 2
	
bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.constraints_clear()
for pb in bpy.context.selected_pose_bones:
	pb.custom_shape = bpy.data.objects['Shape_Arrow.001']
	pb.use_custom_shape_bone_size = False
	pb.custom_shape_scale = 1.5