import bpy

for b in bpy.context.object.pose.bones:
	for k in b.keys():
		if type(b[k]) in (int, float):
			b.property_overridable_library_set(f'["{k}"]', True)