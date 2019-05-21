import bmesh
import bpy
from bpy.props import *
from . import utils

# TODO testing:
# Mirror modifier vertex groups getting spared when they should
# Oh, and also everything else.

class DeleteUnusedMaterialSlots(bpy.types.Operator):
	""" Delete material slots on selected objects that have no faces assigned. """
	bl_idname = "object.delete_unused_material_slots"
	bl_label = "Delete Unused Material Slots"
	bl_options = {'REGISTER', 'UNDO'}

	# TODO: Add this to the UI, to the material arrow panel, with opt_active_only=True.

	opt_objects: EnumProperty(name="Objects",
		items=[	('Active', 'Active', 'Active'),
				('Selected', 'Selected', 'Selected'),
				('All', 'All', 'All')
				],
		description="Which objects to operate on")

	def execute(self, context):
		objs = context.selected_objects
		if(self.opt_objects=='Active'):
			objs = [context.object]
		elif(self.opt_objects=='All'):
			objs = bpy.data.objects

		for o in objs:
			used_mats = []
			if( type(o)!='MESH' or len(o.data.polygons) == 0 ): continue

			for f in o.data.polygons:
				if(f.material_index not in used_mats):
					used_mats.append(f.material_index)
			
			# To remove the material slots, we iterate in reverse.
			for i in range(len(o.material_slots)-1, -1, -1):
				if(i not in used_mats):
					o.active_material_index = i
					print("Removed material slot " + str(i))
					bpy.ops.object.material_slot_remove()
		
		return {'FINISHED'}

class DeleteUnusedVGroups(bpy.types.Operator):
	""" Delete vertex groups that have no weights and/or aren't being used by any modifiers and/or don't correlate to any bones. """
	bl_idname = "object.delete_unused_vgroups"
	bl_label = "Delete Unused Vertex Groups"
	bl_options = {'REGISTER', 'UNDO'}
	
	# TODO: Add this to the UI, to the vertex group dropdown panel, with active_only=True

	opt_objects: EnumProperty(name="Objects",
		items=[	('Active', 'Active', 'Active'),
				('Selected', 'Selected', 'Selected'),
				('All', 'All', 'All')
				],
		description="Which objects to operate on")

	opt_clearZeroVGroups: BoolProperty(name="Clear Empty Vertex Groups", 
		default=True, 
		description="Clear all vertex groups that have no weights at all. Shouldn't break mirror modifier as long as names end in 'R' and 'L'")
		
	opt_clearUnusedVGroups: BoolProperty(name="Clear Unused Vertex Groups", 
		default=True, 
		description="Clear all vertex groups that aren't used by any modifiers and don't have any equivalent Bones in any of the object's armatures")

	def execute(self, context):
		objs = context.selected_objects
		if(self.opt_objects=='Active'):
			objs = [context.object]
		elif(self.opt_objects=='All'):
			objs = bpy.data.objects

		for obj in objs:
			if(len(obj.vertex_groups) == 0): continue
			
			# Clean 0 weights
			bpy.ops.object.vertex_group_clean(group_select_mode='ALL', limit=0)

			# TODO: Should also consider vertex groups used by any kinds of constraints. 
			# Oof. We'd have to look through the objects and bones of the entire scene for that. Maybe worth?

			# Saving vertex groups that are used by modifiers and therefore should not be removed
			safe_groups = []
			def save_groups_by_attributes(owner):
				# Look through an object's attributes. If its value is a string, try to find a vertex group with the same name. If found, make sure we don't delete it.
				for attr in dir(owner):
					value = getattr(owner, attr)
					if(type(value)==str):
						vg = obj.vertex_groups.get(value)
						if(vg):
							safe_groups.append(vg)

			# Save any vertex groups used by modifier parameters.
			for m in obj.modifiers:
				save_groups_by_attributes(m)
				if(hasattr(m, 'settings')):	#Physics modifiers
					save_groups_by_attributes(m.settings)

			# Getting a list of bone names from all armature modifiers.
			bone_names = None
			for m in obj.modifiers:
				if(m.type == 'ARMATURE'):
					armature = m.object
					if armature is None:
						continue
					if(bone_names is None):
						bone_names = list(map(lambda x: x.name, armature.pose.bones))
					else:
						bone_names.extend(list(map(lambda x: x.name, armature.pose.bones)))
			
			# Clearing vertex groups that don't have a corresponding bone in any of the armatures.
			for vg in reversed(obj.vertex_groups):					# For each vertex group
				if(self.opt_clearUnusedVGroups):
					if( vg not in safe_groups ):
						if( bone_names ):
							if (vg.name not in bone_names):
								print("Unused vgroup deleted (case 1): "+vg.name)
								obj.vertex_groups.remove(vg)
						else:	# If there is no armature
							print("Unused vgroup deleted (case 2): "+vg.name)
							obj.vertex_groups.remove(vg)
						continue
				
				# Saving vertex groups that have any weights assigned to them, also considering mirror modifiers
				for i in range(0, len(obj.data.vertices)):	# For each vertex
					try:
						vg.weight(i)							# If there's a weight assigned to this vert (else exception)
						if(vg not in safe_groups):
							safe_groups.append(vg)
							
							opp_name = utils.flip_name(vg.name)
							opp_group = obj.vertex_groups.get(opp_name)
							if(opp_group):
								safe_groups.append(opp_group)
							break
					except RuntimeError:
						continue
			
			# Clearing vertex groups that have no weights at all
			if(self.opt_clearZeroVGroups):
				for vg in obj.vertex_groups:
					if(vg not in safe_groups):
						print("Empty vgroup removed: "+vg.name)
						obj.vertex_groups.remove(vg)
		
		return {'FINISHED'}

