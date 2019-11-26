from mets_tools.armature_nodes.bone import BoneData

def spine_bbone_setup(armature):
	""" Set up all controls for the spine. """
	
	assert armature.type=='ARMATURE', "Not an armature."
	assert armature.mode=='EDIT', "Armature must be in edit mode."

	# Align STR bones to the deform bones
	# Align FK bones to the midway point of deform bones
	# Align IK bones to the FK bones.
	# Align some controls to custom positions? Or just don't so this can be done manually after generating.
	# Parent thighs, clavicles and neck to appropriate bones.

	bone_group = "Body: DEF - Spine Deform Bones ###"	# TODO Hardcoded group name, meh.
	group_bone_names = [b.name for b in armature.pose.bones if b.bone_group and b.bone_group.name==bone_group]
	ebones = [db for db in armature.data.edit_bones if db.name in group_bone_names]

	#### CREATING SPINE RIG BASED ON EXISTING DEFORM BONES ####
	bone_count = len(ebones)
	last_fk_bone_name = ""
	for index, def_eb in enumerate(ebones):
		first = index == 0
		last = index == bone_count-1

		### DEF- Deform Bones ###
		def_bd = BoneData(armature, def_eb)
		bone_number = int(def_eb.name[-1])
		print(def_eb.name)
		assert bone_number == index+1, "Bone number should be 1 higher than index " + def_eb.name + " " + str(index)

		stretch_name = def_bd.name.replace("DEF-", "STR-")
		next_stretch_name = stretch_name[:-1] + str(bone_number+1)	# Add one to the number at the end of the bone name.
		
		def_bd.bbone_custom_handle_start = stretch_name
		def_bd.bbone_custom_handle_end = next_stretch_name
		def_bd.bbone_handle_type_start = def_bd.bbone_handle_type_end = 'TANGENT'
		def_bd.segments = 15

		def_bd.bbone_x = def_bd.bbone_z = 0.008
		def_bd.head.x = def_bd.tail.x = 0

		stretch = {
			'rest_length' 	: 0,
			'use_bulge_min' : True,
			'use_bulge_max' : True,
			'bulge_min' 	: 1,
			'bulge_max' 	: 1,
			'target' 		: armature,
			'subtarget' 	: next_stretch_name
		}
		def_bd.constraints.append(('STRETCH_TO', stretch))
		
		### STR- Stretch Controls ###
		def make_stretch_bone(name, final=False):
			str_bd = BoneData()
			str_bd.name = name
			if(final):		# TODO: technically the STR bone should be oriented like TAN- bones, so these should share code?
				str_bd.head = def_bd.tail
				str_bd.tail = str_bd.head + Vector((0, 0, 0.02))
			else:
				str_bd.head = def_bd.head
				str_bd.tail = def_bd.tail
				str_bd.length = 0.02
			str_bd.bbone_x = str_bd.bbone_z = 0.02
			str_bd.bone_group = armature.pose.bone_groups.get("Body: STR - Stretch Controls")	# TODO: safe_create_bone_group()
			str_bd.custom_shape = sphere_shape
			str_bd.custom_shape_scale = 0.5
			return str_bd
		
		str_bd = make_stretch_bone(stretch_name)

		# First deform bone should be parented to its STR- bone.
		if(first):
			def_bd.parent = str_bd.name
		
		### FK- Controls ###
		fk_bd = None
		fk_name = def_bd.name.replace("DEF-", "FK-")
		if(True): #not last):	# Last DEF- bone shouldn't have an FK control.
			fk_bd = BoneData()
			fk_bd.name = fk_name
			last_fk_bone_name = fk_name
			#fk_bd.head = def_bd.head + (def_bd.tail-def_bd.head)/2	# Place the FK bone at the midpoint of the deform bone.
			fk_bd.head = def_bd.head
			fk_bd.tail = fk_bd.head + Vector((0, 0, 0.01))
			fk_bd.bbone_x = fk_bd.bbone_z = 0.03
			fk_bd.custom_shape = fk_shape
			fk_bd.parent = fk_name[:-1] + str(bone_number-1)
			fk_bd.bone_group = armature.pose.bone_groups.get("Body: Main FK Controls")	# TODO: safe_create_bone_group()
			fk_bd.custom_shape_scale = 2
		
		# Parent STR- to FK-
		if(first):	# First STR should be parented to the hips, not FK spine.
			str_bd.parent = 'MSTR-Hips'
		else:
			str_bd.parent = fk_name[:-1] + str(bone_number-1)
			# Last deform bone needs an STR- bone at its tail, not only its head.
			if(last):
				final_str = make_stretch_bone(next_stretch_name, final=True)
				final_str.parent = str_bd.parent
	
	BoneData.create_all_bones(armature)
	
	# Connect rest of the rig to this thing - This feels hacky.
	bpy.ops.object.mode_set(mode='EDIT')
	clavicle_l = armature.data.edit_bones.get("MSTR-Clavicle.L")
	clavicle_r = armature.data.edit_bones.get("MSTR-Clavicle.R")
	neck = armature.data.edit_bones.get("FK-Neck")
	adjuster = armature.data.edit_bones.get("DEF-COR-Armpit.L")
	clav_parent = armature.data.edit_bones.get(last_fk_bone_name)
	clavicle_l.parent = clavicle_r.parent = neck.parent = adjuster.parent = clav_parent