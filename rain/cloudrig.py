"Version: 1.1"
"2020-01-09"

import bpy
from bpy.props import *
from mathutils import Vector, Matrix
from math import *

def get_rigs():
	""" Find all cloudrig armatures in the file."""
	return [o for o in bpy.data.objects if o.type=='ARMATURE' and 'cloudrig' in o]

def get_rig():
	"""If the active object is a cloudrig, return it."""
	rig = bpy.context.object
	if rig and rig.type == 'ARMATURE' and 'cloudrig' in rig:
		return rig

def get_char_bone(rig):
	for b in rig.pose.bones:
		if b.name.startswith("Properties_Character"):
			return b

class Snap_FK2IK(bpy.types.Operator):
	"""Snap FK to IK chain"""
	bl_idname = "armature.snap_fk_to_ik"
	bl_label = "Snap FK to IK"
	bl_options = {'REGISTER', 'UNDO'}

	fk_bones: StringProperty()
	ik_bones: StringProperty()

	def execute(self, context):
		armature = context.object
		fk_bones = list(map(armature.pose.bones.get, self.fk_bones.split(", ")))
		ik_bones = list(map(armature.pose.bones.get, self.ik_bones.split(", ")))

		for i, fkb in enumerate(fk_bones):
			fk_bones[i].matrix = ik_bones[i].matrix
			context.evaluated_depsgraph_get().update()

		# Deselect all bones
		for b in context.selected_pose_bones:
			b.bone.select=False
			
		# Select affected bones
		for b in fk_bones:
			b.bone.select=True

		return {'FINISHED'}

def perpendicular_vector(v):
	""" Returns a vector that is perpendicular to the one given.
		The returned vector is _not_ guaranteed to be normalized.
	"""
	# Create a vector that is not aligned with v.
	# It doesn't matter what vector.  Just any vector
	# that's guaranteed to not be pointing in the same
	# direction.
	if abs(v[0]) < abs(v[1]):
		tv = Vector((1,0,0))
	else:
		tv = Vector((0,1,0))

	# Use cross prouct to generate a vector perpendicular to
	# both tv and (more importantly) v.
	return v.cross(tv)

def set_pose_translation(pose_bone, mat):
	""" Sets the pose bone's translation to the same translation as the given matrix.
		Matrix should be given in bone's local space.
	"""
	if pose_bone.bone.use_local_location == True:
		pose_bone.location = mat.to_translation()
	else:
		loc = mat.to_translation()

		rest = pose_bone.bone.matrix_local.copy()
		if pose_bone.bone.parent:
			par_rest = pose_bone.bone.parent.matrix_local.copy()
		else:
			par_rest = Matrix()

		q = (par_rest.inverted() @ rest).to_quaternion()
		pose_bone.location = q @ loc

def get_pose_matrix_in_other_space(mat, pose_bone):
	""" Returns the transform matrix relative to pose_bone's current
		transform space.  In other words, presuming that mat is in
		armature space, slapping the returned matrix onto pose_bone
		should give it the armature-space transforms of mat.
		TODO: try to handle cases with axis-scaled parents better.
	"""
	rest = pose_bone.bone.matrix_local.copy()
	rest_inv = rest.inverted()
	if pose_bone.parent:
		par_mat = pose_bone.parent.matrix.copy()
		par_inv = par_mat.inverted()
		par_rest = pose_bone.parent.bone.matrix_local.copy()
	else:
		par_mat = Matrix()
		par_inv = Matrix()
		par_rest = Matrix()

	# Get matrix in bone's current transform space
	smat = rest_inv @ (par_rest @ (par_inv @ mat))

	# Compensate for non-local location
	#if not pose_bone.bone.use_local_location:
	#	loc = smat.to_translation() @ (par_rest.inverted() @ rest).to_quaternion()
	#	smat.translation = loc

	return smat

def rotation_difference(mat1, mat2):
	""" Returns the shortest-path rotational difference between two
		matrices.
	"""
	q1 = mat1.to_quaternion()
	q2 = mat2.to_quaternion()
	angle = acos(min(1,max(-1,q1.dot(q2)))) * 2
	if angle > pi:
		angle = -angle + (2*pi)
	return angle