def get_linked_nodes(nodes, node):	# Recursive function to collect all nodes connected BEFORE the second parameter.
	nodes.append(node)
	for i in node.inputs:
		if(len(i.links) > 0):
			get_linked_nodes(nodes, i.links[0].from_node)
	return nodes

def clean_node_tree(node_tree, delete_unused_nodes=True, fix_groups=False, center_nodes=True, fix_tex_refs=False, rename_tex_nodes=True, hide_sockets=False, min_sockets=2, tex_width=300):	# nodes = nodeTree.nodes
	nodes = node_tree.nodes
	if(len(nodes)==0): return

	if(delete_unused_nodes):
		# Deleting unconnected nodes
		output_nodes = list(filter(lambda x: x.type in ['OUTPUT_MATERIAL', 'OUTPUT_WORLD', 'COMPOSITE', 'VIEWER'], nodes))
		used_nodes = []
		for on in output_nodes:
			used_nodes.extend(get_linked_nodes([], on))

		for n in nodes:
			if(n not in used_nodes and n.type != 'FRAME'):
				print("Removing unconnected node: Type: " + n.type + " Name: " + n.name + " Label: " + n.label)
				nodes.remove(n)
				continue

	# Finding bounding box of all nodes
	x_min = min(n.location.x for n in nodes if n.type!= 'FRAME')
	x_max = max(n.location.x for n in nodes if n.type!= 'FRAME')
	y_min = min(n.location.y for n in nodes if n.type!= 'FRAME')
	y_max = max(n.location.y for n in nodes if n.type!= 'FRAME')
	
	# Finding bounding box center
	x_mid = (x_min+x_max)/2
	y_mid = (y_min+y_max)/2

	for n in nodes:
		if(fix_tex_refs):
			# Changing .xxx texture references
			if(n.type == 'TEX_IMAGE'):
				if(n.image is not None and n.image.name[-4] == '.'):
					existing = bpy.data.images.get(n.image.name[:-4])
					if(existing):
						print("Changed a texture reference to: "+n.image.name)
						n.image = bpy.data.images.get(n.image.name[:-4])
					else:
						n.image.name = n.image.name[:-4]
		
		if(n.type=='TEX_IMAGE'):
			# Resizing image texture nodes
			if(tex_width!=-1):
				n.width=tex_width
				n.width_hidden=tex_width
			
			if(rename_tex_nodes):
				# Renaming and relabelling image texture nodes
				if(n.image is not None):
					extension = "." + n.image.filepath.split(".")[-1]
					n.name = n.image.name.replace(extension, "")
					n.label = n.name
					if(n.label[-4] == '.'):
						n.label = n.label[:-4]
		
		if(hide_sockets):
			# Hiding unplugged sockets, if there are more than min_sockets.
			unplugged = []
			for i in n.inputs:
				if(len(i.links) == 0):
					unplugged.append(i)
			if(len(unplugged) > min_sockets):
				for u in unplugged:
					u.hide = True
			
			for i in n.outputs:
				if(len(i.links) == 0):
					unplugged.append(i)
			if(len(unplugged) > min_sockets):
				for u in unplugged:
					u.hide = True
		
		if(center_nodes):
			# Moving all nodes by the amount of the bounding box center(therefore making the center 0,0) - except Frame nodes, which move by themselves.
			if(n.type != 'FRAME'):
				n.location.x -= x_mid
				n.location.y -= y_mid

		if(fix_groups):
			# Changing references to nodegroups ending in .00x to their original. If the original doesn't exist, rename the nodegroup.
			for n in nodes:
				if(n.type=='GROUP'):
					if('.00' in n.node_tree.name):
						existing = bpy.data.node_groups.get(n.node_tree.name[:-4])
						if(existing):
							n.node_tree = existing
						else:
							n.node_tree.name = n.node_tree.name[:-4]

