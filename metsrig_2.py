# This is a verison of metsrig.py that is meant to be used in conjunction with cloudrig.py.

# This will have all the features that are related to my NSFW rigs. 
# This way I can easily keep unnecessary features out of my professional work with CloudRig.

import bpy
from bpy.props import *

def get_children_recursive(obj, ret=[]):
	# Return all the children and children of children of obj in a flat list.
	for c in obj.children:
		if(c not in ret):
			ret.append(c)
		ret = get_children_recursive(c, ret)
	
	return ret

def get_rigs():
	""" Find all CloudRigs in the current view layer. """
	ret = []
	armatures = [o for o in bpy.context.view_layer.objects if o.type=='ARMATURE']
	for o in armatures:
		if("cloudrig") in o.data:
			ret.append(o)
	return ret

def get_char_bone(rig):
	for b in rig.pose.bones:
		if b.name.startswith("Properties_Character"):
			return b

def pre_depsgraph_update(scene, depsgraph=None):
	""" Runs before every depsgraph update. Is used to handle user input by detecting changes in the rig properties. """
	for rig in get_rigs():
		cloud_props = rig.cloud_rig
		char_bone = get_char_bone(rig)
		outfit_bone = rig.pose.bones.get("Properties_Outfit_"+cloud_props.outfit)
		
		if 'update' not in rig:
			rig['update'] = 0
		if 'prev_props' not in rig:
			rig['prev_props'] = ""
		
		# Saving those properties into a list of dictionaries. 
		current_props = [{}, {}, {}]
		
		saved_types = [int, float]	# Types of properties that we save for user input checks.
		def save_props(prop_owner, list_id):
			for p in prop_owner.keys():
				if(p=='_RNA_UI' or p=='prev_props'): continue	# TODO this check would be redundant if we didn't save strings, and the 2nd part is already redundant due to next line.
				if(type(prop_owner[p]) not in saved_types): continue
				if(p=="prop_hierarchy"): continue
				current_props[list_id][p] = prop_owner[p]
		
		if char_bone:
			save_props(char_bone, 0)
		if outfit_bone:
			save_props(outfit_bone, 1)
		save_props(rig, 2)
		
		# Retrieving the list of dictionaries from prev_props.
		prev_props = []
		if rig['prev_props'] != "":
			prev_props = [
				rig['prev_props'][0].to_dict(),
				rig['prev_props'][1].to_dict(),
				rig['prev_props'][2].to_dict(),
			]
		
		# Compare the current and previous properties.
		# If they do not match, that means there was user input, and it's time to update stuff.
		if current_props != prev_props:
			rig['prev_props'] = [current_props[0], current_props[1], current_props[2]]
			# However, updating meshes before depsgraph update will cause an infinite loop, so we use a flag to let post_depsgraph_update know that it should update meshes.
			rig['update'] = 1

def post_depsgraph_update(scene, depsgraph=None):
	"""Runs after every depsgraph update. If any user input to the rig properties was detected by pre_depsgraph_update(), this will call update_meshes(). """
	for rig in get_rigs():
		if rig['update'] == 1:
			cloud_props = rig.cloud_rig
			char_bone = get_char_bone(rig)
			outfit_bone = rig.pose.bones.get("Properties_Outfit_"+cloud_props.outfit)

			update_node_values(rig, char_bone, outfit_bone)
			rig.metsrig.update_meshes()
			rig['update'] = 0

def nodes_exclusive_to_socket(input_socket, disabled_sockets=[]):
	""" Return a list of nodes that connect into the given socket, and nothing else.
	It is allowed to connect to sockets that are passed in as disabled, which just means to-be-ignored. """

	if len(input_socket.links) != 1:
		return []

	nodes = []

	from_node = input_socket.links[0].from_node
	nodes.append(from_node)
	
	for outp in from_node.outputs:
		for link in outp.links:
			if link.to_socket not in disabled_sockets:
				# Node output connects to something that isn't disabled, so we stop recursion and return with an empty list.
				return []

	# Otherwise add the connected node to the list, and repeat for all of its inputs.
	disabled_sockets.extend(link.from_node.inputs)
	for inp in link.from_node.inputs:
		nodes.extend(nodes_exclusive_to_socket(inp, disabled_sockets))
	
	return nodes

def nodes_connected_to_socket(input_socket):
	""" Return a list of all nodes connected to an input socket. """
	nodes = []
	if len(input_socket.links) != 1:
		return []

	from_node = input_socket.links[0].from_node
	nodes.append(from_node)
	if 'SELECTOR_GROUP' in from_node.name: return nodes
	for inp in from_node.inputs:
		nodes.extend(nodes_connected_to_socket(inp))

	return nodes

