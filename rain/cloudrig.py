"Version: 2.0"
"19/08/19"

import bpy
from bpy.props import *
import webbrowser

def get_rigs():
	""" Find all MetsRig armatures in the file. """
	ret = []
	armatures = [o for o in bpy.data.objects if o.type=='ARMATURE']
	for o in armatures:
		if("metsrig") in o:
			ret.append(o)
	if(len(ret)==0):
		ret = [None]
	return ret

class MetsRig_BoolProperties(bpy.types.PropertyGroup):
	""" Store a BoolProperty referencing an outfit/character property whose min==0 and max==1.
		This BoolProperty will be used to display the property as a toggle button in the UI.
	"""
	# This is currently only used for outfit/character settings, NOT rig settings. Those booleans are instead hard-coded into metsrig_properties.

	def update_id_prop(self, context):
		""" Callback function to update the corresponding ID property when this BoolProperty's value is changed. """
		rig = self.rig
		metsrig_props = rig.metsrig_properties
		outfit_bone = rig.pose.bones.get("Properties_Outfit_"+metsrig_props.metsrig_outfits)
		char_bone = rig.pose.bones.get("Properties_Character_"+metsrig_props.metsrig_chars)
		for prop_owner in [outfit_bone, char_bone]:
			if(prop_owner != None):
				if(self.name in prop_owner):
					prop_owner[self.name] = self.value
	
	rig: PointerProperty(type=bpy.types.Object)
	value: BoolProperty(
		name='Boolean Value',
		description='',
		update=update_id_prop
	)

