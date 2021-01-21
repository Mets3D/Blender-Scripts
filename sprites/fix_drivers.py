# After transferring rig from one character to another, fix the character property drivers.

import bpy

from_char = "Rex"
to_char = "Ellie"

rig_helper_mesh = bpy.data.objects['GEO-ellie_head_rig_helper']
metarig = bpy.data.objects['META-ellie']

for b in metarig.pose.bones:
	for c in b.constraints:
		if c.type=='SHRINKWRAP':
			c.target = rig_helper_mesh

for fcurve in metarig.animation_data.drivers:
	if "Properties_Character_"+from_char in fcurve.data_path:
		fcurve.data_path = fcurve.data_path.replace("Properties_Character_"+from_char, "Properties_Character_"+to_char)
	for v in fcurve.driver.variables:
		if v.type=='SINGLE_PROP':
			v.targets[0].data_path = v.targets[0].data_path.replace("Properties_Character_"+from_char, "Properties_Character_"+to_char)