def optimize_selector_group(nodes, group_node, active_texture=False):
	""" For finding a node value connected even through reroute nodes, then muting unused texture nodes, and optionally changing the active node to this group_node's active texture. """
	node = group_node
	socket = None
	# Find next connected non-reroute node.
	while len(node.inputs[0].links) > 0:
		next_node = node.inputs[0].links[0].from_node

		if(next_node.type == 'REROUTE'):
			node = next_node
			continue
		elif(next_node.type == 'VALUE'):
			node = next_node
			socket = node.outputs[0]
			break
		else:
			break

	selector_value = 1
	if socket:
		selector_value = int(socket.default_value)
		node.label = node.label[:-3] + " " + str(selector_value).zfill(2)
	else:
		print("Warning: Selector value not found - Node probably not connected properly?")
		group_node.label = 'Unconnected Selector'
	if group_node.mute:
		selector_value = 0

	# Setting active node for the sake of visual feedback when in Solid view.
	if len(group_node.inputs[selector_value].links) > 0  and active_texture:
		nodes.active = group_node.inputs[selector_value].links[0].from_node
		nodes.active.mute=False
	# elif(len(group_node.inputs[1].links) > 0 ):
	# 	if active_texture:
	# 		nodes.active = group_node.inputs[1].links[0].from_node
	# 		nodes.active.mute=False
	# 	selector_value = 1

	# Mute all connected nodes that don't connect to anything else.
	disabled_sockets = [s for i, s in enumerate(group_node.inputs) if i!=selector_value]
	active_socket = group_node.inputs[selector_value]
	for i in range(1, len(group_node.inputs)):
		socket = group_node.inputs[i]
		if socket==active_socket: continue
		
		for n in nodes_exclusive_to_socket(socket, disabled_sockets):
			if n.type=='VALUE': continue
			n.mute = True

	# Un-mute nodes that contribute to the active socket.
	for n in nodes_connected_to_socket(active_socket):
		n.mute = False
	
def update_node_values(rig, char_bone, outfit_bone):
	""" In all materials belonging to this rig, update nodes that correspond to an outfit, character, rig data, or metsrig property.
		eg. when Ciri's "Face" property changes, ensure that the "Face" value node in her material updates.
		Also update the active texture of materials for better feedback while in Solid View.
	"""
	# Gathering all the keys and values from outfit and character.
	big_dict = {}
	for e in [outfit_bone, char_bone]:
		if( e==None ): continue
		for k in e.keys():
			if(k=='_RNA_UI'): continue
			value = e[k]
			if( type(value) in [int, float, str] ):
				big_dict[k] = value
			elif('IDPropertyArray' in str(type(value))):
				big_dict[k] = value.to_list()

	# Get a list of every object that's parented to the rig.
	objs = list(filter(lambda o: type(o) == bpy.types.Object, get_children_recursive(rig)))

	# Get a list of node trees that the visible objects use.
	node_trees = []
	for o in objs:
		try:	# Apparently objs list can contain objects that have been deleted by the user, in which case it throws an error.
			if not o.visible_get(): continue
		except:
			continue
		for ms in o.material_slots:
			if not ms.material: continue
			if ms.material.node_tree not in node_trees:
				node_trees.append(ms.material.node_tree)

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
			optimize_selector_group(nodes, active_color_group, True)

		for n in nodes:
			if("SELECTOR_GROUP" in n.name):
				optimize_selector_group(nodes, n)