def match_pole_target(ik_first, ik_last, pole, match_bone, length):
	""" Places an IK chain's pole target to match ik_first's
		transforms to match_bone.  All bones should be given as pose bones.
		You need to be in pose mode on the relevant armature object.
		ik_first: first bone in the IK chain
		ik_last:  last bone in the IK chain
		pole:  pole target bone for the IK chain
		match_bone:  bone to match ik_first to (probably first bone in a matching FK chain)
		length:  distance pole target should be placed from the chain center
	"""
	a = ik_first.matrix.to_translation()
	b = ik_last.matrix.to_translation() + ik_last.vector

	# Vector from the head of ik_first to the
	# tip of ik_last
	ikv = b - a

	# Get a vector perpendicular to ikv
	pv = perpendicular_vector(ikv).normalized() * length

	def set_pole(pvi):
		""" Set pole target's position based on a vector
			from the arm center line.
		"""
		# Translate pvi into armature space
		ploc = a + (ikv/2) + pvi

		# Set pole target to location
		mat = get_pose_matrix_in_other_space(Matrix.Translation(ploc), pole)
		set_pose_translation(pole, mat)

		bpy.ops.object.mode_set(mode='OBJECT')
		bpy.ops.object.mode_set(mode='POSE')

	set_pole(pv)

	# Get the rotation difference between ik_first and match_bone
	angle = rotation_difference(ik_first.matrix, match_bone.matrix)

	# Try compensating for the rotation difference in both directions
	pv1 = Matrix.Rotation(angle, 4, ikv) @ pv
	set_pole(pv1)
	ang1 = rotation_difference(ik_first.matrix, match_bone.matrix)

	pv2 = Matrix.Rotation(-angle, 4, ikv) @ pv
	set_pole(pv2)
	ang2 = rotation_difference(ik_first.matrix, match_bone.matrix)

	# Do the one with the smaller angle
	if ang1 < ang2:
		set_pole(pv1)

class Snap_IK2FK(bpy.types.Operator):
	"""Snap IK to FK chain"""
	"""Credit for most code (for figuring out the pole target matrix) to Rigify."""	# TODO: Actually, the resulting pole target location appears to be imprecise.
	bl_idname = "armature.snap_ik_to_fk"
	bl_label = "Snap IK to FK"
	bl_options = {'REGISTER', 'UNDO'}

	fk_bones: StringProperty()
	ik_bones: StringProperty()
	ik_pole: StringProperty()
	ik_parent: BoolProperty(default=True)
	
	@classmethod
	def poll(cls, context):
		if context.object and context.object.type=='ARMATURE': 
			return True

	def execute(self, context):
		armature = context.object

		fk_bones = list(map(armature.pose.bones.get, self.fk_bones.split(", ")))
		ik_bones = list(map(armature.pose.bones.get, self.ik_bones.split(", ")))
		ik_pole = armature.pose.bones.get(self.ik_pole)

		# Snap the last IK control to the last FK control.
		last_fk_bone = fk_bones[-1]
		last_ik_bone = ik_bones[-1]
		select_bones = [last_ik_bone, ik_pole]
		if self.ik_parent:
			ik_parent_bone = last_ik_bone.parent
			ik_parent_bone.matrix = last_fk_bone.matrix
			select_bones.append(ik_parent_bone)
			context.evaluated_depsgraph_get().update()
		last_ik_bone.matrix = last_fk_bone.matrix
		context.evaluated_depsgraph_get().update()
		
		first_ik_bone = fk_bones[0]
		first_fk_bone = ik_bones[0]
		match_pole_target(first_ik_bone, last_ik_bone, ik_pole, first_fk_bone, 0.5)
		context.evaluated_depsgraph_get().update()

		# Deselect all bones
		for b in context.selected_pose_bones:
			b.bone.select=False

		# Select affected bones
		for b in select_bones:
			b.bone.select=True

		return {'FINISHED'}

