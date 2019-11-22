import bpy

# Assume selected objects are a rig's shapes, and the active object is the armature.
# Resize every rig shape such that their longest dimension is 1 unit long.
# Go thorugh every bone in the rig and if bone_size==False, adjust the bone size according to the new scale of the shape object.
# Apply the scale on the shape objects.

from mathutils import Matrix

armature = bpy.context.object
assert armature.type=='ARMATURE'

for o in bpy.context.selected_objects:
	if o == armature: continue
	if o.type!='MESH': continue

	# Reset transforms
	Matrix.identity(o.matrix_local)
	# Divide uniform scale by longest dimension.
	o.scale /= max(o.dimensions)


used_shapes = []
for b in armature.pose.bones:
	if b.custom_shape:
		if b.custom_shape not in used_shapes:
			used_shapes.append(b.custom_shape)
		if not b.use_custom_shape_bone_size:
			b.custom_shape_scale /= b.custom_shape.scale[0]
		else:
			b.custom_shape_scale = 1

armature.select_set(False)
for o in bpy.context.selected_objects:
	if o not in used_shapes:
		# Just move em to the side for easy deletion.
		o.location.x = 2

bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)