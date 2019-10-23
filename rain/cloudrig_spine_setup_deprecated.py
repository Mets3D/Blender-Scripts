# NOTE: Most of this is probably stupid. This code was never used or even tested. It was just an idea. I still like the idea though, but the execution could probably be better.
class BoneData:
	""" Container and creator of bones. """
	instances = []	# To let the class keep track of its instances.

	@classmethod
	def get_instance(cls, name):
		""" Find a BoneData instance by name, if it exists. """
		for bd in cls.instances:
			if(bd.name == name):
				return bd
		return None

	def __init__(self, armature=None, edit_bone=None):
		self.__class__.instances.append(self)
		self.constraints = []	# List of (Type, attribs{}) tuples where attribs{} is a dictionary with the attributes of the constraint. I'm too lazy to implement a container for every constraint type...
		self.name = "Bone"
		self.head = Vector((0,0,0))
		self.tail = Vector((0,0,0))
		self.roll = 0
		self.rotation_mode = 'QUATERNION'
		self.bbone_curveinx = 0
		self.bbone_curveiny = 0
		self.bbone_curveoutx = 0
		self.bbone_curveouty = 0
		self.bbone_handle_type_start = "AUTO"
		self.bbone_handle_type_end = "AUTO"
		self.bbone_easein = 0
		self.bbone_easeout = 0
		self.bbone_scaleinx = 0
		self.bbone_scaleiny = 0
		self.bbone_scaleoutx = 0
		self.bbone_scaleouty = 0
		self.segments = 1
		self.bbone_x = 0.1
		self.bbone_z = 0.1
		self.bone_group = None
		self.custom_shape = None   # Object ID?
		self.custom_shape_scale = 1.0
		self.custom_shape_transform = None # Bone name
		self.use_custom_shape_bone_size = False
		self.use_endroll_as_inroll = False
		self.use_connect = False
		self.use_deform = False
		self.use_inherit_rotation = True
		self.use_inherit_scale = True
		self.use_local_location = True
		self.use_envelope_multiply = False
		self.use_relative_parent = False

		# We don't want to store a real Bone ID because we want to be able to set the parent before the parent was really created. So this is either a String or a BoneData instance.
		self.parent = None
		self.bbone_custom_handle_start = None
		self.bbone_custom_handle_end = None

		if(armature and edit_bone):
			#print("reading BoneData from: " +edit_bone.name)
			self.read_data(armature, edit_bone)

	# TODO: Reading and writing shit is an absolute fucking mess, because I wasn't prepared for how much of an absolute fucking mess the python API for bones was.

	def read_data(self, armature, edit_bone):
		my_dict = self.__dict__
		eb_attribs = []
		for attr in my_dict.keys():
			if(hasattr(edit_bone, attr)):
				eb_attribs.append(attr)
				setattr( self, attr, getattr(edit_bone, attr) )
		#print("Read BoneData: " + self.name)
		
		# If this bone has a pose bone, also read its constraints.
		
		pose_bone = armature.pose.bones.get(edit_bone.name)
		for attr in my_dict.keys():
			if( hasattr(pose_bone, attr) 
			and attr not in eb_attribs
			and attr not in ['constraints'] ):
				setattr( self, attr, getattr(pose_bone, attr) )
		if(pose_bone):
			for c in pose_bone.constraints:
				constraint_data = (c.type, {})

				for attr in dir(c):
					if("__" in attr): continue
					if(attr in ['bl_rna', 'type', 'rna_type', 'error_location', 'error_rotation', 'is_proxy_local', 'is_valid']): continue
					constraint_data[1][attr] = getattr(c, attr)

				self.constraints.append(constraint_data)

	def write_edit_data(self, armature, edit_bone):
		# This can strictly only be done in edit mode, and it's also important that the parent exists.
		# This does NOT handle constraints or any other pose bone information, since we can't assume that a pose bone exists yet, since those only get initialized when leaving edit mode.
		
		#print("")
		#print("Writing data to bone: " + edit_bone.name)
		#print("From data: " + self.name)

		my_dict = self.__dict__
		# Edit bone data...
		for attr in my_dict.keys():
			if(hasattr(edit_bone, attr)):
				if(attr in ['parent', 'bbone_custom_handle_start', 'bbone_custom_handle_end']):
					self_value = self.__dict__[attr]
					real_bone = None
					if(type(self_value) == str):
						real_bone = armature.data.edit_bones.get(self_value)
					elif(type(self_value) == BoneData):
						# If the target doesn't exist yet, create it.
						real_bone = find_or_create_bone(armature, self_value.name)
					elif(type(self_value) == bpy.types.Bone):
						real_bone = armature.data.edit_bones.get(self_value.name)
					elif(type(self_value) == bpy.types.EditBone):
						real_bone = self_value
					
					if(real_bone):
						setattr(edit_bone, attr, real_bone)
				else:
					setattr(edit_bone, attr, my_dict[attr])
		
		#print("Wrote data to bone: " + edit_bone.name)

	def write_pose_data(self, armature, pose_bone):
		# This should be called in pose mode to make sure the pose bone information is up to date with changes that may have been made in edit mode. And that the pose bone even exists to begin wtih.
		
		data_bone = armature.data.bones.get(pose_bone.name)

		my_dict = self.__dict__

		# Pose bone data...
		for attr in my_dict.keys():
			if(hasattr(pose_bone, attr)):
				if(attr in ['constraints', 'head', 'tail', 'parent', 'length', 'use_connect']): continue
				if('bbone' in attr): continue
				print("")
				print(attr)
				value = my_dict[attr]
				print("FUCKING REEE " + str(my_dict[attr]))
				if(attr in ['custom_shape_transform'] and my_dict[attr]):
					continue
					value = armature.pose.bones.get(my_dict[attr])
				setattr(pose_bone, attr, value)

		# Data bone data...
		for attr in my_dict.keys():
			if(hasattr(data_bone, attr)):
				value = my_dict[attr]
				if(attr in ['constraints', 'head', 'tail', 'parent', 'length', 'use_connect']): continue
				if(attr in ['bbone_custom_handle_start', 'bbone_custom_handle_end']):
					if(type(value)==str):
						value = armature.data.bones.get(value)
				setattr(data_bone, attr, value)
		
		for cd in self.constraints:
			name = cd[1]['name'] if 'name' in cd[1] else None
			c = find_or_create_constraint(pose_bone, cd[0], name)
			for attr in cd[1].keys():
				if(hasattr(c, attr)):
					setattr(c, attr, cd[1][attr])

	def create_bone(self, armature):
		# Create a single bone and its constraints. Needs to switch between object modes.
		armature.select_set(True)
		bpy.context.view_layer.objects.active = armature

		bpy.ops.object.mode_set(mode='EDIT')
		edit_bone = find_or_create_bone(armature, self.name)
		self.write_data(edit_bone)

		bpy.ops.object.mode_set(mode='POSE')
		pose_bone = armature.pose.bones.get(self.name)
		self.write_pose_data(armature, pose_bone)
	
	@staticmethod
	def create_multiple_bones(armature, bone_datas):
		# A more optimized way, since this will only switch between modes twice.
		armature.select_set(True)
		bpy.context.view_layer.objects.active = armature
		bpy.ops.object.mode_set(mode='EDIT')
		for bd in bone_datas:
			edit_bone = find_or_create_bone(armature, bd.name)
		# Now that all the bones are created, loop over again to set the properties.
		for bd in bone_datas:
			edit_bone = armature.data.edit_bones.get(bd.name)
			bd.write_edit_data(armature, edit_bone)

		# And finally a third time, after switching to pose mode to write the bone data out from edit mode and make sure the PoseBone exists, so we can add constraints.
		bpy.ops.object.mode_set(mode='POSE')
		for bd in bone_datas:
			pose_bone = armature.pose.bones.get(bd.name)
			bd.write_pose_data(armature, pose_bone)

	@classmethod
	def create_all_bones(cls, armature):
		# Create a bone for every BoneData instance, then wipe the instances.
		cls.create_multiple_bones(armature, cls.instances)
		cls.clear()
	
	@classmethod
	def clear(cls):
		cls.instances = []

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

		stretch = {}
		stretch['rest_length'] = 0
		stretch['use_bulge_min'] = True
		stretch['use_bulge_max'] = True
		stretch['bulge_min'] = 1
		stretch['bulge_max'] = 1
		stretch['target'] = armature
		stretch['subtarget'] = next_stretch_name
		stretch = ('STRETCH_TO', stretch)
		def_bd.constraints.append(stretch)
		
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