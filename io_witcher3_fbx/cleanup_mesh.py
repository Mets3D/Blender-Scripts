import bpy
from math import pi
import bmesh

def cleanup_mesh(obj, 
		remove_doubles=False, 
		quadrangulate=False, 
		weight_normals=True, 
		seams_from_islands=True, 
		clear_unused_UVs=True, 
		rename_single_UV=True):
	
	# Mode management
	org_active = bpy.context.object
	org_mode = org_active.mode
	org_selected = bpy.context.selected_objects[:]
	bpy.ops.object.mode_set(mode='OBJECT')
	bpy.ops.object.select_all(action='DESELECT')
	bpy.context.view_layer.objects.active = obj
	bpy.ops.object.mode_set(mode='EDIT')
	
	# Setting auto-smooth to 180 is necessary so that splitnormals_clear() doesn't mark sharp edges
	obj.data.use_auto_smooth = True
	obj.data.auto_smooth_angle = pi
	bpy.ops.mesh.customdata_custom_splitnormals_clear()
	
	if(quadrangulate):
		bpy.ops.mesh.tris_convert_to_quads(shape_threshold=1.0472, uvs=True, materials=True)
	
	if(remove_doubles):
		bpy.ops.mesh.remove_doubles(threshold=0.0001)
		bpy.ops.mesh.mark_sharp(clear=True)
	
	bpy.ops.object.mode_set(mode='OBJECT')
	bpy.context.view_layer.objects.active = obj	# Active object needs to be a mesh for calculate_weighted_normals()
	if(weight_normals and remove_doubles):	# Weight normals only works with remove doubles, otherwise throws ZeroDivisionError.
		bpy.ops.object.calculate_weighted_normals()
	bpy.ops.object.mode_set(mode='EDIT')
	
	### Removing useless UVMaps
	if(clear_unused_UVs):
		mesh = obj.data
		bm = bmesh.from_edit_mesh(mesh)

		for uv_idx in reversed(range(0, len(mesh.uv_layers))):			# For each UV layer
			delet_this=True
			mesh.uv_layers.active_index = uv_idx
			bm.faces.ensure_lookup_table()
			for f in bm.faces:						# For each face
				for l in f.loops:					# For each loop(whatever that means)
					if(l[bm.loops.layers.uv.active].uv[0] != 0.0):	# If the loop's UVs first vert's x coord is NOT 0
						delet_this=False
				if(delet_this):
					break
			if(delet_this):
				obj.data.uv_layers.remove(obj.data.uv_layers[uv_idx])
	
		bmesh.update_edit_mesh(mesh, True)
		
	# Renaming single UV maps
	if(len(mesh.uv_layers)==1 and rename_single_UV):
		mesh.uv_layers[0].name = 'UVMap'
	
	# Seams from islands
	if(seams_from_islands):
		bpy.ops.uv.seams_from_islands(mark_seams=True, mark_sharp=False)
	
	# Mode management
	bpy.ops.object.mode_set(mode='OBJECT')
	for o in org_selected:
		o.select_set(True)
	bpy.context.view_layer.objects.active = org_active
	bpy.ops.object.mode_set(mode=org_mode)
	
class CleanUpMesh(bpy.types.Operator):
	"""Clean up meshes"""
	bl_idname = "object.mesh_cleanup"
	bl_label = "Clean Up Mesh"
	bl_options = {'REGISTER', 'UNDO'}
	
	remove_doubles: bpy.props.BoolProperty(
		name="Remove Doubles",
		description="Enable remove doubles",
		default=False
	)
	
	quadrangulate: bpy.props.BoolProperty(
		name="Tris to Quads",
		description="Enable Tris to Quads (UV Seams enabledd)",
		default=False
	)
	
	weight_normals: bpy.props.BoolProperty(
		name="Weight Normals",
		description="Enable weighted normals",
		default=False
	)
	
	seams_from_islands: bpy.props.BoolProperty(
		name="Seams from Islands",
		description="Create UV seams based on UV islands",
		default=False
	)
	
	clear_unused_UVs: bpy.props.BoolProperty(
		name="Delete Unused UV Maps",
		description="If all UV verts' X coordinate is 0, the UV map will be deleted.",
		default=True
	)
	
	rename_single_UV: bpy.props.BoolProperty(
		name="Rename Singular UV Maps",
		description="If an object is only left with one UV map, rename it to the default name, 'UVMap'.",
		default=True
	)
	
	
	def execute(self, context):
		for o in bpy.context.selected_objects:
			cleanup_mesh(o, 
				self.remove_doubles, 
				self.quadrangulate, 
				self.weight_normals, 
				self.seams_from_islands, 
				self.clear_unused_UVs, 
				self.rename_single_UV)
		return {'FINISHED'}

def register():
	from bpy.utils import register_class
	register_class(CleanUpMesh)

def unregister():
	from bpy.utils import unregister_class
	unregister_class(CleanUpMesh)