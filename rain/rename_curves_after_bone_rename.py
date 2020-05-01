import bpy

bone_dict = {
	"Hook_Mouth_00" : "Hook_Mouth.L",
	"Hook_L_Mouth_00" : "Hook_L_Mouth.L",
	"Hook_R_Mouth_00" : "Hook_R_Mouth.L",
	
	"Hook_Mouth_02" : "Hook_Mouth.R",
	"Hook_L_Mouth_02" : "Hook_R_Mouth.R",
	"Hook_R_Mouth_02" : "Hook_L_Mouth.R",
	
	"Hook_L_Mouth_01" : "Hook_Top_Mouth.L",
	"Hook_R_Mouth_01" : "Hook_Top_Mouth.R",
	
	"Hook_L_Mouth_03" : "Hook_Bot_Mouth.R",
	"Hook_R_Mouth_03" : "Hook_Bot_Mouth.L",
	
	"Hook_Eye.L_00" : "Hook_Eye_00.L",
	"Hook_Eye.L_01" : "Hook_Eye_01.L",
	"Hook_Eye.L_02" : "Hook_Eye_02.L",
	"Hook_Eye.L_03" : "Hook_Eye_03.L",
	
	"Hook_Eye.R_00" : "Hook_Eye_00.R",
	"Hook_Eye.R_01" : "Hook_Eye_01.R",
	"Hook_Eye.R_02" : "Hook_Eye_02.R",
	"Hook_Eye.R_03" : "Hook_Eye_03.R",
	
	"Hook_L_Eye.L_00" : "Hook_L_Eye_00.L",
	"Hook_R_Eye.L_00" : "Hook_R_Eye_00.L",
	"Hook_L_Eye.L_01" : "Hook_L_Eye_01.L",
	"Hook_R_Eye.L_01" : "Hook_R_Eye_01.L",
	"Hook_L_Eye.L_02" : "Hook_L_Eye_02.L",
	"Hook_R_Eye.L_02" : "Hook_R_Eye_02.L",
	"Hook_L_Eye.L_03" : "Hook_L_Eye_03.L",
	"Hook_R_Eye.L_03" : "Hook_R_Eye_03.L",
	
	"Hook_L_Eye.R_00" : "Hook_L_Eye_00.R",
	"Hook_R_Eye.R_00" : "Hook_R_Eye_00.R",
	"Hook_L_Eye.R_01" : "Hook_L_Eye_01.R",
	"Hook_R_Eye.R_01" : "Hook_R_Eye_01.R",
	"Hook_L_Eye.R_02" : "Hook_L_Eye_02.R",
	"Hook_R_Eye.R_02" : "Hook_R_Eye_02.R",
	"Hook_L_Eye.R_03" : "Hook_L_Eye_03.R",
	"Hook_R_Eye.R_03" : "Hook_R_Eye_03.R",
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