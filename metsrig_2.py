# This is a verison of metsrig.py that is meant to be used in conjunction with cloudrig.py.

# This will have all the features that are related to my NSFW rigs. 
# This way I can easily keep unnecessary features out of my professional work with CloudRig.

import bpy

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
			print("Update rig")
			cloud_props = rig.cloud_rig
			char_bone = get_char_bone(rig)
			outfit_bone = rig.pose.bones.get("Properties_Outfit_"+cloud_props.outfit)

			update_node_values(rig, char_bone, outfit_bone)
			rig['update'] = 0

def optimize_selector_group(nodes, group_node, active_texture=False):
	""" For finding a node value connected even through reroute nodes, then muting unused texture nodes, and optionally changing the active node to this group_node's active texture. """
	print("Optimize group node:")
	print(group_node.name)
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
		if(len(group_node.inputs[i].links) > 0 ):
			node = group_node.inputs[i].links[0].from_node
			if(node.type=='TEX_IMAGE'):
				node.mute = i!=selector_value
	
	nodes.active.mute=False

def update_node_values(rig, char_bone, outfit_bone):
	""" In all materials belonging to this rig, update nodes that correspond to an outfit, character, rig data, or metsrig property.
		eg. when Ciri's "Face" property changes, ensure that the "Face" value node in her material updates.
		Also update the active texture of materials for better feedback while in Solid View.
	"""
	print("Update node values")
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

	print("objs:")
	print(objs)

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
				print("Save node tree:")
				print(ms.material.name)
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

def register():
	bpy.app.handlers.depsgraph_update_post.append(post_depsgraph_update)
	bpy.app.handlers.depsgraph_update_pre.append(pre_depsgraph_update)

def unregister():
	bpy.app.handlers.depsgraph_update_post.remove(post_depsgraph_update)
	bpy.app.handlers.depsgraph_update_pre.remove(pre_depsgraph_update)

register()