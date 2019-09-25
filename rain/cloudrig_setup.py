import bpy
from mathutils import Vector

# Rig generation scripts and utilities.
# The long term goal for this is that the rig is generated based on a base set of bones that can be moved around in pose mode, akin to BlenRig's reproportion mode.
# The rig should then also be able to be re-generated after any changes to that base set.
# The generated rig could be a separate rig, but I'm not too big a fan of that, I think it makes things more complicated than it has to be.

# Where I left off: Current goal is to just get the STR- bones working. They spawn but they aren't placed correctly at all. Looks like no properties are getting applied.

arrow_shape = bpy.data.objects['Shape_Arrow']
sphere_shape = bpy.data.objects['Shape_Sphere']
fk_shape = bpy.data.objects['Shape_FK_Limb']
scale=0.01

def safe_create_constraint(pb, ctype, name=None):
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

def safe_create_bone(bonename):
	""" Create a bone only if a bone with the given name doesn't exist yet.
		Active object must be an edit mode armature. """
	bone = bpy.context.object.data.edit_bones.get(bonename)
	if(not bone):
		bone = bpy.context.object.data.edit_bones.new(bonename)
		bone.tail = ((0, 0, 0.1))	# Ensure bone doesn't get auto deleted for being 0 length
		#print("Created bone: " + bone.name )
	else:
		pass
		#print("Found bone, not creating: " + bone.name)
	return bone

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
						real_bone = safe_create_bone(self_value.name)
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
			c = safe_create_constraint(pose_bone, cd[0], name)
			for attr in cd[1].keys():
				if(hasattr(c, attr)):
					setattr(c, attr, cd[1][attr])

	def create_bone(self, armature):
		# Create a single bone and its constraints. Needs to switch between object modes.
		armature.select_set(True)
		bpy.context.view_layer.objects.active = armature

		bpy.ops.object.mode_set(mode='EDIT')
		edit_bone = safe_create_bone(self.name)
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
			edit_bone = safe_create_bone(bd.name)
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

def bone_iterator(armature, search=None, start=None, end=None, edit_bone=False):
	""" Convenience function to get iterators for our for loops. """
	bone_list = []
	if(edit_bone):
		bone_list = armature.data.edit_bones
	else:
		bone_list = armature.pose.bones
	
	if(search):
		return [b for b in bone_list if search in b.name]
	elif(start):
		return [b for b in bone_list if b.name.startswith(start)]
	elif(end):
		return [b for b in bone_list if b.name.endswith(end)]
	else:
		assert False, "Nothing passed."

def find_nearby_bones(search_co, dist, ebones=None):
	""" Bruteforce search for bones that are within a given distance of the given coordinates. """
	""" Active object must be an armature. """	# TODO: Let armature be passed, maybe optionally. Do some assert sanity checks.
	""" ebones: Only search in these bones. """
	
	armature = bpy.context.object
	ret = []
	for eb in armature.data.edit_bones:	# TODO: Could use data.bones instead so we don't have to be in edit mode?
		if(ebones and eb not in ebones): continue
		if( (eb.head - search_co).length < dist):
			ret.append(b)
	return ret

def get_chain(bone, ret=[]):
	""" Recursively build a list of the first children. 
		bone: Can be pose/data/edit bone, doesn't matter. """
	ret.append(bone)
	if(len(bone.children) > 0):
		return get_chain(bone.children[0], ret)
	return ret

def create_bbone_handle(bone_start=None, bone_end=None):
	""" Create a bone at the head of the start bone. (We assume the head of the start bone and the tail of the end bone are in the same place)
		Place the tail such that this bone's orientation is the average of the start and end bones' orientations.
		Assign arbitrary bone length, bbone scale, bone shape.
		bone_start: The bone for which this tangent bone should be the start handle of. Pose/Data/EditBone.
		bone_end: The bone for which this tangent bone should be the end handle of. Pose/Data/EditBone.
		Usually bone_start.parent==bone_end.
		Active object must be an armature in edit mode.
	"""

	assert bone_start or bone_end, "No bones passed."	# TODO: This should be a warning, not an error?

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
		nearby_bones = find_nearby_bones(bone_start.tail, 0.0005, )
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

def create_bbone_handles_for_chain(chain):
	""" Create all BBone handles for a chain. Active object must be an armature in edit mode.
		chain: list of Pose/Data/Editbones in hierarchical order. """
	for i, def_bone in enumerate(chain):
		if(i==0):
			# Tangent control for the first bone in each chain needs to be created based on only start bone.
			def_bone.bbone_custom_handle_start = create_bbone_handle(bone_start=chain[0], bone_end=None)
			if(len(chain)==1):
				# If there is exactly one bone in the chain, it's both the first and last bone, so we also need to create its tail tangent here.
				def_bone.bbone_custom_handle_end = create_bbone_handle(bone_start=None, bone_end=chain[0])
			continue

		chain[i].bbone_custom_handle_start = chain[i-1].bbone_custom_handle_end = create_bbone_handle(chain[i], chain[i-1])

		if(i==len(chain)-1):
			# Tangent control for the last bone in each chain needs to be created based on only end bone.
			chain[i].bbone_custom_handle_end = create_bbone_handle(bone_start=None, bone_end=chain[i])
			continue

