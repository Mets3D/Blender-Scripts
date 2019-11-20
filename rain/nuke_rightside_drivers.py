import bpy

drivers = bpy.context.object.animation_data.drivers
for d in drivers:
	bone = d.data_path.split('["')[1].split('"]')[0]
	
	if bone.endswith(".R"):
		drivers.remove(d)