import bpy
from rna_prop_ui import rna_idprop_ui_create

for b in bpy.context.object.pose.bones:
	if "Properties" in b.name or 'rot_mode' in b:
		if '_RNA_UI' not in b: continue
		for prop_name in b['_RNA_UI'].keys():
			prop = b['_RNA_UI'][prop_name]
			rna_idprop_ui_create(
	            b, 
	            prop_name, 
	            default = b[prop_name],
	            min = prop['min'], 
	            max = prop['max'], 
	            soft_min = prop['soft_min'], 
	            soft_max = prop['soft_max'],
	            description = prop['description'],
	            overridable = True,
	            #subtype = self.subtype
	        )