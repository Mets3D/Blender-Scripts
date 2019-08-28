import bpy
from mathutils import Vector

class BoneData:
	# Container and creator of Bones for the Armature Node system.
	# (Only Edit Bone data, not pose)
	name = "Bone"
	head = Vector((0,0,0))
	tail = Vector((0,0,0))
	roll = 0
	rotation_mode = 'QUATERNION'
	bbone_curveinx = 0
	bbone_curveiny = 0
	bbone_curveoutx = 0
	bbone_curveouty = 0
	bbone_custom_handle_start = ""  # Bone name
	bbone_custom_handle_end = ""	# Bone name
	bbone_custom_handle_start_type = "AUTO"
	bbone_custom_handle_end_type = "AUTO"
	bbone_easein = 0
	bbone_easeout = 0
	bbone_scaleinx = 0
	bbone_scaleiny = 0
	bbone_scaleoutx = 0
	bbone_scaleouty = 0
	bbone_segments = 1
	bbone_x = 0.1
	bbone_z = 0.1
	bone_group = ""
	custom_shape = None   # Object ID?
	custom_shape_scale = 1.0
	custom_shape_transform = "" # Bone name
	use_endroll_as_inroll = False
	use_connect = False
	use_deform = False
	use_inherit_rotation = True
	use_inherit_scale = True
	use_local_location = True
	use_envelope_multiply = False
	use_relative_parent = False
	parent = None # Bone ID?
	
	constraints = []

	def apply_edit(to_bone):
		# to_bone is an EditBone.
		my_dict = self.__dict__
		for attr in my_dict.keys():
			if(attr in ["constraints", "bone_group"]): continue	# Skip non-edit-bone values
			setattr(to_bone, attr, my_dict[attr])
	
	def apply_pose(to_bone):
		# to_bone is a PoseBone.
		for attr in ["bone_group"]:
			setattr(to_bone, attr, self.__dict__[attr])
		self.create_constraints(to_bone)
	
	def create_constraints(to_bone):
		# to_bone is a PoseBone.
		for c in self.constraints:

class ConstraintData:
	# I don't want to do thiiiisssssss!!!!-+


