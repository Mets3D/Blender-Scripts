import bpy

bone_dict = {
	"DEF_CTR-Spine" : "CTR-DEF-Spine",
	"DEF_CTR-Belly" : "CTR-DEF-Belly",
	"DEF_CTR-Chest" : "CTR-DEF-Chest",
}

for a in bpy.data.actions:
	for name in bone_dict.keys():
		for c in a.fcurves:
			if(name in c.data_path):
				c.data_path = c.data_path.replace(name, bone_dict[name])
				group = a.groups.get(bone_dict[name])
				if(not group):
					group = a.groups.new(bone_dict[name])
				c.group = group