class MetsRig_Properties(bpy.types.PropertyGroup):
	def determine_visibility_by_expression(self, o, prop_owners):
		""" Determine whether an object should be visible based on its Expression custom property.
			Expressions will recognize any character or outfit property names as variables.
			'Outfit' keyword can also be used to compare with the currently selected outfit.
			Example expression: "Outfit=='Ciri_Default' and Hood==1"
		"""
		rig = self.id_data

		# Support "Outfit" keyword to refer to the cloudrig outfit
		expression = o['Expression']
		expression = expression.replace('Outfit', "'" + rig.cloud_rig.outfit + "'")

		# Replacing the variable names in the expression with the corresponding variables' values.
		found_anything=False
		for prop_owner in prop_owners:
			for prop_name in prop_owner.keys():
				if prop_name in expression:
					found_anything = True
					expression = expression.replace(prop_name, str(prop_owner[prop_name]))
		
		#if(not found_anything):
		#	return False
		
		try:
			ret = eval(expression)
			return ret
		except NameError:	# When the variable name in an expression doesn't get replaced by its value because the object doesn't belong to the active outfit.
			return False

	def determine_visibility_by_properties(self, o, prop_owners):
		""" Determine whether an object should be visible by matching its custom properties to the active character and outfit properties. """
		rig = self.id_data

		print(o.name)
		for prop_owner in prop_owners:
			for prop_name in o.keys():
				if( (prop_name == '_RNA_UI') or (prop_name not in prop_owner) ): continue
				
				prop_value = prop_owner[prop_name]	# Value of the property on the property owner (bone). Changed by the user via the UI.
				requirement = o[prop_name]			# Value of the property on the object. (Not to be changed by the user) This defines what the property's value must be in order for this object to be visible.
				
				# Checking if the property value fits the requirement...
				if type(requirement) == int:
					if prop_value != requirement:
						print(f"{prop_value} not equal to {requirement}, returning False")
						return False
				elif 'IDPropertyArray' in str(type(requirement)):
					if prop_value not in requirement.to_list():
						print(f"{prop_value} not in {requirement.to_list()}, returning False.")
						return False

				# TODO: wtf is this next bit?
				elif type(requirement) == str:
					if '#' not in requirement: continue
					if not eval(requirement.replace("#", str(prop_value))):
						return False
				else:
					print("Error: Unsupported property type: " + str(type(requirement)) + " of property: " + p + " on object: " + o.name)
		
		# If we got this far without returning False, then all the properties matched and this object should be visible.
		print("Returning True")
		return True
		
	def determine_object_visibility(self, o):
		""" Determine if an object should be visible based on its properties and the rig's current state. """
		rig = self.id_data
		char_bone = get_char_bone(rig)
		outfit_bone = rig.pose.bones.get('Properties_Outfit_' + rig.cloud_rig.outfit)
		prop_owners = [char_bone, outfit_bone]

		if('Expression' in o):
			return self.determine_visibility_by_expression(o, prop_owners)
		else:
			return self.determine_visibility_by_properties(o, prop_owners)
		
	def determine_visibility_by_name(self, m, obj=None):
		""" Determine whether the passed vertex group or shape key should be enabled, based on its name and the properties of the currently active outfit.
			Naming convention example: M:Ciri_Default:Corset==1*Top==1
			Split in 3 parts by :(colon) characters.
			The first part must be "M" to indicate that this shape key/vgroup is used by the outfit swapping system.
			The second part is the outfit name.
			The third part is an expression, which recognizes variable names that are custom properties on the given outfit, or the character.

			param m: The vertex group or shape key (or anything with a "name" property).
		"""
		
		if("M:" not in m.name):
			return None
		
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
		#TODO: This of course doesn't work with linking. Hopefully one day with overrides?

		if obj.type!='MESH': return
		
		mask_vertex_groups = [vg for vg in obj.vertex_groups if self.determine_visibility_by_name(vg, obj)]
		final_mask_vg = obj.vertex_groups.get('Mask')
		if final_mask_vg:
			for v in obj.data.vertices:
				final_mask_vg.add([v.index], 0, 'REPLACE')
				for mvg in mask_vertex_groups:
					try:
						if mvg.weight(v.index) > 0:
							final_mask_vg.add([v.index], 1, 'REPLACE')
							break
					except:
						pass
		
		# Toggling shape keys using the same naming convention as the VertexWeightMix modifiers.
		if obj.data.shape_keys:
			#shapekeys = [sk for sk in obj.data.shape_keys.key_blocks if "M-" in sk.name]
			shapekeys = obj.data.shape_keys.key_blocks
			for sk in shapekeys:
				visible = self.determine_visibility_by_name(sk, obj)
				if visible != None:
					sk.value = visible

	def update_meshes(self, dummy=None):
		""" Executes the cloth swapping system by updating object visibilities, mask vertex groups and shape key values. """

		def do_child(rig, obj, hide=None):
			# Recursive function to control item visibilities.
			# We use the object hierarchy and assume that if an object is disabled, all its children should be disabled.
			visible = None
			if hide!=None:
				visible = not hide
			else:
				visible = self.determine_object_visibility(obj)

			if visible != None:
				obj.hide_viewport = not visible
				obj.hide_render = not visible

			if obj.hide_viewport == False:
				self.activate_vertex_groups_and_shape_keys(obj)
			else:
				hide = True

			# Recursion
			for child in obj.children:
				do_child(rig, child, hide)

		hide = False if self.show_all_meshes else None

		rig = self.id_data
		# Recursively determining object visibilities
		for child in rig.children:
			do_child(rig, child, hide)

	show_all_meshes: BoolProperty(
		name='show_all_meshes'
		,description='Enable all child meshes of this armature'
		,options={'LIBRARY_EDITABLE'}
		,update=update_meshes
	)

classes = [
	MetsRig_Properties,
]

def register():
	from bpy.utils import register_class
	for c in classes:
		register_class(c)

	# TODO: Might want to rename where this is stored, so it doesn't clash with my older rigs... awkward though.
	bpy.types.Object.metsrig = bpy.props.PointerProperty(type=MetsRig_Properties)

	bpy.app.handlers.depsgraph_update_post.append(post_depsgraph_update)
	bpy.app.handlers.depsgraph_update_pre.append(pre_depsgraph_update)

	bpy.app.handlers.frame_change_pre.append(pre_depsgraph_update)
	bpy.app.handlers.frame_change_post.append(post_depsgraph_update)

def unregister():
	from bpy.utils import unregister_class
	for c in reversed(classes):
		unregister_class(c)

	bpy.app.handlers.frame_change_pre.remove(pre_depsgraph_update)
	bpy.app.handlers.frame_change_post.remove(post_depsgraph_update)

	bpy.app.handlers.depsgraph_update_post.remove(post_depsgraph_update)
	bpy.app.handlers.depsgraph_update_pre.remove(pre_depsgraph_update)

register()