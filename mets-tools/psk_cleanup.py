import bpy
import bmesh

# .psk models import as a single mesh with multiple UV channels. Each UV channel corresponds to a material.
# This script will select every UV face that isn't on 0.0 on each UV laayer, separate that part of the mesh into an object and clean up material and UV slots.
# Wprls pm pme se;ected object for now

def assign_materials_by_uv_layers():
	obj = bpy.context.object
	mesh = obj.data
	orig_mode = obj.mode
	bpy.ops.object.mode_set(mode='EDIT')

	bm = bmesh.from_edit_mesh(mesh)

	for uv_idx in range(0, len(mesh.uv_layers)):			# For each UV layer
		obj.active_material_index = uv_idx
		mesh.uv_layers.active_index = uv_idx
		bpy.ops.mesh.select_all(action='DESELECT')
		bm.faces.ensure_lookup_table()
		for f in bm.faces:						# For each face
			for l in f.loops:					# For each loop(whatever that means)
				if(l[bm.loops.layers.uv.active].uv[0] != 0.0):	# If the loop's UVs first vert are NOT in the bottom left corner
					f.select_set(True)			# Select this face
		bpy.ops.object.material_slot_assign()
		obj.active_material.name = mesh.uv_layers[uv_idx].name
		
	bmesh.update_edit_mesh(mesh, True)
	bpy.ops.object.mode_set(mode=orig_mode)
	
assign_materials_by_uv_layers()

# Separating object by materials
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.separate(type='MATERIAL')
bpy.ops.object.mode_set(mode='OBJECT')

# Cleaning up objects
for o in bpy.context.selected_objects:
	# Cleaning up UV Maps
	mat_name = o.material_slots[0].name
	for uv_map in reversed(o.data.uv_layers):
		if(uv_map.name not in mat_name):
			o.data.uv_layers.remove(uv_map)
	if(len(o.data.uv_layers) > 0):
		o.data.uv_layers[0].name = "UVMap"
	
	# Cleaning mesh
	bpy.context.view_layer.objects.active = o
	bpy.ops.object.mode_set(mode='EDIT')
	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.mesh.tris_convert_to_quads(uvs=True, seam=True)
	bpy.ops.mesh.faces_shade_smooth()
	if(len(o.data.uv_layers) > 0):
		bpy.ops.uv.seams_from_islands()
	bpy.ops.object.mode_set(mode='OBJECT')
	if(hasattr(bpy.ops.object, "calculate_weighted_normals")):	# Check if the Weighted Normals addon is available
		bpy.ops.object.calculate_weighted_normals()