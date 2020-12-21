import bpy

bone_dict = {
	"STR-I-Cap+_Ring2.L" : "STR-I-Cap_Base+Edge2.L",
	"STR-I-Cap+_Ring4.R" : "STR-I-Cap_Base+Edge2.R",
	"STR-I-Cap_Front+Ring1" : "STR-I-Cap_Base_Front+Edge1",
	"STR-I-Cap_Back+Ring3" : "STR-I-Cap_Base_Back+Edge2",
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