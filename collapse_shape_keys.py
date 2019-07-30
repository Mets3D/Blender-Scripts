import bpy

# On all selected objects:
# Create New Shape From Mix
# Blend From Shape from Basis into the new shape
# Nuke all shape keys.

for o in bpy.context.selected_objects:
	# Get Shape Keys datablock
	shape_keys = o.data.shape_keys.key_blocks
	
	# Create New Shape From Mix
	bpy.context.view_layer.objects.active = o
	bpy.ops.object.shape_key_add(from_mix=True)

	# Blend from Shape Basis into new shape
	bpy.context.object.active_shape_key_index = 0
	bpy.ops.object.mode_set(mode='EDIT')
	bpy.ops.mesh.reveal
	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.mesh.blend_from_shape(shape=shape_keys[-1].name, blend=1, add=False)

	# Nuke all shape keys.
	bpy.ops.object.mode_set(mode='OBJECT')
	bpy.ops.object.shape_key_remove(all=True)
	
	# Rain specific stuff
	for m in o.modifiers:
		apply_types = ['SOLIDIFY', 'MIRROR']
		if('teeth' in o.name):
			apply_types.append('SUBSURF')
		if(m.type=='SUBSURF'):
			m.render_levels = 1
			m.levels = 1
		if(m.type in apply_types):
			bpy.ops.object.modifier_apply(apply_as='DATA', modifier=m.name)
	o.modifiers.clear()