import bpy

bone_dict = {
	"DEF-Hair_Default_Ponytail1" : "FK-Hair_Ponytail1",
	"DEF-Hair_Default_Ponytail2" : "FK-Hair_Ponytail2",
	"DEF-Hair_Default_Ponytail3" : "FK-Hair_Ponytail3",
	"DEF-Hair_Default_Ponytail4" : "FK-Hair_Ponytail4",
	"DEF-Hair_Default_Strand1" : "FK-Hair_Strand1",
	"DEF-Hair_Default_Strand2" : "FK-Hair_Strand2",
	"DEF-Scarf1" : "FK-Scarf1",
	"DEF-Scarf2" : "FK-Scarf2",
	"DEF-Scarf3" : "FK-Scarf3",
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