class MetsRig_Properties(bpy.types.PropertyGroup):
	# PropertyGroup for storing MetsRig related properties in.
	# Character and Outfit specific properties will still be stored in their relevant Properties bones (eg. Properties_Outfit_Ciri_Default).
	
	def get_rig(self):
		""" Find the armature object that is using this instance of MetsRig_Properties. """

		for rig in get_rigs():
			if(rig.metsrig_properties == self):
				return rig

	@classmethod
	def pre_depsgraph_update(cls, scene):
		""" Runs before every depsgraph update. Is used to handle user input by detecting changes in the rig properties. """
		
		# The pinned rig should store the most recently selected metsrig.
		if(bpy.context.object in get_rigs()):
			scene['metsrig_pinned'] = bpy.context.object
		if(scene['metsrig_pinned'] == None):
			scene['metsrig_pinned'] = get_rigs()[0] # Can be None, only when no metsrigs are in the scene.

	def update_bool_properties(self, context):
		""" Create BoolProperties out of those outfit/character properties whose min==0 and max==1.
			These BoolProperties are necessarry because only BoolProperties can be displayed in the UI as toggle buttons.
		"""
		
		rig = self.get_rig()
		bool_props = rig.metsrig_boolproperties
		bool_props.clear()	# Nuke all the bool properties
		
		outfit_bone = rig.pose.bones.get("Properties_Outfit_" + self.metsrig_outfits)
		character_bone = rig.pose.bones.get("Properties_Character_" + self.metsrig_chars)
		for prop_owner in [outfit_bone, character_bone]:
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
		""" Callback function for finding the list of available outfits for the metsrig_outfits enum. """
		rig = self.get_rig()
		chars = [self.metsrig_chars]
		if(self.metsrig_sets == 'Generic'):
			chars = ['Generic']
		elif(self.metsrig_sets == 'All'):
			chars = [b.name.replace("Properties_Character_", "") for b in rig.pose.bones if "Properties_Character_" in b.name]
		
		outfits = []
		for char in chars:
			char_bone = rig.pose.bones.get("Properties_Character_"+char)
			if(not char_bone): continue
			outfits.extend([c.name.replace("Properties_Outfit_", "") for c in char_bone.children if "Properties_Outfit_" in c.name])
		
		items = []
		for i, outfit in enumerate(outfits):
			items.append((outfit, outfit, outfit, i))	# Identifier, name, description, can all be the character name.
		
		# If no outfits were found, don't return an empty list so the console doesn't spam "'0' matches no enum" warnings.
		if(items==[]):
			return [(('identifier', 'name', 'description'))]
		
		return items
	
	def chars(self, context):
		""" Callback function for finding the list of available chars for the metsrig_chars enum. """
		items = []
		chars = [b.name.replace("Properties_Character_", "") for b in self.get_rig().pose.bones if "Properties_Character_" in b.name]
		for char in chars:
			if(char=='Generic'): continue
			items.append((char, char, char))
		
		# If no characters were found, don't return an empty list so the console doesn't spam "'0' matches no enum" warnings.
		if(items==[]):
			return [(('identifier', 'name', 'description'))]
		
		return items
	
	def hairs(self, context):
		""" Callback function for finding the list of available hairs for the metsrig_hairs enum. """
		rig = self.get_rig()
		hairs = []
		char_bones = [b for b in rig.pose.bones if "Properties_Character_" in b.name]
		outfit_bones = [b for b in rig.pose.bones if "Properties_Outfit_" in b.name]
		for bone in char_bones+outfit_bones:
			if("Hair" not in bone): continue
			bone_hairs = bone['Hair'].split(", ")
			for bh in bone_hairs:
				if(bh not in hairs):
					hairs.append(bh)
		
		items = [('None', 'None', 'None')]
		for hair in hairs:
			items.append((hair, hair, hair))
		return items
	
	def change_outfit(self, context):
		""" Update callback of metsrig_outfits enum. """
		
		rig = self.get_rig()
		char_bone = rig.pose.bones.get("Properties_Character_"+self.metsrig_chars)
		
		if( (self.metsrig_outfits == '') ):
			self.metsrig_outfits = self.outfits(context)[0][0]
		
		outfit_bone = rig.pose.bones.get("Properties_Outfit_"+self.metsrig_outfits)

		if('Hair' in char_bone):
			self.metsrig_hairs = char_bone['Hair'].split(", ")[0]
		if('Hair' in outfit_bone):
			self.metsrig_hairs = outfit_bone['Hair']
		
		self.update_bool_properties(context)

	def change_characters(self, context):
		""" Update callback of metsrig_chars enum. """
		rig = self.get_rig()
		char_bone = rig.pose.bones.get("Properties_Character_"+self.metsrig_chars)
		
		self.change_outfit(context)
	
	metsrig_chars: EnumProperty(
		name="Character",
		items=chars,
		update=change_characters)
	
	metsrig_sets: EnumProperty(
		name="Outfit Set",
		description = "Set of outfits to choose from",
		items={
			('Character', "Canon Outfits", "Outfits of the selected character", 1),
			('Generic', "Generic Outfits", "Outfits that don't belong to a character", 2),
			('All', "All Outfits", "All outfits, including those of other characters", 3)
		},
		default='Character',
		update=change_outfit)
	
	metsrig_outfits: EnumProperty(
		name="Outfit",
		items=outfits,
		update=change_outfit)
	
	metsrig_hairs: EnumProperty(
		name="Hairstyle",
		items=hairs)

	render_modifiers: BoolProperty(
		name='render_modifiers',
		description='Enable SubSurf, Solidify, Bevel, etc. modifiers in the viewport')
	use_proxy: BoolProperty(
		name='use_proxy',
		description='Use Proxy Meshes')

	### BOOLEANS ### - Since custom properties cannot be displayed as toggles, I'm hardcoding anything that needs toggle buttons. This is pretty ugly so hopefully one day we can either display integers custom props as toggle buttons or have real boolean custom props.
	neck_hinge: BoolProperty()
	head_hinge: BoolProperty()