class IKFK_Toggle(bpy.types.Operator):
	"Toggle between IK and FK, and snap the controls accordingly. This will NOT place any keyframes, but it will select the affected bones"
	bl_idname = "armature.ikfk_toggle"
	bl_label = "Toggle IK/FK"
	bl_options = {'REGISTER', 'UNDO'}
	
	prop_bone: StringProperty()
	prop_name: StringProperty()

	fk_bones: StringProperty()
	ik_bones: StringProperty()
	ik_pole: StringProperty()
	ik_parent: BoolProperty(default=True)

	@classmethod
	def poll(cls, context):
		if context.object and context.object.type=='ARMATURE' and context.mode=='POSE': 
			return True

	def execute(self, context):
		if self.prop_bone != "":
			armature = context.object

			prop_bone = armature.pose.bones.get(self.prop_bone)
			if prop_bone[self.prop_name] < 1:
				bpy.ops.armature.snap_ik_to_fk(fk_bones=self.fk_bones, ik_bones=self.ik_bones, ik_pole=self.ik_pole, ik_parent=self.ik_parent)
				prop_bone[self.prop_name] = 1.0
			else:
				bpy.ops.armature.snap_fk_to_ik(fk_bones=self.fk_bones, ik_bones=self.ik_bones)
				prop_bone[self.prop_name] = 0.0

		return {'FINISHED'}

class Reset_Rig_Colors(bpy.types.Operator):
	"""Reset rig color properties to their stored default."""
	bl_idname = "object.reset_rig_colors"
	bl_label = "Reset Rig Colors"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return 'cloudrig' in context.object

	def execute(self, context):
		rig = context.object
		for cp in rig.rig_colorproperties:
			cp.color = cp.default
		return {'FINISHED'}

class Rig_ColorProperties(bpy.types.PropertyGroup):
	""" Store a ColorProperty that can be used to drive colors on the rig, and then be controlled even when the rig is linked.
	"""
	default: FloatVectorProperty(
		name='Default',
		description='',
		subtype='COLOR',
		min=0,
		max=1,
		options={'LIBRARY_EDITABLE'}
	)
	color: FloatVectorProperty(
		name='Color',
		description='',
		subtype='COLOR',
		min=0,
		max=1,
		options={'LIBRARY_EDITABLE'}
	)

class Rig_BoolProperties(bpy.types.PropertyGroup):
	""" Store a BoolProperty referencing an outfit/character property whose min==0 and max==1.
		This BoolProperty will be used to display the property as a toggle button in the UI.
	"""
	# This is currently only used for outfit/character settings, NOT rig settings. Those booleans are instead hard-coded into rig_properties.

	def update_id_prop(self, context):
		""" Callback function to update the corresponding ID property when this BoolProperty's value is changed. """
		rig = get_rig()
		rig_props = rig.rig_properties
		outfit_bone = rig.pose.bones.get("Properties_Outfit_"+rig_props.outfit)
		char_bone = get_char_bone(rig)
		for prop_owner in [outfit_bone, char_bone]:
			if(prop_owner != None):
				if(self.name in prop_owner):
					prop_owner[self.name] = self.value
		

	value: BoolProperty(
		name='Boolean Value',
		description='',
		update=update_id_prop,
		options={'LIBRARY_EDITABLE'}
	)

class Rig_Properties(bpy.types.PropertyGroup):
	""" PropertyGroup for storing fancy custom properties in.
		Character and Outfit specific properties will still be stored in their relevant Properties bones (eg. Properties_Outfit_Rain).
	"""

	def get_rig(self):
		""" Find the armature object that is using this instance (self). """

		for rig in get_rigs():
			if(rig.rig_properties == self):
				return rig

	def update_bool_properties(self, context):
		""" Create BoolProperties out of those outfit properties whose min==0 and max==1.
			These BoolProperties are necessarry because only BoolProperties can be displayed in the UI as toggle buttons.
		"""
		
		rig = self.get_rig()
		bool_props = rig.rig_boolproperties
		bool_props.clear()	# Nuke all the bool properties
		
		outfit_bone = rig.pose.bones.get("Properties_Outfit_" + self.outfit)
		char_bone = get_char_bone(rig)
		for prop_owner in [outfit_bone, char_bone]:
			if(prop_owner==None): continue
			for p in prop_owner.keys():
				if( type(prop_owner[p]) != int or p.startswith("_") ): continue
				my_min = prop_owner['_RNA_UI'].to_dict()[p]['min']
				my_max = prop_owner['_RNA_UI'].to_dict()[p]['max']
				if(my_min==0 and my_max==1):
					new_bool = bool_props.add()
					new_bool.name = p
					new_bool.value = prop_owner[p]
					new_bool.rig = rig
	
	def outfits(self, context):
		""" Callback function for finding the list of available outfits for the outfit enum.
			Based on naming convention. Bones storing an outfit's properties must be named "Properties_Outfit_OutfitName".
		"""
		rig = self.get_rig()

		outfits = []
		for b in rig.pose.bones:
			if b.name.startswith("Properties_Outfit_"):
				outfits.append(b.name.replace("Properties_Outfit_", ""))
		
		# Convert the list into what an EnumProperty expects.
		items = []
		for i, outfit in enumerate(outfits):
			items.append((outfit, outfit, outfit, i))	# Identifier, name, description, can all be the character name.
		
		# If no outfits were found, don't return an empty list so the console doesn't spam "'0' matches no enum" warnings.
		if(items==[]):
			return [(('identifier', 'name', 'description'))]
		
		return items
	
	def change_outfit(self, context):
		""" Update callback of outfit enum. """
		
		rig = self.get_rig()
		
		if( (self.outfit == '') ):
			self.outfit = self.outfits(context)[0][0]
		
		outfit_bone = rig.pose.bones.get("Properties_Outfit_"+self.outfit)
		
		self.update_bool_properties(context)

	outfit: EnumProperty(
		name="Outfit",
		items=outfits,
		update=change_outfit)
	
	render_modifiers: BoolProperty(
		name='render_modifiers',
		description='Enable SubSurf, Solidify, Bevel, etc. modifiers in the viewport')
	
	use_proxy: BoolProperty(
		name='use_proxy',
		description='Use Proxy Meshes')