def face_bbone_setup(armature):
	""" Set up the low level controls for the face, based on bones in a predefined group. """
	# TODO: Also set up higher level controls...

	assert armature.type=='ARMATURE', "Not an armature."

	bone_group = "Face: DEF - Bendy Deform Bones ###"	# TODO Hardcoded group name, meh.

	pbones = [b for b in armature.pose.bones if b.bone_group and b.bone_group.name==bone_group]
	ebones = [eb for eb in armature.data.edit_bones if eb.name in pbones]

	for eb in ebones:
		if(eb.parent not in ebones
		or eb.parent.children[0] != eb):	# This is not the 1st child of the bone, so it is considered a separate chain.
			chain = get_chain(eb, [])
			create_bbone_handles_for_chain(chain)

	bpy.ops.armature.select_more()
	bpy.ops.object.mode_set(mode='POSE')	# TODO: this is not needed?
	
	### CONSTRAINTS
	for pb in armature.pose.bones:		
		if("Node_UserRotation_CTR-" in pb.name):
			copy_rotation = safe_create_constraint(pb, 'COPY_ROTATION')
			copy_rotation.target = armature
			copy_rotation.subtarget = pb.name.replace("Node_UserRotation_CTR-", "CTR-")
			copy_rotation.target_space = copy_rotation.owner_space = 'LOCAL'
		
		if("Node_UserRotation_TAN-" in pb.name):
			pb.custom_shape = arrow_shape
			pb.use_custom_shape_bone_size = False
			armature_const = safe_create_constraint(pb, 'ARMATURE')
			target = armature_const.targets.new()
			target.target = armature
			db = armature.data.bones.get(pb.name)
			target.subtarget = db['parent']
		
		if('TAN-' not in pb.name): continue
		
		pb.custom_shape = arrow_shape
		pb.use_custom_shape_bone_size = False
		if(pb.name.startswith('TAN')):
			pb.bone_group = armature.pose.bone_groups.get('Face: TAN - BBone Tangent Handle Helpers')	# TODO: safe_create_bone_group()
			pb.custom_shape_scale = 1.4
			copy_rotation = safe_create_constraint(pb, 'COPY_ROTATION')
			copy_rotation.target = armature
			copy_rotation.subtarget = pb.name.replace("TAN-", "Node_UserRotation_TAN-")
			copy_rotation.target_space = copy_rotation.owner_space = 'LOCAL'
			copy_rotation.use_offset = True

		if(pb.name.startswith('AIM')):
			pb.bone_group = armature.pose.bone_groups.get('Face: TAN-AIM - BBone Automatic Handle Helpers')
			pb.custom_shape_scale = 1.6
			db = armature.data.bones.get(pb.name)
			copy_location = safe_create_constraint(pb, 'COPY_LOCATION')
			copy_location.target = armature
			copy_location.subtarget = db['copy_loc']
			if('pos_aim' in db):
				damped_pos = safe_create_constraint(pb, 'DAMPED_TRACK', "Damped Track +Y")
				damped_pos.target = armature
				damped_pos.subtarget = db['pos_aim']
				damped_pos.track_axis = 'TRACK_Y'
			if('neg_aim' in db):
				damped_neg = safe_create_constraint(pb, 'DAMPED_TRACK', "Damped Track -Y")
				damped_neg.target = armature
				damped_neg.subtarget = db['neg_aim']
				damped_neg.track_axis = 'TRACK_NEGATIVE_Y'
				if('pos_aim' in db):
					damped_neg.influence = 0.5

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

	
	
def run():
	# Make sure only passed armature is in edit mode.	# TODO: This should actually be done further outside of this function. So by the time this funciton is called, we already want to assume that we have an armature in edit mode.
	armature = bpy.context.object
	org_mode = armature.mode
	assert armature.type=='ARMATURE', "Active object must be an armature."
	bpy.ops.object.mode_set(mode='EDIT')

	#face_bbone_setup(armature)
	spine_bbone_setup(armature)
	# FK Controls should have specific names. This is nice to do outside of the spine setup function because then while we're in there, we can rely on numbers at the end of the bones.
	# TODO: However, it has to be done after the bones are created, because otherwise parent names (which have to be stored as strings...) get messed up.
	# Alternatively, maybe parent strings should be BoneData instances instead. Or let them be either. I like this.
	"""fk_bone_datas = [bd for bd in BoneData.instances if bd.name.startswith("FK-")]
	fk_spine_names = ["Spine", "Ribcage", "Chest"]
	for i, name in enumerate(fk_spine_names):
		fk_bone_datas[i].name = name"""
	bpy.ops.object.mode_set(mode=org_mode)

run()