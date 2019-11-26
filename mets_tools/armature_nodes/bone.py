# Data Container and utilities for de-coupling bone creation and setup from BPY.
# Lets us easily create bones without having to worry about edit/pose mode.
def get_defaults(contype, armature):
    """Return my preferred defaults for each constraint type."""
    ret = {
        "target_space" : 'LOCAL',
        "owner_space" : 'LOCAL',
        "target" : armature,

     }

    if contype == 'STRETCH_TO':
        pass



class BoneData:
	"""Container and creator of bones."""
	instances = []	# Let the class keep track of its instances.

	@classmethod
	def get_instance(cls, name):
		"""Find a BoneData instance by name, if it exists."""
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

    def add_constraint(self, contype, props={}, armature=None, true_defaults=False):
        """Add a constraint to this bone.
        contype: Type of constraint, eg. 'STRETCH_TO'.
        props: Dictionary of properties and values that this constraint type would have.
        true_defaults: When False, we use a set of arbitrary default values that I consider better than Blender's defaults.
        """
        pass





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

        assert armature.mode == 'EDIT', "Armature must be in Edit Mode when writing bone data"

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
		assert armature.mode != 'EDIT', "Armature cannot be in Edit Mode when writing pose data"

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
		# First we create all the bones.
        for bd in bone_datas:
			edit_bone = find_or_create_bone(armature, bd.name)
        
		# Now that all the bones are created, loop over again to set the properties.
		for bd in bone_datas:
			edit_bone = armature.data.edit_bones.get(bd.name)
			bd.write_edit_data(armature, edit_bone)

		# And finally a third time, after switching to pose mode, so we can add constraints.
		bpy.ops.object.mode_set(mode='POSE')
		for bd in bone_datas:
			pose_bone = armature.pose.bones.get(bd.name)
			bd.write_pose_data(armature, pose_bone)

	@classmethod
	def create_all_bones(cls, armature, clear=True):
		cls.create_multiple_bones(armature, cls.instances)
		if clear:
            cls.clear()
	
	@classmethod
	def clear(cls):
		cls.instances = []