class MetsRigUI(bpy.types.Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'MetsRig'
	
	@classmethod
	def poll(cls, context):
		return 'metsrig_pinned' in bpy.context.scene and bpy.context.scene['metsrig_pinned'] != None
	
	def draw(self, context):
		layout = self.layout

class MetsRigUI_Properties(MetsRigUI):
	bl_idname = "OBJECT_PT_metsrig_ui_properties"
	bl_label = "Outfits"

	@classmethod
	def poll(cls, context):
		if(not super().poll(context)):
			return False
		# Only display this panel if there is either an outfit with options, multiple outfits, or multiple characters.
		rig = context.scene['metsrig_pinned']
		if(not rig): return False
		mets_props = rig.metsrig_properties
		bool_props = rig.metsrig_boolproperties
		multiple_chars = len(mets_props.chars(context)) > 1	# Whether the rig has multiple characters. If not, we won't display Character and OutfitSet menus.
		multiple_outfits = len(mets_props.outfits(context)) > 1
		outfit_properties_bone = rig.pose.bones.get("Properties_Outfit_"+mets_props.metsrig_outfits)
		character_properties_bone = rig.pose.bones.get("Properties_Character_"+mets_props.metsrig_chars)
		outfit_properties_exist = False
		character_properties_exist = False
		if(outfit_properties_bone):
			keys = [k for k in outfit_properties_bone.keys() if not k.startswith("_")]
			outfit_properties_exist = len(keys) > 0
		if(character_properties_bone):
			keys = [k for k in character_properties_bone.keys() if not k.startswith("_")]
			character_properties_exist = len(keys) > 0

		return multiple_chars or multiple_outfits or outfit_properties_exist or character_properties_exist

	def draw(self, context):
		layout = self.layout
		rig = context.scene['metsrig_pinned']
		
		self.bl_label = rig.name

		mets_props = rig.metsrig_properties
		bool_props = rig.metsrig_boolproperties
		
		character = mets_props.metsrig_chars
		multiple_chars = len(mets_props.chars(context)) > 1
		
		character_properties_bone = rig.pose.bones.get("Properties_Character_"+character)
		outfitset = mets_props.metsrig_sets
		outfit = mets_props.metsrig_outfits
		outfit_properties_bone = rig.pose.bones.get("Properties_Outfit_"+outfit)

		if(multiple_chars):
			self.bl_label = "Characters and Outfits"
			layout.prop(mets_props, 'metsrig_chars')
		
		def add_props(prop_owner):
			""" Add all properties of prop_owner to the layout. 
				A property hierarchy can be specified in a property named 'prop_hierarchy'.
				It needs to be a string:list_of_strings dictionary, where string is the parent and list_of_strings are the children.
				For example this is the prop_hierarchy of the outfit "Ciri_Default":
				{"Corset" : ["Back_Pouch", "Belt_Medallion", "Dagger", "Front_Pouch", "Squares"], "Hood-23" : ["Coat"]}
				(The Coat child of Hood only shows up when Hood is 2 or 3) - TODO This is pretty messy
			"""
		
			# Drawing properties with hierarchy
			props_done = []
			if( 'prop_hierarchy' in prop_owner ):
				prop_hierarchy = eval(prop_owner['prop_hierarchy'])
				
				for parent_prop_name in prop_hierarchy.keys():
					if( parent_prop_name == '_RNA_UI' ): continue
					parent_prop_name_without_values = parent_prop_name	# VERBOSE AF
					values = [1]	# Values which this property needs to be for its children to show. For bools this is always 1.
					# Preparing parenting to non-bool properties. In prop_hierarchy the convention for these is "Prop_Name-###".
					if('-' in parent_prop_name):
						split = parent_prop_name.split('-')
						parent_prop_name_without_values = split[0]
						values = [int(val) for val in split[1]]	# Convert them to an int list ( eg. '23' -> [2, 3] )
					
					parent_prop_value = prop_owner[parent_prop_name_without_values]
					
					icon = 'TRIA_DOWN' if parent_prop_value in values else 'TRIA_RIGHT'
					# Drawing parent prop, if it wasn't drawn yet.
					if(parent_prop_name_without_values not in props_done):
						if(parent_prop_name_without_values in bool_props):
							bp = bool_props[parent_prop_name_without_values]
							layout.prop(bp, 'value', toggle=True, text=bp.name.replace("_", " "), icon=icon)
						else:
							layout.prop(prop_owner, '["'+parent_prop_name_without_values+'"]', slider=True, text=parent_prop_name_without_values.replace("_", " "))
					
					# Marking parent prop as done drawing.
					props_done.append(parent_prop_name_without_values)
					
					# Marking child props as done drawing. (Before they're drawn, since if the parent is disabled, we don't want to draw them.)
					for child_prop_name in prop_hierarchy[parent_prop_name]:
						props_done.append(child_prop_name)
					
					# Checking if we should draw children.
					if(parent_prop_value not in values): continue
					
					# Drawing children.
					childrens_box = layout.box()
					for child_prop_name in prop_hierarchy[parent_prop_name]:
						if(child_prop_name in bool_props):
							bp = bool_props[child_prop_name]
							childrens_box.prop(bp, 'value', toggle=True, text=bp.name)
						else:
							childrens_box.prop(prop_owner, '["'+child_prop_name+'"]')
			
			# Drawing properties without hierarchy
			for prop_name in prop_owner.keys():
				if( prop_name in props_done or prop_name.startswith("_") ): continue
				# Int Props
				if(prop_name not in bool_props and type(prop_owner[prop_name]) in [int, float] ):
					layout.prop(prop_owner, '["'+prop_name+'"]', slider=True, text=prop_name.replace("_", " "))
			# Bool Props
			for bp in bool_props:
				if(bp.name in prop_owner.keys() and bp.name not in props_done):
					layout.prop(bp, 'value', toggle=True, text=bp.name.replace("_", " "))
		
		if( character_properties_bone != None ):
			add_props(character_properties_bone)
			layout.separator()

		if(multiple_chars):
			layout.prop(mets_props, 'metsrig_sets')
		layout.prop(mets_props, 'metsrig_outfits')
		
		if( outfit_properties_bone != None ):
			add_props(outfit_properties_bone)

class MetsRigUI_Layers(MetsRigUI):
	bl_idname = "OBJECT_PT_metsrig_ui_layers"
	bl_label = "Rig Layers"
	
	def draw(self, context):
		layout = self.layout
		rig = context.scene['metsrig_pinned']
		data = rig.data
		
		row_ik = layout.row()
		row_ik.column().prop(data, 'layers', index=0, toggle=True, text='Body IK')
		row_ik.column().prop(data, 'layers', index=16, toggle=True, text='Body IK Secondary')
		
		layout.row().prop(data, 'layers', index=1, toggle=True, text='Body FK')
		layout.row().prop(data, 'layers', index=17, toggle=True, text='Body Stretch')
		
		row_face = layout.row()
		row_face.column().prop(data, 'layers', index=2, toggle=True, text='Face Main')
		row_face.column().prop(data, 'layers', index=18, toggle=True, text='Face Secondary')
		
		row_fingers = layout.row()
		row_fingers.column().prop(data, 'layers', index=3, toggle=True, text='Finger Controls')
		row_fingers.column().prop(data, 'layers', index=19, toggle=True, text='Finger Stretch')
		
		layout.row().prop(data, 'layers', index=6, toggle=True, text='Hair')
		layout.row().prop(data, 'layers', index=7, toggle=True, text='Clothes')
		
		layout.separator()
		if('dev' in rig and rig['dev']==1):
			row_mechanism = layout.row()
			row_mechanism.prop(data, 'layers', index=8, toggle=True, text='Body Mechanism')
			row_mechanism.prop(data, 'layers', index=9, toggle=True, text='Body Adjust Mechanism')
			row_mechanism.prop(data, 'layers', index=10, toggle=True, text='Face Mechanism')
			
			row_deform = layout.row()
			row_deform.prop(data, 'layers', index=24, toggle=True, text='Body Deform')
			row_deform.prop(data, 'layers', index=25, toggle=True, text='Body Adjust Deform')
			row_deform.prop(data, 'layers', index=26, toggle=True, text='Face Deform')

			death_row = layout.row()
			death_row.prop(data, 'layers', index=30, toggle=True, text='Properties')
			death_row.prop(data, 'layers', index=31, toggle=True, text='Black Box')

class MetsRigUI_IKFK(MetsRigUI):
	bl_idname = "OBJECT_PT_metsrig_ui_ik"
	bl_label = "FK/IK Settings"
	
	def draw(self, context):
		layout = self.layout
		column = layout.column()
		rig = context.scene['metsrig_pinned']
		mets_props = rig.metsrig_properties
		ikfk_props = rig.pose.bones.get('Properties_IKFK')
		face_props = rig.pose.bones.get('Properties_Face')
		
		# TODO improve the overall organization for all these buttons.
		
		### FK/IK Switch Sliders
		layout.label(text='FK/IK Switches')

		# Spine
		layout.row().prop(ikfk_props, '["ik_spine"]', slider=True, text='Spine')
		
		# Arms
		arms_row = layout.row()
		arms_row.prop(ikfk_props, '["ik_arm_left"]', slider=True, text='Left Arm')
		arms_row.prop(ikfk_props, '["ik_arm_right"]', slider=True, text='Right Arm')
		
		# Legs
		legs_row = layout.row()
		legs_row.prop(ikfk_props, '["ik_leg_left"]', slider=True, text='Left Leg')
		legs_row.prop(ikfk_props, '["ik_leg_right"]', slider=True, text='Right Leg')

		# IK Stretch
		layout.label(text='IK Stretch')
		layout.row().prop(ikfk_props, '["ik_stretch_spine"]', slider=True, text='Stretchy Spine')
		layout.row().prop(ikfk_props, '["ik_stretch_arms"]', slider=True, text='Stretchy Arms')
		layout.row().prop(ikfk_props, '["ik_stretch_legs"]', slider=True, text='Stretchy Legs')

		# IK Hinge
		layout.label(text='IK Hinge')
		hand_row = layout.row()
		hand_row.column().prop(ikfk_props, '["ik_hinge_hand_left"]', slider=True, text='Left Hand')
		hand_row.column().prop(ikfk_props, '["ik_hinge_hand_right"]', slider=True, text='Right Hand')
		foot_row = layout.row()
		foot_row.column().prop(ikfk_props, '["ik_hinge_foot_left"]', slider=True, text='Left Foot')
		foot_row.column().prop(ikfk_props, '["ik_hinge_foot_right"]', slider=True, text='Right Foot')
		
		# FK Hinge
		layout.label(text='FK Hinge')
		
		hand_row = layout.row()
		hand_row.column().prop(ikfk_props, '["fk_hinge_arm_left"]', slider=True, text='Left Arm')
		hand_row.column().prop(ikfk_props, '["fk_hinge_arm_right"]', slider=True, text='Right Arm')
		foot_row = layout.row()
		foot_row.column().prop(ikfk_props, '["fk_hinge_leg_left"]', slider=True, text='Left Leg')
		foot_row.column().prop(ikfk_props, '["fk_hinge_leg_right"]', slider=True, text='Right Leg')

		# IK Parents
		layout.label(text='IK Parents')
		arm_parent_row = layout.row()
		arm_parents = ['Root', 'Pelvis', 'Chest', 'Arm']
		arm_parent_row.column().prop(ikfk_props, '["ik_parents_arm_left"]', slider=True, text='Left Hand ['+arm_parents[ikfk_props["ik_parents_arm_left"]] + "]")
		arm_parent_row.column().prop(ikfk_props, '["ik_parents_arm_right"]', slider=True, text='Right Hand ['+arm_parents[ikfk_props["ik_parents_arm_right"]] + "]")
		leg_parent_row = layout.row()
		leg_parents = ['Root', 'Pelvis', 'Hips', 'Leg']
		leg_parent_row.column().prop(ikfk_props, '["ik_parents_leg_left"]', slider=True, text='Left Foot ['+leg_parents[ikfk_props["ik_parents_leg_left"]] + "]")
		leg_parent_row.column().prop(ikfk_props, '["ik_parents_leg_right"]', slider=True, text='Right Foot ['+leg_parents[ikfk_props["ik_parents_leg_right"]] + "]")

		# IK Pole Follow
		layout.label(text='IK Pole Follow')
		pole_row = layout.row()
		# TODO: This should be real toggles...
		pole_row.column().prop(ikfk_props, '["ik_pole_follow_hands"]', toggle=True, text='Arms')
		pole_row.column().prop(ikfk_props, '["ik_pole_follow_feet"]', toggle=True, text='Legs')

		layout.label(text='Head Settings')
		layout.row().prop(mets_props, 'neck_hinge', toggle=True, text='Neck Hinge')
		head_hinge_row = layout.row()
		head_hinge_row.enabled = mets_props.neck_hinge
		head_hinge_row.prop(mets_props, 'head_hinge', toggle=True, text='Head Hinge')
		layout.row().prop(face_props, '["head_look"]', slider=True, text='Head Look')
		head_parents = ['Root', 'Pelvis', 'Chest']
		layout.row().prop(face_props, '["head_target_parents"]', slider=True, text='Head Target Parent ['+head_parents[face_props["head_target_parents"]] + "]")

		# Face settings
		layout.label(text='Face Settings')
		layout.row().prop(face_props, '["sticky_eyelids"]', text='Sticky Eyelids', slider=True)
		layout.row().prop(face_props, '["sticky_eyesockets"]', text='Sticky Eyerings', slider=True)

class MetsRigUI_Extras(MetsRigUI):
	bl_idname = "OBJECT_PT_metsrig_ui_extras"
	bl_label = "Extras"
	
	def draw(self, context):
		layout = self.layout
		rig = context.scene['metsrig_pinned']
		mets_props = rig.metsrig_properties
	
		layout.row().prop(mets_props, 'render_modifiers', text='Enable Modifiers', toggle=True)
		layout.row().prop(mets_props, 'use_proxy', text='Use Proxy Meshes', toggle=True)

class MetsRigUI_Extras_Physics(MetsRigUI):
	bl_idname = "OBJECT_PT_metsrig_ui_extras_physics"
	bl_label = "Physics"
	bl_parent_id = "OBJECT_PT_metsrig_ui_extras"
	
	def draw_header(self, context):
		rig = context.scene['metsrig_pinned']
		mets_props = rig.metsrig_properties
		layout = self.layout
		layout.prop(mets_props, "physics_toggle", text="")
	
	def draw(self, context):
		rig = context.scene['metsrig_pinned']
		mets_props = rig.metsrig_properties
		layout = self.layout
		
		layout.active = mets_props.physics_toggle
		
		cache_row = layout.row()
		cache_row.label(text="Cache: ")
		cache_row.prop(mets_props, 'physics_cache_start', text="Start")
		cache_row.prop(mets_props, 'physics_cache_end', text="End")
		
		mult_row = layout.row()
		mult_row.label(text="Apply Speed Multiplier:")
		mult_row.prop(mets_props, 'physics_speed_multiplier', text="")
		
		layout.operator("ptcache.bake_all", text="Bake All Dynamics").bake = True
		layout.operator("ptcache.free_bake_all", text="Delete All Bakes")

class Link_Button(bpy.types.Operator):
	"""Open a link in a web browser"""
	bl_idname = "ops.open_link"
	bl_label = "Open a link in web browser"
	bl_options = {'REGISTER'}
	
	url: StringProperty(name='URL',
		description="URL",
		default="http://blender.org/"
	)

	def execute(self, context):
		webbrowser.open_new(self.url) # opens in default browser
		return {'FINISHED'}

class MetsRigUI_Links(MetsRigUI):
	bl_idname = "OBJECT_PT_metsrig_ui_support"
	bl_label = "Links"
	
	url_cloud = "https://cloud.blender.org/welcome"
	url_dev_fund = "https://fund.blender.org/"
	url_dev_blog = "https://code.blender.org/"
	url_blender_chat = "https://blender.chat/"
	
	def draw(self, context):
		layout = self.layout
		
		cloud_button = layout.operator('ops.open_link', text="Blender Cloud")
		cloud_button.url = self.url_cloud
		#cloud_button.description = "Subscribe to the Blender Cloud!" #TODO: Can I have unique descriptions per button? I think not, but would be nice.
		fund_button = layout.operator('ops.open_link', text="Blender Dev Fund")
		fund_button.url = self.url_dev_fund
		blog_button = layout.operator('ops.open_link', text="Blender Dev Blog")
		blog_button.url = self.url_dev_blog
		chat_button = layout.operator('ops.open_link', text="Blender Chat")
		chat_button.url = self.url_blender_chat

classes = (
	MetsRig_Properties, 
	MetsRig_BoolProperties,
	MetsRigUI_Properties, 
	MetsRigUI_Layers, 
	MetsRigUI_IKFK, 
	MetsRigUI_Extras, 
	Link_Button, 
	MetsRigUI_Links
)

from bpy.utils import register_class
for c in classes:
	register_class(c)

bpy.types.Object.metsrig_properties = bpy.props.PointerProperty(type=MetsRig_Properties)
bpy.types.Object.metsrig_boolproperties = bpy.props.CollectionProperty(type=MetsRig_BoolProperties)

bpy.app.handlers.depsgraph_update_pre.append(MetsRig_Properties.pre_depsgraph_update)