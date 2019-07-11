"Version: 1.1"
"05/07/19"

import bpy
from bpy.props import *
from mathutils import Vector
import time
import webbrowser

#TODO:
# Physics settings should only show up if a Physics collection is specified in the armature's custom properties. This could be called 'phys_collection'.
# Instead of checking for any collection named 'phys' belonging to the armature's collection(which is super dirty), we should check for any collection in the scene matching the value of that custom property.

# Modularity
# The rig script and UI should start functioning as soon as the metsrig custom property is added to the armature.
# Every other information should be able to be provided without the rig creator having to hard code it(although some python syntax will probably have to be used in the custom properties), such as characters, outfits, bone layer names and layout(TODO).

# Constraints
# TODO: If a constraint has multiple "names" but is meant to have an influence other than 0 or 1, and only its visibility should be toggled, the influence gets changed anyways.
# Might need to do a thing where the constraint name is instead an expression for the influence. This would make more sense considering other things as well.
# Alternatively, these constraints could just have a driver on their influence that forces it to a constant value.
# But at that point, we might as well just have a driver on the influence that sets the damn influence. But that wouldn't align with the modular design of the rig which is still WIP.

# prop_hierarchy: allow for nested children
# Objects should be responsible for enabling mask vertex groups on the body(or everything), as opposed to the vertex groups being responsible for enabling themselves based on rig properties.
#	Except some objects get masked to make other versions of themselves, so some objects would have multiple masks to enable depending on rig properties.

# Optimization
	# Could try limiting update_meshes() and update_node_values() to only worry about changed properties.
		# This would be done by finding a list of the changed properties in pre_depsgraph_update() and then passing those in as params.
		# This would enable users to manually enable/disable things, then interact with the rig, and not lose their manual modifications.
		# There would need to be a button to refresh the entire rig though (which would probably happen by not passing the optional param from pre_depsgraph_update() into update_meshes() ).

# Animation
	# Currently when values are animated, outfits don't update, since just because something is animated it doesn't call a depsgraph update when animation is played or timeline is scrubbed. We might need to run pre_depsgraph_uipdate() on frame change instead of depsgraph update, which would probably affect performance.
	# I think even properties' update callbacks only run when the user changes them, not when animation changes them. Isn't that a bug?
	# In any case, for cloth swapping to work with animation, we might need to check for changes on both ID and other properties on frame change. Yikes.

# Linking/Appending
	# The rig should detect when itself is a proxy and be aware of what rig it is a proxy of. Use that rig's children instead of the proxy armature's(presumably non-existent) children.
	# It should also detect when multiple copies of itself exist. Currently the only thing that needs to be done for two rigs to work without messing each other up is to change the 'material_controller' to the correct one.

def get_children_recursive(obj, ret=[]):
	# Return all the children and children of children of obj in a flat list.
	for c in obj.children:
		if(c not in ret):
			ret.append(c)
		ret = get_children_recursive(c, ret)
	
	return ret


def get_rigs():
	""" Find all MetsRigs in the current view layer. """
	ret = []
	armatures = [o for o in bpy.context.view_layer.objects if o.type=='ARMATURE']
	for o in armatures:
		if("metsrig") in o.data:
			ret.append(o)
	return ret