class RigUI(bpy.types.Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'CloudRig'
	
	@classmethod
	def poll(cls, context):
		return 'cloudrig' in context.object

	def draw(self, context):
		layout = self.layout

class RigUI_Outfits(RigUI):
	bl_idname = "OBJECT_PT_rig_ui_properties"
	bl_label = "Outfits"

	@classmethod
	def poll(cls, context):
		if(not super().poll(context)):
			return False

		# Only display this panel if there is either an outfit with options, multiple outfits, or character options.
		rig = context.object
		if(not rig): return False
		rig_props = rig.rig_properties
		bool_props = rig.rig_boolproperties
		multiple_outfits = len(rig_props.outfits(context)) > 1
		outfit_properties_bone = rig.pose.bones.get("Properties_Outfit_"+rig_props.outfit)
		char_bone = get_char_bone(rig)

		return multiple_outfits or outfit_properties_bone or char_bone

	def draw(self, context):
		layout = self.layout
		rig = context.object

		rig_props = rig.rig_properties
		bool_props = rig.rig_boolproperties
		
		char_bone = get_char_bone(rig)
		outfit_properties_bone = rig.pose.bones.get("Properties_Outfit_"+rig_props.outfit)
		
		def add_props(prop_owner):
			props_done = []

			for prop_name in prop_owner.keys():
				if( prop_name in props_done or prop_name.startswith("_") ): continue
				# Int Props
				if(prop_name not in bool_props and type(prop_owner[prop_name]) in [int, float] ):
					layout.prop(prop_owner, '["'+prop_name+'"]', slider=True, text=prop_name.replace("_", " "))
					props_done.append(prop_name)
			# Bool Props
			for bp in bool_props:
				if(bp.name in prop_owner.keys() and bp.name not in props_done):
					layout.prop(bp, 'value', toggle=True, text=bp.name.replace("_", " "))

		# Add character properties to the UI, if any.
		if( char_bone ):
			add_props(char_bone)
			layout.separator()

		# Add outfit properties to the UI, if any. Always add outfit selector.
		layout.prop(rig_props, 'outfit')
		if( outfit_properties_bone != None ):
			add_props(outfit_properties_bone)

class RigUI_Layers(RigUI):
	bl_idname = "OBJECT_PT_rig_ui_layers"
	bl_label = "Layers"
	
	def draw(self, context):
		layout = self.layout
		rig = context.object
		data = rig.data
		
		row_ik = layout.row()
		row_ik.prop(data, 'layers', index=0, toggle=True, text='IK')
		row_ik.prop(data, 'layers', index=16, toggle=True, text='IK Secondary')
		
		row_fk = layout.row()
		row_fk.prop(data, 'layers', index=1, toggle=True, text='FK')
		row_fk.prop(data, 'layers', index=17, toggle=True, text='FK Secondary')
		
		layout.prop(data, 'layers', index=2, toggle=True, text='Stretch')
		
		row_face = layout.row()
		row_face.column().prop(data, 'layers', index=3, toggle=True, text='Face Primary')
		row_face.column().prop(data, 'layers', index=19, toggle=True, text='Face Extras')
		row_face.column().prop(data, 'layers', index=20, toggle=True, text='Face Tweak')
		
		layout.prop(data, 'layers', index=5, toggle=True, text='Fingers')
		
		layout.row().prop(data, 'layers', index=6, toggle=True, text='Hair')
		layout.row().prop(data, 'layers', index=7, toggle=True, text='Clothes')
		
		# Draw secret layers
		if('dev' in rig and rig['dev']==1):
			layout.separator()
			layout.prop(rig, '["dev"]', text="Secret Layers")
			layout.label(text="Body")
			row = layout.row()
			row.prop(data, 'layers', index=8, toggle=True, text='Mech')
			row.prop(data, 'layers', index=9, toggle=True, text='Adjust Mech')
			row = layout.row()
			row.prop(data, 'layers', index=24, toggle=True, text='Deform')
			row.prop(data, 'layers', index=25, toggle=True, text='Adjust Deform')

			layout.label(text="Head")
			row = layout.row()
			row.prop(data, 'layers', index=11, toggle=True, text='Mech')
			row.prop(data, 'layers', index=12, toggle=True, text='Unlockers')
			row = layout.row()
			row.prop(data, 'layers', index=27, toggle=True, text='Deform')
			row.prop(data, 'layers', index=28, toggle=True, text='Hierarchy')

			layout.label(text="Other")
			death_row = layout.row()
			death_row.prop(data, 'layers', index=30, toggle=True, text='Properties')
			death_row.prop(data, 'layers', index=31, toggle=True, text='Black Box')

class RigUI_Settings_FKIK(RigUI):
	bl_idname = "OBJECT_PT_rig_ui_settings"
	bl_label = "Settings"
	
	def draw(self, context):
		layout = self.layout
		rig = context.object

		rig_props = rig.rig_properties
		layout.row().prop(rig_props, 'render_modifiers', text='Enable Modifiers', toggle=True)

class RigUI_Settings_FKIK_Switch(RigUI):
	bl_idname = "OBJECT_PT_rig_ui_ikfk_switch"
	bl_label = "FK/IK Switch"
	bl_parent_id = "OBJECT_PT_rig_ui_settings"

	def draw(self, context):
		layout = self.layout
		rig = context.object

		fk_arm_left = ", ".join(["FK-Upperarm_Parent.L", "FK-Upperarm.L", "FK-Forearm.L", "FK-Hand.L"])
		ik_arm_left = ", ".join(["IK-Upperarm.L", "IK-Upperarm.L", "IK-Forearm.L", "IK-Hand.L"])
		pole_arm_left = "IK-Pole-Forearm.L"

		fk_arm_right = ", ".join(["FK-Upperarm_Parent.R", "FK-Upperarm.R", "FK-Forearm.R", "FK-Hand.R"])
		ik_arm_right = ", ".join(["IK-Upperarm.R", "IK-Upperarm.R", "IK-Forearm.R", "IK-Hand.R"])
		pole_arm_right = "IK-Pole-Forearm.R"

		fk_leg_left  = ", ".join(["FK-Thigh_Parent.L", "FK-Thigh.L", "FK-Shin.L", "FK-Foot.L"])
		ik_leg_left  = ", ".join(["IK-Thigh.L", "IK-Thigh.L", "IK-Shin.L", "MSTR-Foot.L"])
		pole_leg_left = "IK-Pole-Shin.L"

		fk_leg_right = ", ".join(["FK-Thigh_Parent.R", "FK-Thigh.R", "FK-Shin.R", "FK-Foot.R"])
		ik_leg_right  = ", ".join(["IK-Thigh.R", "IK-Thigh.R", "IK-Shin.R", "MSTR-Foot.R"])
		pole_leg_right = "IK-Pole-Shin.R"

		ikfk_props = rig.pose.bones.get('Properties_IKFK')

		layout.row().prop(ikfk_props, '["ik_spine"]', slider=True, text='Spine')
		
		arms = [
			("ik_arm_left", "Left Arm", fk_arm_left, ik_arm_left, pole_arm_left), 
			("ik_arm_right", "Right Arm", fk_arm_right, ik_arm_right, pole_arm_right)
		]
		legs = [
			("ik_leg_left", "Left Leg", fk_leg_left, ik_leg_left, pole_leg_left),
			("ik_leg_right", "Right Leg", fk_leg_right, ik_leg_right, pole_leg_right)
		]
		limbses = [arms, legs]

		for limbs in limbses:
			limb_row = layout.row()
			for limb in limbs:
				limb_col = limb_row.column()
				limb_sub = limb_col.row(align=True)
				limb_sub.prop(ikfk_props, '["'+limb[0]+'"]', slider=True, text=limb[1])
				switch = limb_sub.operator(IKFK_Toggle.bl_idname, text="", icon='FILE_REFRESH')
				switch.fk_bones = limb[2]
				switch.ik_bones = limb[3]
				switch.ik_pole = limb[4]
				switch.prop_bone = ikfk_props.name
				switch.prop_name = limb[0]

class RigUI_Settings_IK(RigUI):
	bl_idname = "OBJECT_PT_rig_ui_ik"
	bl_label = "IK Settings"
	bl_parent_id = "OBJECT_PT_rig_ui_settings"

	def draw(self, context):
		layout = self.layout
		rig = context.object
		ikfk_props = rig.pose.bones.get('Properties_IKFK')

		# IK Stretch
		layout.label(text="IK Stretch")
		layout.prop(ikfk_props, '["ik_stretch_spine"]', slider=True, text='Stretchy Spine')
		layout.prop(ikfk_props, '["ik_stretch_arms"]',  slider=True, text='Stretchy Arms' )
		layout.prop(ikfk_props, '["ik_stretch_legs"]',  slider=True, text='Stretchy Legs' )

		# IK Hinge
		layout.label(text="IK Hinge")
		hand_row = layout.row()
		hand_row.prop(ikfk_props, '["ik_hinge_hand_left"]',  slider=True, text='Left Hand' )
		hand_row.prop(ikfk_props, '["ik_hinge_hand_right"]', slider=True, text='Right Hand')
		foot_row = layout.row()
		foot_row.prop(ikfk_props, '["ik_hinge_foot_left"]',  slider=True, text='Left Foot' )
		foot_row.prop(ikfk_props, '["ik_hinge_foot_right"]', slider=True, text='Right Foot')

		# IK Parents
		layout.label(text='IK Parents')
		arm_parent_row = layout.row()
		arm_parents = ['Root', 'Pelvis', 'Chest', 'Arm']
		arm_parent_row.prop(ikfk_props, '["ik_parents_arm_left"]',  slider=True, text = "Left Hand ["  + arm_parents[ikfk_props["ik_parents_arm_left"]]  + "]")
		arm_parent_row.prop(ikfk_props, '["ik_parents_arm_right"]', slider=True, text = "Right Hand [" + arm_parents[ikfk_props["ik_parents_arm_right"]] + "]")
		leg_parent_row = layout.row()
		leg_parents = ['Root', 'Pelvis', 'Hips', 'Leg']
		leg_parent_row.prop(ikfk_props, '["ik_parents_leg_left"]',  slider=True, text = "Left Foot ["  + leg_parents[ikfk_props["ik_parents_leg_left"]]  + "]")
		leg_parent_row.prop(ikfk_props, '["ik_parents_leg_right"]', slider=True, text = "Right Foot [" + leg_parents[ikfk_props["ik_parents_leg_right"]] + "]")

		# IK Pole Follow
		layout.label(text='IK Pole Follow')
		pole_row = layout.row()
		pole_row.prop(ikfk_props, '["ik_pole_follow_hands"]', slider=True, text='Arms')
		pole_row.prop(ikfk_props, '["ik_pole_follow_feet"]',  slider=True, text='Legs')

class RigUI_Settings_FK(RigUI):
	bl_idname = "OBJECT_PT_rig_ui_fk"
	bl_label = "FK Settings"
	bl_parent_id = "OBJECT_PT_rig_ui_settings"

	def draw(self, context):
		layout = self.layout
		rig = context.object
		rig_props = rig.rig_properties
		ikfk_props = rig.pose.bones.get('Properties_IKFK')
		face_props = rig.pose.bones.get('Properties_Face')

		# FK Hinge
		layout.label(text='FK Hinge')
		hand_row = layout.row()
		hand_row.prop(ikfk_props, '["fk_hinge_arm_left"]',  slider=True, text='Left Arm' )
		hand_row.prop(ikfk_props, '["fk_hinge_arm_right"]', slider=True, text='Right Arm')
		foot_row = layout.row()
		foot_row.prop(ikfk_props, '["fk_hinge_leg_left"]',  slider=True, text='Left Leg' )
		foot_row.prop(ikfk_props, '["fk_hinge_leg_right"]', slider=True, text='Right Leg')

		# Head settings
		layout.separator()
		layout.prop(face_props, '["neck_hinge"]', slider=True, text='Neck Hinge')
		layout.prop(face_props, '["head_hinge"]', slider=True, text='Head Hinge')

class RigUI_Settings_Face(RigUI):
	bl_idname = "OBJECT_PT_rig_ui_face"
	bl_label = "Face Settings"
	bl_parent_id = "OBJECT_PT_rig_ui_settings"

	def draw(self, context):
		layout = self.layout
		rig = context.object
		face_props = rig.pose.bones.get('Properties_Face')

		# Eyelid settings
		layout.prop(face_props, '["sticky_eyelids"]',    text='Sticky Eyelids',  slider=True)
		layout.prop(face_props, '["sticky_eyesockets"]', text='Sticky Eyerings', slider=True)

		layout.separator()
		# Mouth settings
		layout.prop(face_props, '["teeth_follow_mouth"]', text='Teeth Follow Mouth', slider=True)

class RigUI_Settings_Misc(RigUI):
	bl_idname = "OBJECT_PT_rig_ui_misc"
	bl_label = "Misc"
	bl_parent_id = "OBJECT_PT_rig_ui_settings"

	def draw(self, context):
		layout = self.layout
		rig = context.object
		rig_props = rig.rig_properties
		ikfk_props = rig.pose.bones.get('Properties_IKFK')
		face_props = rig.pose.bones.get('Properties_Face')

		layout.label(text="Grab Parents")
		row = layout.row()
		grab_parents = ['Root', 'Hand']
		row.prop(ikfk_props, '["grab_parent_left"]',  text="Left Hand [" + grab_parents[ikfk_props["grab_parent_left"]] + "]", slider=True)
		row.prop(ikfk_props, '["grab_parent_right"]',  text="Right Hand [" + grab_parents[ikfk_props["grab_parent_right"]] + "]", slider=True)

		layout.label(text="Eye Target Parent")
		row = layout.row()
		eye_parents = ['Root', 'Torso', 'Torso_Loc', 'Head']
		row.prop(ikfk_props, '["eye_target_parent"]',  text=eye_parents[ikfk_props["eye_target_parent"]], slider=True)

class RigUI_Viewport_Display(RigUI):
	bl_idname = "OBJECT_PT_rig_ui_viewport_display"
	bl_label = "Viewport Display"

	def draw(self, context):
		layout = self.layout
		rig = context.object
		layout.operator(Reset_Rig_Colors.bl_idname, text="Reset Colors")
		layout.separator()
		for cp in rig.rig_colorproperties:
			layout.prop(cp, "color", text=cp.name)

classes = (
	Rig_ColorProperties,
	Rig_BoolProperties,
	Rig_Properties,
	RigUI_Outfits,
	RigUI_Layers,
	Snap_IK2FK,
	Snap_FK2IK,
	IKFK_Toggle,
	Reset_Rig_Colors,
	RigUI_Settings_FKIK,
	RigUI_Settings_FKIK_Switch,
	RigUI_Settings_IK,
	RigUI_Settings_FK,
	RigUI_Settings_Face,
	RigUI_Settings_Misc,
	RigUI_Viewport_Display,
)

from bpy.utils import register_class
for c in classes:
	register_class(c)

bpy.types.Object.rig_properties = bpy.props.PointerProperty(type=Rig_Properties)
bpy.types.Object.rig_boolproperties = bpy.props.CollectionProperty(type=Rig_BoolProperties)
bpy.types.Object.rig_colorproperties = bpy.props.CollectionProperty(type=Rig_ColorProperties)

# Certain render settings must be enabled for this character!
bpy.context.scene.eevee.use_ssr = True
bpy.context.scene.eevee.use_ssr_refraction = True