class CleanUpMeshes(bpy.types.Operator):
	pass
	# TODO: Overwatch mesh cleanup code(quadrify, remove doubles, etc)

class CleanUpArmatures(bpy.types.Operator):
	pass
	# TODO: add consistent bone envelope and bbone scales.
	# TODO: disable Deform tickbox on bones with no corresponding vgroups. (This would ideally be done before vgroup cleanup) - Always print a warning for this.
	# TODO: vice versa, warn is a non-deform bone has a corresponding vgroup.

class CleanUpMaterials(bpy.types.Operator):
	bl_idname = "material.clean_up"
	bl_label = "Clean Up Material"
	bl_options = {'REGISTER', 'UNDO'}
	
	opt_objects: EnumProperty(name="Objects",
		items=[	('Active', 'Active', 'Active'),
				('Selected', 'Selected', 'Selected'),
				('All', 'All', 'All')
				],
		description="Which objects to operate on")

	opt_fix_name: BoolProperty(name="Fix .00x Material Names", 
		default=False, 
		description="Materials ending in .001 or similar will be attempted to be renamed")
		
	opt_delete_unused_nodes: BoolProperty(name="Clear Unused Nodes", 
		default=False, 
		description="Clear all nodes (except Frames) in all materials that aren't linked to the 'Material Output' node")
		
	opt_hide_sockets: BoolProperty(name="Hide Node Sockets", 
		default=False, 
		description="Hide all unplugged sockets on either side of group nodes if they have more than 2 unplugged sockets on either side")
	
	opt_fix_groups: BoolProperty(name="Fix .00x Group Nodes",
		default=True,
		description="If a group node's nodegroup ends in .00x but a nodegroup exists without it, replace the reference. If such nodegroup doesn't exist, rename it")

	opt_fix_tex_refs: BoolProperty(name="Fix .00x Texture References",
		default=True,
		description="If a texture node references a texture ending in .00x but a texture without it exists, change the reference. If such texture doesn't exist, rename it")

	opt_rename_nodes: BoolProperty(name="Rename Texture Nodes",
		default=False,
		description="Rename and relabel texture nodes to the filename of their image, without extension")

	opt_set_tex_widths: IntProperty(name="Set Texture Node Widths",
		default=400,
		description="Set all Texture Node widths to this value")

	# TODO: Can be added to the UI the same place as delete unused material slots.

	def execute(self, context):
		mats_done = []
		
		objs = context.selected_objects
		if(self.opt_objects=='Active'):
			objs = [context.object]
		elif(self.opt_objects=='All'):
			objs = bpy.data.objects
		
		for o in objs:
			for ms in o.material_slots:
				m = ms.material
				if(m==None or m in mats_done): continue
				if(self.opt_fix_name):
					# Clearing .00x from end of names
					if(('.' in m.name) and (m.name[-4] == '.')):
						existing = bpy.data.materials.get(m.name[:-4])
						if(not existing):
							m.name = m.name[:-4]
							print("...Renamed to " + m.name)
				# Cleaning nodetree
				if(m.use_nodes):
					clean_node_tree(m.node_tree, 
					delete_unused_nodes=self.opt_delete_unused_nodes, 
					fix_groups=self.opt_fix_groups, 
					center_nodes=True, 
					fix_tex_refs=self.opt_fix_tex_refs, 
					rename_tex_nodes=self.opt_rename_nodes, 
					hide_sockets=self.opt_hide_sockets, 
					min_sockets=2, 
					tex_width=self.opt_set_tex_widths)
				mats_done.append(m)
		return {'FINISHED'}