class MetsRig_BoolProperties(bpy.types.PropertyGroup):
	""" Store a BoolProperty referencing an outfit/character property whose min==0 and max==1.
		This BoolProperty will be used to display the property as a toggle button in the UI.
	"""
	
	def update_id_prop(self, context):
		""" Callback function to update the ID property when this BoolProperty's value is changed.
		"""
		if( self.rig == None ): return
		metsrig_props = self.rig.data.metsrig_properties
		
		outfit_bone = self.rig.pose.bones.get("Properties_Outfit_"+metsrig_props.metsrig_outfits)
		char_bone = self.rig.pose.bones.get("Properties_Character_"+metsrig_props.metsrig_chars)
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
		""" Find the rig that is using this instance. """
		for rig in get_rigs():
			if(rig.data.metsrig_properties == self):
				return rig
	
	@classmethod
	def pre_depsgraph_update(cls, scene):
		""" Runs before every depsgraph update. Is used to handle user input by detecting changes in the rig properties. """
		for rig in get_rigs():
			# Grabbing relevant data
			mets_props = rig.data.metsrig_properties
			character_bone = rig.pose.bones.get("Properties_Character_"+mets_props.metsrig_chars)
			outfit_bone = rig.pose.bones.get("Properties_Outfit_"+mets_props.metsrig_outfits)
			
			if('update' not in rig.data):
				rig.data['update'] = 0
			if('prev_props' not in rig.data):
				rig.data['prev_props'] = ""
			
			# Saving those properties into a list of dictionaries. 
			current_props = [{}, {}, {}]
			
			saved_types = [int, float]	# Types of properties that we save for user input checks.
			def save_props(prop_owner, list_id):
				for p in prop_owner.keys():
					if(p=='_RNA_UI' or p=='prev_props'): continue	# TODO this check would be redundant if we didn't save strings, and the 2nd part is already redundant due to next line.
					if(type(prop_owner[p]) not in saved_types): continue
					if(p=="prop_hierarchy"): continue
					current_props[list_id][p] = prop_owner[p]
			
			if(character_bone):
				save_props(character_bone, 0)
			#else:
			#	print("Warning: Character bone for " + mets_props.metsrig_chars + " not found. It needs to be named 'Properties_Character_CharName'.")
			if(outfit_bone):
				save_props(outfit_bone, 1)
			#else:
			#	print("Warning: Outfit bone for " + mets_props.metsrig_outfits + " not found. It should be named 'Properties_Outfit_OutfitName' and its parent should be the character bone.")
			save_props(rig.data, 2)
			
			# Retrieving the list of dictionaries from the ID Property - have to use to_dict() on each dictionary due to the way ID properties... are.
			prev_props = []
			if(rig.data['prev_props'] != ""):
				prev_props = [
					rig.data['prev_props'][0].to_dict(), 
					rig.data['prev_props'][1].to_dict(), 
					rig.data['prev_props'][2].to_dict(), 
				]
			
			# Finally, we compare the current and previous properties.
			# If they do not match, that means there was user input, and it's time to update stuff.
			if( current_props != prev_props ):
				# Materials need to update before the depsgraph update, otherwise they will not update even in rendered view.
				rig.data.metsrig_properties.update_node_values(bpy.context)
				rig.data['prev_props'] = [current_props[0], current_props[1], current_props[2]]
				# However, updating meshes before depsgraph update will cause an infinite loop, so we use a flag to let post_depsgraph_update know that it should update meshes.
				rig.data['update'] = 1

	@classmethod
	def post_depsgraph_update(cls, scene):
		"""Runs after every depsgraph update. If any user input to the rig properties was detected by pre_depsgraph_update(), this will call update_meshes(). """
		for rig in get_rigs():
			if(rig.data['update'] == 1):
				rig.data.metsrig_properties.update_meshes(bpy.context)
				rig.data['update'] = 0
	
	def determine_visibility_by_expression(self, o):
		""" Determine whether an object should be visible based on its Expression custom property.
			Expressions will recognize any character or outfit property names as variables.
			'Character', 'Outfit' and 'Hair' are special variables that will correspond to the currently selected things.
			Example expression: "Outfit=='Ciri_Default' and Hood==1"
			o: object to determine stuff on.
		"""
		rig = self.get_rig()
		outfit_bone = rig.pose.bones.get('Properties_Outfit_' + self.metsrig_outfits)
		character_bone = rig.pose.bones.get('Properties_Character_' + self.metsrig_chars)
		
		# Replacing the variable names in the expression with the corresponding variables' values.
		
		expression = o['Expression']
		if( ('Outfit' not in expression) and ('Character' not in expression) and ('Hair' not in expression) ): 
			print("Warning: invalid expression - no 'Outfit', 'Character' or 'Hair' found. " + o.name)
			return None
		expression = expression.replace('Outfit', "'" + self.metsrig_outfits + "'")
		expression = expression.replace('Character', "'" + self.metsrig_chars + "'")
		expression = expression.replace('Hair', "'" + self.metsrig_hairs + "'")
		
		bones = [outfit_bone, character_bone]
		found_anything=False
		for bone in bones:
			for prop_name in bone.keys():
				if(prop_name in expression):
					found_anything = True
					expression = expression.replace(prop_name, str(bone[prop_name]))
		
		#if(not found_anything):
		#	return False
		
		try:
			ret = eval(expression)
			return ret
		except NameError:	# When the variable name in an expression doesn't get replaced by its value because the object doesn't belong to the active outfit.
			return False
	
	def determine_visibility_by_properties(self, o):
		""" Determine whether an object should be visible by matching its custom properties to the active character and outfit properties. """
		rig = self.get_rig()
		char_bone = rig.pose.bones.get("Properties_Character_"+self.metsrig_chars)
		outfit_bone = rig.pose.bones.get("Properties_Outfit_"+self.metsrig_outfits)
		
		if("Hair" in o):
			if( self.metsrig_hairs != o['Hair'] ):
				return False
		
		if("Character" in o):
			chars = o['Character'].split(", ")
			if(self.metsrig_chars not in chars):
				return False
		if("Outfit" in o):
			outfits = o['Outfit'].split(", ")
			if(self.metsrig_outfits not in outfits):
				return False
		
		for prop_bone in [char_bone, outfit_bone]:
			for prop_name in o.keys():
				if( (prop_name == '_RNA_UI') or (prop_name not in prop_bone) ): continue
				
				prop_value = prop_bone[prop_name]	# Value of the property on the properties bone. Changed by the user via the UI.
				requirement = o[prop_name]					# Value of the property on the object. This defines what the property's value must be in order for this object to be visible.
				
				# Checking if the property value fits the requirement...
				if(type(requirement)==int):
					if(not prop_value == requirement):
						
						return False
				elif('IDPropertyArray' in str(type(requirement))):
					if(not prop_value in requirement.to_list()):
						return False
				elif(type(requirement)==str):
					if('#' not in requirement): continue
					if(not eval(requirement.replace("#", str(prop_value)))):
						return False
				else:
					print("Error: Unsupported property type: " + str(type(requirement)) + " of property: " + p + " on object: " + o.name)
		
		# If we got this far without returning False, then all the properties matched and this object should be visible.
		return True
		
	def determine_object_visibility(self, o):
		""" Determine if an object should be visible based on its properties and the rig's current state. """

		if('Expression' in o):
			if( ('Hair' in o) or ('Outfit' in o) or ('Character' in o) ):
				if( self.determine_visibility_by_properties(o) ):
					return self.determine_visibility_by_expression(o)
				else:
					# This lets us combine expressions and outfits, which is mainly useful to let us debug expressions.
					# This way, even if there is an expression, we check for hair/outfit/character first, and if those don't match, we don't have to run the expression.
					return False
			else:
				return self.determine_visibility_by_expression(o)
		elif( ('Hair' in o) or ('Outfit' in o) or ('Character' in o) ):
			return self.determine_visibility_by_properties(o)
		else:
			return None
		
	def determine_visibility_by_name(self, m, obj=None):
		""" Determine whether the passed vertex group or shape key should be enabled, based on its name and the properties of the currently active outfit.
			Naming convention example: M:Ciri_Default:Corset==1*Top==1
			m: The vertex group or shape key (or anything with a "name" property).
			THIS CODE IS REALLY FUCKING BAD
		"""
		
		if("M:" not in m.name):
			return None
		
		# Gathering data
		rig = self.get_rig()
		active_outfit = self.metsrig_outfits
		outfit_bone = rig.pose.bones.get('Properties_Outfit_' + active_outfit)
		active_character = self.metsrig_chars
		character_bone = rig.pose.bones.get('Properties_Character_' + active_character)
		
		if(outfit_bone==None):
			return None
	
		parts = m.name.split(":")	# The 3 parts: "M" to indicate it's a mask, the outfit/character names, and the expression.
		prop_owners = parts[1].split(",")	# outfit/characters are divided by ",".
		
		bone = None
		expression = ""
		
		if(len(parts) == 3):
			expression = parts[2]
			found_owner = False
			if(active_outfit in prop_owners):
				bone = outfit_bone
				found_owner=True
			elif(active_character in prop_owners):
				bone = character_bone
				found_owner=True
			else:
				return False
			if(found_owner):
				if(expression in ["True", "False"]):	# Sigh.
					return eval(expression)
		elif(len(parts) == 2):
			bone = outfit_bone
			expression = parts[1]
		else:
			assert False, "Vertex group or shape key name is invalid: " + m.name + " In object: " + obj.name
		
		found_anything = False
		
		for prop_name in bone.keys():
			if(prop_name in expression):
				found_anything = True
				expression = expression.replace(prop_name, str(bone[prop_name]))

		if(not found_anything):
			return None

		try:
			return eval(expression)
		except:
			print("WARNING: Invalid Expression: " + expression + " from object: " + obj.name + " This thing: " + m.name)
	
	def activate_vertex_groups_and_shape_keys(self, obj):
		""" Combines vertex groups with the "Mask" vertex group on all objects belonging to the rig.
			Whether a vertex group is active or not is decided based on its name, using determine_visibility_by_name().
		"""
		if(obj.type!='MESH'): return
		
		mask_vertex_groups = [vg for vg in obj.vertex_groups if self.determine_visibility_by_name(vg, obj)]
		final_mask_vg = obj.vertex_groups.get('Mask')
		if(final_mask_vg):
			for v in obj.data.vertices:
				final_mask_vg.add([v.index], 0, 'REPLACE')
				for mvg in mask_vertex_groups:
					try:
						if(mvg.weight(v.index) > 0):
							final_mask_vg.add([v.index], 1, 'REPLACE')
							break
					except:
						pass
		
		# Toggling shape keys using the same naming convention as the VertexWeightMix modifiers.
		if(obj.data.shape_keys!=None):
			#shapekeys = [sk for sk in obj.data.shape_keys.key_blocks if "M-" in sk.name]
			shapekeys = obj.data.shape_keys.key_blocks
			for sk in shapekeys:
				visible = self.determine_visibility_by_name(sk, obj)
				if(visible != None):
					sk.value = visible
	
	def update_node_values(self, context):
		""" In all materials belonging to this rig, update nodes that correspond to an outfit, character, rig data, or metsrig property.
			eg. when Ciri's "Face" property changes, ensure that the "Face" value node in her material updates.
			Also update the active texture of materials for better feedback while in Solid View.
		"""
		# Gathering relevant data
		rig = self.get_rig()
		outfit_bone = rig.pose.bones.get('Properties_Outfit_'+self.metsrig_outfits)
		char_bone = rig.pose.bones.get('Properties_Character_'+self.metsrig_chars)
		
		# Gathering all the keys and values from outfit, character, main properties and witcher3_properties(self).
		big_dict = {}
		for e in [outfit_bone, char_bone, rig.data, self]:
			if( e==None ): continue
			for k in e.keys():
				if(k=='_RNA_UI'): continue
				value = e[k]
				if( type(value) in [int, float, str] ):
					big_dict[k] = value
				elif('IDPropertyArray' in str(type(value))):
					big_dict[k] = value.to_list()
		
		
		### Looking through every node of every material of every visible object. Trying to keep this optimized.
		objs = list(filter(lambda o: type(o) == bpy.types.Object, get_children_recursive(rig)))
		#objs = [o for o in children if o.hide_viewport==False]	# Errors if objects were deleted.
		
		# Gathering a list of the materials that the visible objects use. Also node groups.
		node_trees = []
		for o in objs:
			try:	# This try block is here because apparently objs contains objects that have potentially been deleted by the user, in which case it throws an error.
				if(o.hide_viewport): continue
			except:
				continue
			for ms in o.material_slots:
				if(ms.material==None): continue
				if(ms.material.node_tree not in node_trees):
					node_trees.append(ms.material.node_tree)

		self.update_material_controller(char_bone)
		self.update_material_controller(outfit_bone)

		def handle_group_node(group_node, active_texture=False):
			""" For finding a node value connected even through reroute nodes, then muting unused texture nodes, and optionally changing the active node to this group_node's active texture. """
			node = group_node
			socket = None
			# Find next connected non-reroute node.
			while True:
				if(len(node.inputs[0].links) > 0):
					next_node = node.inputs[0].links[0].from_node
					
					if(next_node.type == 'REROUTE'):
						node = next_node
						continue
					elif(next_node.type == 'GROUP'):
						if('material_controller' in rig.data and 
						next_node.node_tree.name == rig.data.material_controller):
							# If this is our special Material Controller nodegroup, whose nodetree input default values are exposed to the UI under Extras->Materials.
							# More info about this very confusing system is in update_material_controller().
							socket = next_node.node_tree.inputs[socket.name]
							break
					elif(next_node.type == 'VALUE'):
						node = next_node
						socket = node.outputs[0]
						break
					else:
						break
				else:
					break

			selector_value = 1
			if(n):
				selector_value = int(socket.default_value)
			else:
				print("Warning: Selector value not found - Node probably not connected properly?")
				group_node.label = 'Unconnected Selector'
			# Setting active node for the sake of visual feedback when in Solid view.
			if(len(group_node.inputs[selector_value].links) > 0 ):
				if(active_texture):
					nodes.active = group_node.inputs[selector_value].links[0].from_node
			elif(len(group_node.inputs[1].links) > 0 ):
				if(active_texture):
					nodes.active = group_node.inputs[1].links[0].from_node
				selector_value = 1

			# Muting input texture nodes that we don't need, to help avoid hitting Eevee texture node limits.
			for i in range(1, len(group_node.inputs)):
				chosen_one = i==selector_value
				if(len(group_node.inputs[i].links) > 0 ):
					node = group_node.inputs[i].links[0].from_node
					if(node.type=='TEX_IMAGE'):
						node.mute = i!=selector_value
			
			nodes.active.mute=False

		# Update Value nodes that match the name of a property.
		for nt in node_trees:
			nodes = nt.nodes
			for prop_name in big_dict.keys():
				value = big_dict[prop_name]

				# Checking for expressions (If a property's value is a string starting with "=", it will be evaluated as an expression)
				if(type(value)==str and value.startswith("=")):
					expression = value[1:]
					for var_name in big_dict.keys():
						if(var_name in expression):
							expression = expression.replace(var_name, str(big_dict[var_name]))
					value = eval(expression)

				# Fixing constants (values that shouldn't be exposed to the user but still affect materials should be prefixed with "_".)
				if(prop_name.startswith("_")):
					prop_name = prop_name[1:]
				if(prop_name in nodes):
					#if(prop_name.startswith("_")): continue	# Why did I have this line?
					n = nodes[prop_name]
					# Setting the value of the node to the value of the corresponding property.
					if(type(value) in [int, float]):
						n.outputs[0].default_value = value
					else:
						n.inputs[0].default_value = value[0]
						n.inputs[1].default_value = value[1]
						n.inputs[2].default_value = value[2]

			### Updating active texture for the sake of visual feedback when in Solid view.
			active_color_group = nodes.get('ACTIVE_COLOR_GROUP')
			if(active_color_group):
				handle_group_node(active_color_group, True)
				
			for n in nodes:
				if("SELECTOR_GROUP" in n.name):
					handle_group_node(n)
	
	def update_proxies(self, context):
		# This is WIP code, doesn't work properly yet. TODO (non-proxy mesh doesn't get unhidden)
		# Note: Proxy meshes must be named NameOfObject_Proxy.
		
		rig = self.get_rig()
		use_proxy = rig.data.metsrig_properties.use_proxy
		objs = get_children_recursive(rig)
		for o in objs:
			if('_Proxy' in o.name):
				not_proxy_name = o.name.split("_Proxy")[0]
				not_proxy = next((x for x in objs if x.name == not_proxy_name), None)
				if(not_proxy):
					if(not_proxy.hide_viewport):			# If the base object is hidden to begin with, the proxy should also be hidden.
						o.hide_viewport = True
					else:									# If the base object is visible
						if(use_proxy):						# And proxy is enabled
							not_proxy.hide_viewport = True 	# Hide the base object
							o.hide_viewport = False 		# Unhide the proxy
				else:
					print("Warning: Proxy object has no base object: " + o.name)
					o.hide_viewport = True

	def update_meshes(self, context):
		""" Executes the cloth swapping system by updating object visibilities, mask vertex groups and shape key values. """
		
		def do_child(rig, obj, hide=None):
			# Recursive function to control item visibilities.
			# The object hierarchy assumes that if an object is disabled, all its children should be disabled, that's why this is done recursively.
			
			visible = None
			if(hide!=None):
				visible = not hide
			else:
				visible = self.determine_object_visibility(obj)
			
			if(visible!=None):
				obj.hide_viewport = not visible
				obj.hide_render = not visible
			
			if(obj.hide_viewport == False):
				self.activate_vertex_groups_and_shape_keys(obj)
			else:
				hide = True
			
			# Recursion
			for child in obj.children:
				do_child(rig, child, hide)
		
		hide = False if self.show_all_meshes else None
		
		rig = self.get_rig()
		# Recursively determining object visibilities
		for child in rig.children:
			do_child(rig, child, hide)
		
		#self.update_proxies(context)
			
	def update_bone_location(self, context):
		""" Custom bone locations for each character can be specified in any bone in the rig, by adding a custom property to the bone named "BoneName_CharacterName".
			The value of the custom property has to be a list of 3 floats containing edit_bone coordinates.
			This function will move such bones to the specified coordinates in edit mode.
		"""
		
		rig = self.get_rig()
		rig.data.use_mirror_x = False	# TODO: Currently only the Witcher rig uses this function, and that rig is assymetrical. This causes this function to break stuff if mirroring is turned on. In the future, might need to turn this into a "symmetry" property.
		orig_mode = rig.mode
		bpy.ops.object.mode_set(mode='EDIT')
		
		active_character = self.metsrig_chars
		
		# Moving the bones
		for b in rig.pose.bones:
			# The custom properties' names that store the bone locations are prefixed with the bone's name, eg. "Eye.L_Yennefer"
			# This is necessary because of this bug: https://developer.blender.org/T61386
			# If it ever gets fixed, next line can be changed (along with the custom property names)
			chars = [p.replace(b.name + "_", "") for p in b.keys()]	
			if(active_character not in chars): continue
			edit_bone = rig.data.edit_bones.get(b.name)
			char_vector = b[b.name + "_" + active_character].to_list()
			offset = edit_bone.tail - edit_bone.head
			edit_bone.head = char_vector
			edit_bone.tail = edit_bone.head + offset

		bpy.ops.object.mode_set(mode=orig_mode)
	
	def update_bone_layers(self, context):
		""" Makes sure that outfit/hair bones that aren't being used are on a designated trash layer.
			For this to work, all outfit and hair bones need to be organized into bonegroups named after the hair/outfit itself, prefixed with "Hair_" or "Outfit_" respectively.
		"""
		# Gathering info
		rig = self.get_rig()
		outfit_bone = rig.pose.bones.get('Properties_Outfit_'+self.metsrig_outfits)
		character_bone = rig.pose.bones.get('Properties_Character_'+self.metsrig_chars)
		if(character_bone == None): return	# Every character should have a character bone which should contain at least a "Hair" property.
		
		active_hair = self.metsrig_hairs
		
		# Moving bones to designated layers.
		for b in rig.data.bones:
			bg = rig.pose.bones[b.name].bone_group
			if(bg==None): continue
			
			if('Hair' in bg.name):
				hairs = bg.name.replace("Hair_", "").split(",")
				if(active_hair in hairs ):
					b.layers[10] = True
				else:
					b.layers[10] = False
			elif('Outfit' in bg.name):
				outfits = bg.name.replace("Outfit_", "").split(",")
				if(self.metsrig_outfits in outfits):
					b.layers[9] = True
				else:
					b.layers[9] = False
			elif('Character' in bg.name):
				characters = bg.name.replace("Character_", "").split(",")
				if(self.metsrig_chars in characters):
					b.layers[8] = True
				else:
					b.layers[8] = False

	def update_bool_properties(self, context):
		""" Create BoolProperties out of those outfit/character properties whose min==0 and max==1.
			These BoolProperties are necessarry because only BoolProperties can be displayed in the UI as toggle buttons.
		"""
		
		rig = self.get_rig()
		bool_props = rig.data.metsrig_boolproperties
		bool_props.clear()	# Nuke all the bool properties
		
		outfit_bone = rig.pose.bones.get("Properties_Outfit_" + self.metsrig_outfits)
		character_bone = rig.pose.bones.get("Properties_Character_" + self.metsrig_chars)
		for prop_owner in [outfit_bone, character_bone]:
			if(prop_owner==None): continue
			for p in prop_owner.keys():
				if( type(prop_owner[p]) != int or p.startswith("_") ): continue
				min = prop_owner['_RNA_UI'].to_dict()[p]['min']
				max = prop_owner['_RNA_UI'].to_dict()[p]['max']
				if(min==0 and max==1):
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
	
	def update_material_controller(self, bone):
		# Updating material controller with this character's values.
		rig = self.get_rig()
		if('material_controller' in rig.data):
			controller_nodegroup = bpy.data.node_groups.get(rig.data['material_controller'])
			if(controller_nodegroup):
				# To update the material controller, we set the nodegroup's input default values to the desired values.
				# A nodegroup's input and output default_values are normally ONLY used by Blender to set said values when a new instance of the node is created.
				# Which is to say, changing the input/output default_values won't have any effect on existing nodes.
				# To overcome this, value nodes inside the controller material copy the values of the input/output default_values via drivers.
				
				# Why not just add the Value nodes themselves to the UI? Because they don't have min/max values, but nodegroup inputs/outputs do.
				# Why hook up the input rather than the output? It makes no difference. It just made more sense to me this way.
				for io in [controller_nodegroup.inputs, controller_nodegroup.outputs]:
					for i in io:
						prop_value = None
						if("_" + i.name in bone):
							prop_value = bone["_" + i.name]
						elif(i.name in bone):
							prop_value = bone[i.name]
						else:
							continue
						if( type(prop_value) in [int, float] ):
							i.default_value = prop_value
						else:
							color = prop_value.to_list()
							color.append(1)
							i.default_value = color

	def change_outfit(self, context):
		""" Update callback of metsrig_outfits enum. """
		
		rig = self.get_rig()
		char_bone = rig.pose.bones.get("Properties_Character_"+self.metsrig_chars)
		
		if( (self.metsrig_outfits == '') ):
			self.metsrig_outfits = self.outfits(context)[0][0]
		
		outfit_bone = rig.pose.bones.get("Properties_Outfit_"+self.metsrig_outfits)
		
		if('_body' in outfit_bone):
			rig.data['body'] = outfit_bone['_body']
		elif('_body' in char_bone):
			rig.data['body'] = char_bone['_body']
		else:
			pass
			#rig.data['body'] = 0	#TODO make this work better...

		if('Hair' in char_bone):
			self.metsrig_hairs = char_bone['Hair'].split(", ")[0]
		if('Hair' in outfit_bone):
			self.metsrig_hairs = outfit_bone['Hair']
		else:
			self.update_meshes(context)
			self.update_bone_layers(context)
		
		#self.update_node_values(context)
		self.update_bool_properties(context)

	def change_characters(self, context):
		""" Update callback of metsrig_chars enum. """
		rig = self.get_rig()
		char_bone = rig.pose.bones.get("Properties_Character_"+self.metsrig_chars)
		
		self.update_bone_location(context)
		self.change_outfit(context)				# Just to make sure the active outfit isn't None.

		# TODO: Currently the only character with a unique nude body is Ciri. If another character has a unique body, we'll code this properly.
		if(self.metsrig_chars == 'Ciri'):
			rig.data['body_id'] = 2
		else:
			rig.data['body_id'] = 1
	
	def change_hair(self, context):
		self.update_meshes(context)
		self.update_bone_layers(context)

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
		items=hairs,
		update=change_hair)
	
	def update_physics(self, context):
		""" Handle input to the Physics settings found under MetsRig Extras. """
		
		# Saving and resetting speed multiplier
		speed_mult = 0
		if(self.physics_speed_multiplier != ""):	# This is important to avoid inifnite looping the callback function.
			try:
				speed_mult = float(eval(self.physics_speed_multiplier))
			except ValueError:
				pass
			self.physics_speed_multiplier = ""
	
		rig = self.get_rig()
		
		colors = {
			'CLOTH' : (0, 1, 0, 1),
			'COLLISION' : (1, 0, 0, 1),
		}
		
		for o in bpy.context.view_layer.objects:
			if(o.parent != rig): continue
			
			# Toggling all physics modifiers
			for m in o.modifiers:
				if(	m.type=='CLOTH' or 
					m.type=='COLLISION' or ( 
					"phys" in m.name.lower() and ( 
							( m.type=='MESH_DEFORM' ) or 
							( m.type=='SURFACE_DEFORM') 
						)
					)
				):
					# Change object color and save original
					if(self.physics_toggle and m.type in colors ):
						o['org_color'] = o.color
						o.color = colors[m.type]
					elif('org_color' in o):
						o.color = o['org_color'].to_list()
						del(o['org_color'])
					
					m.show_viewport = self.physics_toggle
					m.show_render = self.physics_toggle
					
					if(m.type!='CLOTH'): continue
				
					# Applying Speed multiplier
					if(speed_mult != 0):
						m.settings.time_scale = m.settings.time_scale * speed_mult
						
					# Setting Start/End frame (with nudge)
					if(self.physics_cache_start != m.point_cache.frame_start and 
						self.physics_cache_start > self.physics_cache_end):
						self.physics_cache_end = self.physics_cache_start + 1
						
					elif(self.physics_cache_end != m.point_cache.frame_end and 
						self.physics_cache_end < self.physics_cache_start):
						self.physics_cache_start = self.physics_cache_end - 1
					
					m.point_cache.frame_start = self.physics_cache_start
					m.point_cache.frame_end = self.physics_cache_end
		
		# Toggling Physics bone constraints
		for b in rig.pose.bones:
			for c in b.constraints:
				if("phys" in c.name.lower()):
					c.mute = not self.physics_toggle

		# Toggling Physics collection(s)...
		for collection in get_children_recursive(bpy.context.scene.collection):
			if(type(collection) != bpy.types.Collection): continue
			if(rig in collection.objects[:]):
				for rig_collection in collection.children:
					if( 'phys' in rig_collection.name.lower() ):
						rig_collection.hide_viewport = not self.physics_toggle
						rig_collection.hide_render = not self.physics_toggle
						break
				break

	physics_toggle: BoolProperty(
		name='Physics',
		description='Toggle Physics systems (Enables Physics collection and Cloth, Mesh Deform, Surface Deform modifiers, etc)',
		update=update_physics)
	physics_speed_multiplier: StringProperty(
		name='Apply multiplier to physics speed',
		description = 'Apply entered multiplier to physics speed. The default physics setups are made for 60FPS. If you are animating at 30FPS, enter 2 here once. If you entered 2, you have to enter 0.5 to get back to the original physics speed',
		default="",
		update=update_physics)
	physics_cache_start: IntProperty(
		name='Physics Frame Start',
		default=1,
		update=update_physics,
		min=0, max=1048573)
	physics_cache_end: IntProperty(
		name='Physics Frame End',
		default=1,
		update=update_physics,
		min=1, max=1048574)
	
	def update_render_modifiers(self, context):
		""" Callback function for render_modifiers. Toggles SubSurf, Solidify, Bevel modifiers according to input from the UI. """
		
		for o in get_children_recursive(self.get_rig()):
			try:	# Try block is here because for some reason if an object is deleted by user, this throws an error.
				if( o.type != 'MESH' ): continue
			except:
				continue
			for m in o.modifiers:
				if(m.type in ['SOLIDIFY', 'BEVEL']):
					m.show_viewport = self.render_modifiers
				if(m.type == 'SUBSURF'):
					m.show_viewport = True
					m.levels = m.render_levels * self.render_modifiers
	
	render_modifiers: BoolProperty(
		name='render_modifiers',
		description='Enable SubSurf, Solidify, Bevel, etc. modifiers in the viewport',
		update=update_render_modifiers)
	show_all_meshes: BoolProperty(
		name='show_all_meshes',
		description='Enable all child meshes of this armature',
		update=update_meshes)
	use_proxy: BoolProperty(
		name='use_proxy',
		description='Use Proxy Meshes',
		update=update_meshes)

	def update_ik(self, context):
		""" Callback function for FK/IK settings.
			For this to work (All case-insensitive):
			Constraints must be named according to the property names they should be toggled by.
			A constraint can have more than one name, separated by a comma and a space, eg. "ik_stretch_arms, ik_arm_left". The behaviour will be like an AND statement, so the constraint is only enabled when both properties are enabled. (This is WIP, and the final form of this will probably end up being slapping expressions into constraint names...)
			Finger IK constraints must be named according to the 'finger_names' list and ending in .L/.R, eg. "Thumb_IK.L".
			Hinge IK constraints must be named according to the 'hinge_prop_names'.
		"""
		rig = self.get_rig()
		
		finger_names = ["thumb", "index", "middle", "ring", "pinky"]
		for b in rig.pose.bones:
			for c in b.constraints:
				# Handling the constraint name as an expression, where any metsrig property name can be referenced by its name.
				expression = c.name.lower()
				
				# For fingers, when per-finger IK is disabled, we want to replace them with the overall fingers_left/right variable
				if(not self.ik_per_finger):
					for fn in finger_names:
						if(fn in expression):
							if("_ik.l" in expression):
								expression = expression.replace(fn+"_ik.l", "ik_fingers_left")
							elif("_ik.r" in name):
								expression = expression.replace(fn+"_ik.R", "ik_fingers_right")
							break
				
				# Replacing variable names with their values
				metsprops = rig.data.metsrig_properties
				for k in metsprops.keys():
					expression = expression.replace(k, str(metsprops[k]))
				
				# Evaluating the expression and setting the constraint influence to the result
				try:
					result = eval(expression)
					c.influence = result
					c.mute = result <= 0
				except:
					pass	# Most constraints will fail, since most constraints don't have expressions in their names. This makes error handling, well, non-existent, which is not ideal. TODO.
				
	
	### FK/IK Properties ###

	### FK/IK Switches
	ik_spine: FloatProperty(
		name='FK/IK Spine',
		default=0,
		update=update_ik,
		min=0, max=1 )
	
	ik_leg_left: FloatProperty(
		name='FK/IK Left Leg',
		default=0,
		update=update_ik,
		min=0, max=1 )
	ik_leg_right: FloatProperty(
		name='FK/IK Right Leg',
		default=0,
		update=update_ik,
		min=0, max=1 )
	
	ik_arm_left: FloatProperty(
		name='FK/IK Left Arm',
		default=0,
		update=update_ik,
		min=0, max=1 )
	ik_arm_right: FloatProperty(
		name='FK/IK Right Arm',
		default=0,
		update=update_ik,
		min=0, max=1 )
	
	ik_fingers_right: FloatProperty(
		name='Right Fingers',
		default=0,
		update=update_ik,
		min=0, max=1 )
	ik_fingers_left: FloatProperty(
		name='Left Fingers',
		default=0,
		update=update_ik,
		min=0, max=1 )
	
	ik_per_finger: BoolProperty(
		name='Per Finger',
		description='Control Ik/FK on individual fingers',
		update=update_ik)
	
	### IK Stretch
	ik_stretch_arms: BoolProperty(
		name='Stretchy Arms',
		description='Ik Stretch Arms',
		update=update_ik)
	ik_stretch_legs: BoolProperty(
		name='Stretchy Legs',
		description='Ik Stretch Legs',
		update=update_ik)
	ik_stretch_spine: FloatProperty(
		name='Stretchy Spine',
		description='Ik Stretch Spine',
		min=0,
		max=1,
		update=update_ik)

	# IK Hinge
	ik_hinge_hand_left: BoolProperty(
		name='Left Hand Hinge',
		description='Left Hand Hinge',
		update=update_ik)
	ik_hinge_hand_right: BoolProperty(
		name='Right Hand Hinge',
		description='Right Hand Hinge',
		update=update_ik)
	
	ik_hinge_foot_left: BoolProperty(
		name='Left Foot Hinge',
		description='Left Foot Hinge',
		update=update_ik)
	ik_hinge_foot_right: BoolProperty(
		name='Right Foot Hinge',
		description='Right Foot Hinge',
		update=update_ik)
	
	# IK Auto Clavicle
	ik_auto_clav_left: BoolProperty(
		name='Left Automatic IK Clavicle',
		description='Left Automatic IK Clavicle',
		update=update_ik)
	ik_auto_clav_right: BoolProperty(
		name='Right Automatic IK Clavicle',
		description='Right Automatic IK Clavicle',
		update=update_ik)
	
	# IK Pole Follow
	ik_pole_follow_hands: FloatProperty(
		name='IK Poles Follow Hands',
		description='IK Poles Follow Hands',
		min=0,
		max=1,
		update=update_ik)
	ik_pole_follow_feet: FloatProperty(
		name='IK Poles Follow Feet',
		description='IK Poles Follow Feet',
		min=0,
		max=1,
		update=update_ik)

	# IK Parents (These values are currently just used by drivers on Child Of constraints, since update_ik() doesn't support integer checks atm.)
	ik_parents_arm_left: IntProperty(
		name='Left Arm IK Parent',
		description='Cycle between Left Arm IK Parents',
		min=0,
		max=3)
	ik_parents_arm_right: IntProperty(
		name='Right Arm IK Parent',
		description='Cycle between Right Arm IK Parents',
		min=0,
		max=3)
	ik_parents_leg_left: IntProperty(
		name='Left Leg IK Parent',
		description='Cycle between Left Leg IK Parents',
		min=0,
		max=3)
	ik_parents_leg_right: IntProperty(
		name='Right Leg IK Parent',
		description='Cycle between Right Leg IK Parents',
		min=0,
		max=3)
	
	# Head Look
	head_look: BoolProperty(
		name='Head Look',
		description='Head Look',
		update=update_ik)
	head_target_parents: IntProperty(
		name='Head Target Parent',
		description='Cycle between Head Target Parents',
		min=0,
		max=2)

