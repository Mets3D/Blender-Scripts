"Version: 1.0"
"18/11/19"

import bpy
from bpy.props import *

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
		ikfk_props = rig.pose.bones.get('Properties_IKFK')

		layout.row().prop(ikfk_props, '["ik_spine"]', slider=True, text='Spine')
		arms_row = layout.row()
		arms_row.prop(ikfk_props, '["ik_arm_left"]', slider=True, text='Left Arm')
		arms_row.prop(ikfk_props, '["ik_arm_right"]', slider=True, text='Right Arm')
		legs_row = layout.row()
		legs_row.prop(ikfk_props, '["ik_leg_left"]', slider=True, text='Left Leg')
		legs_row.prop(ikfk_props, '["ik_leg_right"]', slider=True, text='Right Leg')

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
	RigUI_Settings_FKIK,
	RigUI_Settings_FKIK_Switch,
	RigUI_Settings_IK,
	RigUI_Settings_FK,
	RigUI_Settings_Face,
	RigUI_Settings_Misc,
	RigUI_Viewport_Display,
	Reset_Rig_Colors
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
