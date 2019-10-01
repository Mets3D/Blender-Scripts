import bpy

# In order to apply (UNIFORM) scale on an armature without breaking the rigging, we need to apply the scale factor to all location and scale values used by the rig.
# This means listing every property of every constraint that references a location or scale,
# Every driver expression that references a variable that is a location or scale needs to get this arbitrary scale value embedded in it, so this scale value will spread all over the rig like cancer, instead of being contained in a single Empty that would cause no harm.
# Every location and scale curve used by Action constraints...

o = bpy.context.object
scale = o.scale[0]  #0.5196
do_round = True 	# Round some less important values, like bone shape size.

locs = scales = []

min_max = [
	'min_x',
	'max_x',
	'min_y',
	'max_y',
	'min_z',
	'max_z',
]

for b in o.pose.bones:
	if(not b.use_custom_shape_bone_size):
		b.custom_shape_scale *= scale
		if(do_round):
			b.custom_shape_scale = round(b.custom_shape_scale, 2)
	for c in b.constraints:
		if(c.type in ['LIMIT_LOCATION', 'LIMIT_SCALE']):
			locs = min_max
		elif(c.type=='LIMIT_DISTANCE'):
			locs = ['distance']
		elif(c.type=='TRANSFORM'):
			locs = [
				"from_min_x", "from_max_x", "to_min_x", "to_max_x",
				"from_min_y", "from_max_y", "to_min_y", "to_max_y",
				"from_min_z", "from_min_z", "to_min_z", "to_max_z"
			]
			scales = [
				"from_min_x_scale", "from_max_x_scale", "to_min_x_scale", "to_max_x_scale",
				"from_min_y_scale", "from_max_y_scale", "to_min_y_scale", "to_max_y_scale",
				"from_min_z_scale", "from_min_z_scale", "to_min_z_scale", "to_max_z_scale"
			]
		elif(c.type=='STRETCH_TO'):
			locs = ["rest_length"]
		elif(c.type=='ACTION'):
			locs = ["min", "max"]
		elif(c.type=='FLOOR'):
			locs = ["offset"]
		else:
			continue
		
		for prop in locs:
			new_value = getattr(c, prop) * scale
			setattr(c, prop, new_value)

for action in bpy.data.actions:
	for cur in action.fcurves:
		if( ("location" in cur.data_path) ):
			for kf in cur.keyframe_points:
				kf.co[1] *= scale
				kf.handle_left[1] *= scale
				kf.handle_right[1] *= scale
		if( ("scale" in cur.data_path) ):
			pass # I guess we don't need to touch scale?

bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)