class CleanUpObjects(bpy.types.Operator):
	bl_idname = "object.clean_up"
	bl_label = "Clean Up Selected Objects"
	bl_options = {'REGISTER', 'UNDO'}
	
	opt_objects: EnumProperty(name="Objects",
		items=[	('Active', 'Active', 'Active'),
				('Selected', 'Selected', 'Selected'),
				('All', 'All', 'All')
				],
		description="Which objects to operate on")

	opt_rename_data: BoolProperty(
		name="Rename Datas", 
		default=True, 
		description="If an object or armature is named 'Apple', its data will be renamed to 'Data_Apple'")
	
	opt_rename_uvs: BoolProperty(
		name="Rename UV Maps", 
		default=True, 
		description="If an object has only one UVMap, rename that to the default: 'UVMap'")

	opt_clean_material_slots: BoolProperty(
		name="Clean Material Slots",
		default=True,
		description="Delete material slots on selected objects that have no faces assigned")

	opt_rename_materials: BoolProperty(
		name="Fix .00x Material Names", 
		default=False, 
		description="Materials ending in .001 or similar will be attempted to be renamed")

	opt_clean_materials: BoolProperty(
		name="Clean Material Nodes",
		default=True,
		description="Remove unused nodes, resize and rename image nodes, hide unused group node sockets, and center nodes")

	opt_clearZeroVGroups: BoolProperty(name="Clear Empty Vertex Groups", 
		default=True, 
		description="Clear all vertex groups that have no weights at all. Shouldn't break mirror modifier as long as names end in 'R' and 'L'")
		
	opt_clearUnusedVGroups: BoolProperty(name="Clear Unused Vertex Groups", 
		default=True, 
		description="Clear all vertex groups that aren't used by any modifiers and don't have any equivalent Bones in any of the object's armatures")

	# TODO: implement this
	opt_create_mirror_vgroups: BoolProperty(
		name="Create Mirror Vertex Groups",
		default=True,
		description="If there is a Mirror modifier, create any missing left/right sided vertex groups")

	def execute(self, context):
		org_active = context.object

		objs = context.selected_objects
		if(self.opt_objects=='Active'):
			objs = [context.object]
		elif(self.opt_objects=='All'):
			objs = bpy.data.objects
		
		for obj in objs:
			if(obj.type == 'MESH' or obj.type == 'ARMATURE'):
				print("...Working on object: "+obj.name)
				bpy.ops.object.mode_set(mode="OBJECT")
				bpy.context.view_layer.objects.active = obj
				
				# Naming mesh/skeleton data blocks
				if(self.opt_rename_data):
					obj.data.name = "Data_" + obj.name
					
				# That's it for armatures.
				if(obj.type == 'ARMATURE'):
					continue
				
				# Renaming UV map if there is only one
				if(self.opt_rename_uvs):
					if(len(obj.data.uv_layers) == 1):
						obj.data.uv_layers[0].name = "UVMap"
				
		# Deleting unused materials
		if(self.opt_clean_material_slots):
			bpy.ops.object.delete_unused_material_slots(opt_objects=self.opt_objects)

		# Cleaning node trees
		bpy.ops.material.clean_up(opt_objects=self.opt_objects, 
			opt_fix_name=self.opt_rename_materials, 
			opt_delete_unused_nodes=self.opt_clean_materials, 
			opt_fix_groups=self.opt_clean_materials, 
			opt_fix_tex_refs=self.opt_clean_materials, 
			opt_rename_nodes=self.opt_clean_materials)

		bpy.ops.object.delete_unused_vgroups(opt_objects=self.opt_objects, 
		opt_clearZeroVGroups=self.opt_clearZeroVGroups, 
		opt_clearUnusedVGroups=self.opt_clearUnusedVGroups)
		
		bpy.context.view_layer.objects.active = org_active
		return {'FINISHED'}

