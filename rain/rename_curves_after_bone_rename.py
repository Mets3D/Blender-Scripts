import bpy

bone_dict = {
	"IK-MSTR-P-Wrist.L" : "IK-MSTR-Wrist.L",
	"IK-MSTR-P-Wrist.R" : "IK-MSTR-Wrist.R",
	"IK-MSTR-P-Foot.L" : "IK-MSTR-Foot.L",
	"IK-MSTR-P-Foot.R" : "IK-MSTR-Foot.R",
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