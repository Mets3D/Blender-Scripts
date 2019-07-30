import bpy

# For setting up BBone tangents.
# Before using:
# Make sure all previous TAN- bones are deleted
# Select all face DEF- bones in edit mode.

# If this script becomes often used in the future, it should probably be rewritten. Currently there's some duplicate code for handling bones that are at the tail of bones that don't have any children.
# And we start by duplicating selected bones, which is just kinda weird.
# Instead, all TAN- bones should be created in the same way, probably going through the DEF- bones in a chain by chain manner.

arrow_shape = bpy.data.objects['Shape_Arrow.001']

def find_nearby_bones(search_co, dist):
	# Bruteforce search for bones that are within a given distance of the given coordinates.
	ret = []
	for b in bpy.context.object.data.edit_bones:
		if( (b.head - search_co).length < dist):
			ret.append(b)
	return ret

def create_tangent_bones():
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
			# Start target of current def bone
			def_bone.bbone_handle_type_start = 'TANGENT'
			def_bone.bbone_custom_handle_start = eb
			
			if(not def_bone.parent): continue
			
			if(def_bone.parent.name.startswith("DEF")):
				# End target of parent def bone
				parent_bone = def_bone.parent
				parent_bone.bbone_handle_type_start = 'TANGENT'
				parent_bone.bbone_handle_type_end = 'TANGENT'
				parent_bone.bbone_custom_handle_end = eb
				
				# Set rotation of the TAN- bone so that it's the average between this DEF- bone and its parent.
				def_bone_vec = (def_bone.head - def_bone.tail).normalized()
				parent_bone_vec = (parent_bone.head - parent_bone.tail).normalized()
				tan_eb_vec = (def_bone_vec + parent_bone_vec) * 1/2 *-1
				eb.tail = eb.head + tan_eb_vec * scale
				eb.roll = (def_bone.roll + parent_bone.roll) / 2

			# Check if this bone has a DEF- child
			found = False
			for c in def_bone.children:
				if(c.name.startswith('DEF-')):
					found=True
			if(found): continue
			
			# If not, create a TAN- bone for the tail. 
			# A CTR- bone still has to exist there, so finding that first.
			nearby_bones = find_nearby_bones(def_bone.tail, 0.0005)
			tail_ctr_bones = [b for b in nearby_bones if b.name.startswith('CTR') and not b.name.startswith('CTR2')]
			tail_ctr_bone = None
			if(len(tail_ctr_bones) > 0):
				tail_ctr_bone = tail_ctr_bones[0]
				# Create TAN- bone at this location, with the same rotation as the DEF- bone.
				tail_tan = bpy.context.object.data.edit_bones.new(eb.name.replace('TAN-', 'TAN-Tail-'))
				tail_tan.head = tail_ctr_bone.head
				vector = (def_bone.tail-def_bone.head).normalized()
				tail_tan.tail = tail_tan.head + vector*scale
				tail_tan.bbone_x = tail_tan.bbone_z = 0.001
				tail_tan.parent = tail_ctr_bone
				def_bone.bbone_handle_type_end = 'TANGENT'
				def_bone.bbone_custom_handle_end = tail_tan
				tail_tan.use_deform = False
	
	bpy.ops.armature.select_more()
	bpy.ops.object.mode_set(mode='POSE')
	bpy.ops.pose.constraints_clear()
	for pb in bpy.context.selected_pose_bones:
		pb.custom_shape = arrow_shape
		pb.use_custom_shape_bone_size = False
		pb.custom_shape_scale = 1.5
		pb.bone_group = bpy.context.object.pose.bone_groups.active

create_tangent_bones()