class CleanUpScene(bpy.types.Operator):
	bl_idname = "scene.clean_up"
	bl_label = "Clean Up Scene"
	bl_options = {'REGISTER', 'UNDO'}
	
	opt_freeze: BoolProperty(
		name="Freeze Operator", 
		default=False, 
		description="Freeze the operator to change settings without having to wait for the operator to run")
	
	opt_selected_only: BoolProperty(
		name="Selected Objects",
		default=True,
		description="DIsable to affect all objects")

	opt_removeUnusedMats: BoolProperty(
		name="Clean Material Slots", 
		default=True, 
		description="If a material has no faces assigned to it, it will be removed from the object. Objects with no faces are ignored")

	opt_clean_worlds: BoolProperty(
		name="Clean Worlds",
		default=True,
		description="Clean up World node setups")
	
	opt_clean_comp: BoolProperty(
		name="Clean Compositing",
		default=True,
		description="Clean up Compositing nodes")

	opt_clean_nodegroups: BoolProperty(
		name="Clean Nodegroups",
		default=True,
		description="Clean up Nodegroups")

	opt_clearZeroVGroups: BoolProperty(name="Clear Empty Vertex Groups", 
		default=True, 
		description="Clear all vertex groups that have no weights at all. Shouldn't break mirror modifier as long as names end in 'R' and 'L'")
		
	opt_clearUnusedVGroups: BoolProperty(name="Clear Unused Vertex Groups", 
		default=True, 
		description="Clear all vertex groups that aren't used by any modifiers and don't have any equivalent Bones in any of the object's armatures")
	
	opt_clean_material_slots: BoolProperty(
		name="Clean Material Slots",
		default=True,
		description="Delete material slots on selected objects that have no faces assigned")

	opt_rename_materials: BoolProperty(
		name="Fix .00x Material Names", 
		default=False, 
		description="Materials ending in .001 or similar will be attempted to be renamed")

	opt_clean_materials: BoolProperty(
		name="Clean Material Nodes",
		default=True,
		description="Remove unused nodes, resize and rename image nodes, hide unused group node sockets, and center nodes")

	def execute(self, context):
		if(self.opt_freeze):
			return {'FINISHED'}

		org_active = bpy.context.view_layer.objects.active

		if(self.opt_clean_worlds):
			for w in bpy.data.worlds:
				if(w.use_nodes):
					clean_node_tree(w.node_tree)

		if(self.opt_clean_comp):
			for s in bpy.data.scenes:
				if(s.use_nodes):
					clean_node_tree(s.node_tree)
		
		if(self.opt_clean_nodegroups):
			for nt in bpy.data.node_groups:
				clean_node_tree(nt)
		
		objects = 'Selected' if self.opt_selected_only else 'All'
		bpy.ops.object.clean_up(opt_objects=objects, 
			opt_clearZeroVGroups=self.opt_clearZeroVGroups, 
			opt_clearUnusedVGroups=self.opt_clearUnusedVGroups, 
			opt_clean_material_slots=self.opt_clean_material_slots, 
			opt_rename_materials=self.opt_rename_materials, 
			opt_clean_materials=self.opt_clean_materials)
		
		bpy.context.view_layer.objects.active = org_active
		return {'FINISHED'}

def draw_func_CleanUpScene(self, context):
	self.layout.operator(CleanUpScene.bl_idname, text=CleanUpScene.bl_label)

def register():
	from bpy.utils import register_class
	register_class(DeleteUnusedMaterialSlots)
	register_class(DeleteUnusedVGroups)
	register_class(CleanUpObjects)
	#register_class(CleanUpMeshes)
	#register_class(CleanUpArmatures)
	register_class(CleanUpMaterials)
	register_class(CleanUpScene)

def unregister():
	from bpy.utils import unregister_class
	unregister_class(DeleteUnusedMaterialSlots)
	unregister_class(DeleteUnusedVGroups)
	unregister_class(CleanUpObjects)
	#unregister_class(CleanUpMeshes)
	#unregister_class(CleanUpArmatures)
	unregister_class(CleanUpMaterials)
	unregister_class(CleanUpScene)