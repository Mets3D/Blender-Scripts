import bpy

# Rename curves from STR to STR-P in case I start keyframing the wrong bones. 
# Actions must be on the STR-P bones for the lips for correct constraint order.
# (Actions must come before Armature constraint)

rig = bpy.context.object
for a in bpy.data.actions:
	for c in a.fcurves:
		data_path = c.data_path
		if not 'STR-' in data_path: continue
		if 'P-STR' in data_path:
			print("why is this here?")
			print(a)
			print(data_path)
			continue

		new_path = data_path.replace("STR-", "P-STR-")
		bone_name = "P-STR-" + data_path.split("STR-")[1].split('"]')[0]
		print(bone_name)
		bone = rig.pose.bones.get(bone_name)
		if not bone: continue

		c.data_path = new_path
		group = a.groups.get(bone_name)
		if(not group):
			group = a.groups.new(bone_name)
		c.group = group