class MetsRigUI(bpy.types.Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'MetsRig'
	
	@classmethod
	def poll(cls, context):
		if(context.object != None and
			context.object in get_rigs()):
				return True
		return False
	
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
		obj = context.object
		data = obj.data
		mets_props = data.metsrig_properties
		bool_props = data.metsrig_boolproperties
		multiple_chars = len(mets_props.chars(context)) > 1	# Whether the rig has multiple characters. If not, we won't display Character and OutfitSet menus.
		multiple_outfits = len(mets_props.outfits(context)) > 1
		outfit_properties_bone = obj.pose.bones.get("Properties_Outfit_"+mets_props.metsrig_outfits)
		character_properties_bone = obj.pose.bones.get("Properties_Character_"+mets_props.metsrig_chars)
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
		obj = context.object
		data = obj.data
		mets_props = data.metsrig_properties
		bool_props = data.metsrig_boolproperties
		
		character = mets_props.metsrig_chars
		multiple_chars = len(mets_props.chars(context)) > 1
		
		character_properties_bone = obj.pose.bones.get("Properties_Character_"+character)
		outfitset = mets_props.metsrig_sets
		outfit = mets_props.metsrig_outfits
		outfit_properties_bone = obj.pose.bones.get("Properties_Outfit_"+outfit)

		if(multiple_chars):
			bl_label = "Characters and Outfits"
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
							layout.prop(bp, 'value', toggle=True, text=bp.name, icon=icon)
						else:
							layout.prop(prop_owner, '["'+parent_prop_name_without_values+'"]', slider=True)
					
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
					layout.prop(prop_owner, '["'+prop_name+'"]', slider=True)
			# Bool Props
			for bp in bool_props:
				if(bp.name in prop_owner.keys() and bp.name not in props_done):
					layout.prop(bp, 'value', toggle=True, text=bp.name)
		
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
		
		data = context.object.data
		
		row_ik = layout.row()
		row_ik.column().prop(data, 'layers', index=0, toggle=True, text='Main IK Controls')
		row_ik.column().prop(data, 'layers', index=16, toggle=True, text='Secondary IK Controls')
		
		layout.row().prop(data, 'layers', index=1, toggle=True, text='FK Controls')
		layout.row().prop(data, 'layers', index=2, toggle=True, text='Stretch Controls')
		
		row_face = layout.row()
		row_face.column().prop(data, 'layers', index=3, toggle=True, text='Face Controls')
		#row_face.column().prop(data, 'layers', index=19, toggle=True, text='Face Deform')
		
		row_fingers = layout.row()
		row_fingers.column().prop(data, 'layers', index=21, toggle=True, text='Finger FK')
		row_fingers.column().prop(data, 'layers', index=22, toggle=True, text='Finger IK')
		row_fingers.column().prop(data, 'layers', index=23, toggle=True, text='Finger Stretch')
		
		layout.row().prop(data, 'layers', index=5, toggle=True, text='Hair')
		layout.row().prop(data, 'layers', index=6, toggle=True, text='Clothes')
		
		layout.separator()
		if(False):
			dev_box = layout.box()

			dev_box.row().prop(data, 'layers', index=29, toggle=True, text='IK Mechanism')
			
			row_deform = dev_box.row()
			row_deform.prop(data, 'layers', index=30, toggle=True, text='Deform Main')
			row_deform.prop(data, 'layers', index=31, toggle=True, text='Deform Adjust')

class MetsRigUI_IKFK(MetsRigUI):
	bl_idname = "OBJECT_PT_metsrig_ui_ik"
	bl_label = "FK/IK Settings"
	
	def draw(self, context):
		layout = self.layout
		column = layout.column()
		rig = context.object
		mets_props = rig.data.metsrig_properties
		
		# TODO improve the overall organization for all these buttons.
		
		### FK/IK Switch Sliders
		layout.label(text='FK/IK Switches')

		# Spine
		layout.row().prop(mets_props, 'ik_spine', slider=True, text='Spine')
		
		# Arms
		arms_row = layout.row()
		arms_row.prop(mets_props, 'ik_arm_left', slider=True, text='Left Arm')
		arms_row.prop(mets_props, 'ik_arm_right', slider=True, text='Right Arm')
		
		# Legs
		legs_row = layout.row()
		legs_row.prop(mets_props, 'ik_leg_left', slider=True, text='Left Leg')
		legs_row.prop(mets_props, 'ik_leg_right', slider=True, text='Right Leg')
		
		### Fingers
		layout.row().prop(mets_props, 'ik_per_finger', toggle=True)
		
		# Drawing individual finger controls, if that toggle is enabled.
		if(mets_props.ik_per_finger):
			finger_names = ["thumb", "index", "middle", "ring", "pinky"]
			side_names = ["_ik.l", "_ik.r"]
			for cn in finger_names:
				finger_row = layout.row()
				for sn in side_names:
					found=False
					for b in rig.pose.bones:
						for c in b.constraints:
							if(cn+sn in c.name.lower()):
								clean_name = cn+sn
								if(clean_name.endswith("_ik.l")):
									clean_name = "L " + clean_name.replace("_ik.l", "").capitalize()
								if(clean_name.endswith("_ik.r")):
									clean_name = "R " + clean_name.replace("_ik.r", "").capitalize()
								finger_row.prop(c, 'influence', slider=True, text=clean_name)
								found=True
								break
						if(found):break
		
		else:
			fingers_row = layout.row()
			fingers_row.prop(mets_props, 'ik_fingers_left', slider=True)
			fingers_row.prop(mets_props, 'ik_fingers_right', slider=True)
		
		# IK Stretch
		layout.label(text='IK Stretch')
		layout.row().prop(mets_props, 'ik_stretch_spine', slider=True, text='Stretchy Spine')
		layout.row().prop(mets_props, 'ik_stretch_arms', toggle=True, text='Stretchy Arms')
		layout.row().prop(mets_props, 'ik_stretch_legs', toggle=True, text='Stretchy Legs')

		# IK Hinge
		layout.label(text='IK Hinge')
		hand_row = layout.row()
		hand_row.column().prop(mets_props, 'ik_hinge_hand_left', toggle=True, text='Left Hand')
		hand_row.column().prop(mets_props, 'ik_hinge_hand_right', toggle=True, text='Right Hand')
		foot_row = layout.row()
		foot_row.column().prop(mets_props, 'ik_hinge_foot_left', toggle=True, text='Left Foot')
		foot_row.column().prop(mets_props, 'ik_hinge_foot_right', toggle=True, text='Right Foot')

		# FK Hinge
		left_fk_shoulder_bone = rig.data.bones.get('FK-Shoulder.L')
		left_fk_thigh_bone = rig.data.bones.get('FK-Thigh.L')
		right_fk_shoulder_bone = rig.data.bones.get('FK-Shoulder.R')
		right_fk_thigh_bone = rig.data.bones.get('FK-Thigh.R')
		if(right_fk_shoulder_bone or right_fk_thigh_bone or left_fk_shoulder_bone or left_fk_thigh_bone):
			layout.label(text='FK Hinge')
			if(left_fk_shoulder_bone or right_fk_shoulder_bone):
				arm_row = layout.row()
				if(left_fk_shoulder_bone):
					arm_row.column().prop(left_fk_shoulder_bone, 'use_inherit_rotation', toggle=True, text='Left Arm')
				if(right_fk_shoulder_bone):
					arm_row.column().prop(right_fk_shoulder_bone, 'use_inherit_rotation', toggle=True, text='Right Arm')
			if(left_fk_thigh_bone or right_fk_thigh_bone):
				leg_row = layout.row()
				if(left_fk_thigh_bone):
					leg_row.column().prop(left_fk_thigh_bone, 'use_inherit_rotation', toggle=True, text='Left Leg')
				if(right_fk_thigh_bone):
					leg_row.column().prop(right_fk_thigh_bone, 'use_inherit_rotation', toggle=True, text='Right Leg')

		# IK Auto Clavicle
		layout.label(text='IK Auto Clavicle')
		hand_row = layout.row()
		hand_row.column().prop(mets_props, 'ik_auto_clav_left', toggle=True, text='Left Clavicle')
		hand_row.column().prop(mets_props, 'ik_auto_clav_right', toggle=True, text='Right Clavicle')

		# IK Parents
		layout.label(text='IK Parents')
		arm_parent_row = layout.row()
		arm_parents = ['Root', 'Pelvis', 'Chest', 'Arm']
		arm_parent_row.column().prop(mets_props, 'ik_parents_arm_left', slider=True, text='Left Hand ['+arm_parents[mets_props.ik_parents_arm_left] + "]")
		arm_parent_row.column().prop(mets_props, 'ik_parents_arm_right', slider=True, text='Right Hand ['+arm_parents[mets_props.ik_parents_arm_right] + "]")
		leg_parent_row = layout.row()
		leg_parents = ['Root', 'Pelvis', 'Hips', 'Leg']
		leg_parent_row.column().prop(mets_props, 'ik_parents_leg_left', slider=True, text='Left Foot ['+leg_parents[mets_props.ik_parents_leg_left] + "]")
		leg_parent_row.column().prop(mets_props, 'ik_parents_leg_right', slider=True, text='Right Foot ['+leg_parents[mets_props.ik_parents_leg_right] + "]")

		# IK Pole Follow
		layout.label(text='IK Pole Follow')
		pole_row = layout.row()
		pole_row.column().prop(mets_props, 'ik_pole_follow_hands', slider=True, text='Arms')
		pole_row.column().prop(mets_props, 'ik_pole_follow_feet', slider=True, text='Legs')

		# Head & Neck Settings
		layout.label(text='Head Settings')
		head_bone = rig.data.bones.get("AIM-Head")
		neck_bone = rig.data.bones.get("DEF-Neck")
		head_pose_bone = rig.pose.bones.get("AIM-Head")
		aim_constraint = head_pose_bone.constraints.get('head_look')
		if(neck_bone):
			layout.row().prop(neck_bone, 'use_inherit_rotation', toggle=True, text='Neck Hinge')
		if(head_bone):
			layout.row().prop(head_bone, 'use_inherit_rotation', toggle=True, text='Head Hinge')
			if(aim_constraint):
				layout.row().prop(mets_props, 'head_look', toggle=True, text='Head Look')
		head_parents = ['Root', 'Pelvis', 'Chest', 'Neck', 'Head']
		layout.row().prop(mets_props, 'head_target_parents', slider=True, text='Head Target Parent ['+head_parents[mets_props.head_target_parents] + "]")

class MetsRigUI_Extras(MetsRigUI):
	bl_idname = "OBJECT_PT_metsrig_ui_extras"
	bl_label = "Extras"
	
	def draw(self, context):
		layout = self.layout
		data = context.object.data
		mets_props = data.metsrig_properties
		bool_props = data.metsrig_boolproperties
		
		#layout.row().prop(mets_props, 'metsrig_hairs')
		#layout.separator()
		
		show_all_meshes = mets_props.show_all_meshes
		layout.row().prop(mets_props, 'show_all_meshes', text='Enable All Meshes', toggle=True)
		render_modifiers = mets_props.render_modifiers
		layout.row().prop(mets_props, 'render_modifiers', text='Enable Modifiers', toggle=True)
		use_proxy = mets_props.use_proxy
		layout.row().prop(mets_props, 'use_proxy', text='Use Proxies', toggle=True)

class MetsRigUI_Extras_Materials(MetsRigUI):
	bl_idname = "OBJECT_PT_metsrig_ui_extras_materials"
	bl_label = "Materials"
	bl_parent_id = "OBJECT_PT_metsrig_ui_extras"
	
	@classmethod
	def poll(cls, context):
		if(not super().poll(context)):
			return False
		rig = context.object
		if('material_controller' not in rig.data):
			return False
		mat_ctr_name = rig.data['material_controller']
		return bpy.data.node_groups.get(str(mat_ctr_name)) != None
		
	def draw(self, context):
		layout = self.layout
		data = context.object.data
		
		if('material_controller' in data):
			material_controller = bpy.data.node_groups.get(data['material_controller'])
			if(material_controller):
				output_node = material_controller.nodes.get('Group Output')
				for i in output_node.inputs:
					input = material_controller.inputs.get(i.name)
					if(input==None): continue
					value_socket = i.links[0].from_socket
					
					name = i.name.replace("_", " ").title()
					layout.prop(input, 'default_value', text=name, slider=True)

class MetsRigUI_Extras_Physics(MetsRigUI):
	bl_idname = "OBJECT_PT_metsrig_ui_extras_physics"
	bl_label = "Physics"
	bl_parent_id = "OBJECT_PT_metsrig_ui_extras"
	
	def draw_header(self, context):
		data = context.object.data
		mets_props = data.metsrig_properties
		layout = self.layout
		layout.prop(mets_props, "physics_toggle", text="")
	
	def draw(self, context):
		data = context.object.data
		mets_props = data.metsrig_properties
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
	"""Open links in a web browser."""
	bl_idname = "ops.open_link"
	bl_label = "Open Link in web browser"
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
		
		layout.operator('ops.open_link', text="Blender Cloud").url = self.url_cloud
		layout.operator('ops.open_link', text="Blender Dev Fund").url = self.url_dev_fund
		layout.operator('ops.open_link', text="Blender Dev Blog").url = self.url_dev_blog
		layout.operator('ops.open_link', text="Blender Chat").url = self.url_blender_chat
	
classes = (
	MetsRigUI_Properties, 
	MetsRigUI_Layers, 
	MetsRigUI_IKFK, 
	MetsRigUI_Extras, 
	MetsRigUI_Extras_Materials, 
	MetsRigUI_Extras_Physics, 
	Link_Button, 
	MetsRigUI_Links, 
	MetsRig_Properties, 
	MetsRig_BoolProperties
)

from bpy.utils import register_class
for c in classes:
	register_class(c)

bpy.types.Armature.metsrig_properties = bpy.props.PointerProperty(type=MetsRig_Properties)
bpy.types.Armature.metsrig_boolproperties = bpy.props.CollectionProperty(type=MetsRig_BoolProperties)

bpy.app.handlers.depsgraph_update_post.append(MetsRig_Properties.post_depsgraph_update)
bpy.app.handlers.depsgraph_update_pre.append(MetsRig_Properties.pre_depsgraph_update)