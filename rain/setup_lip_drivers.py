import bpy
from mets_tools.armature_nodes.driver import *

for b in bpy.context.object.pose.bones:
	for c in b.constraints:
		if c.type == 'ACTION' and c.action.name=='Rain_Lips_Corner_Up+Wide':	
			# Setup drivers for Action: Lips_Up+Wide
			d = Driver()
			d.type = 'SCRIPTED'

			wide = d.make_var("wide")
			wide.type = 'TRANSFORMS'

			d.expression = "wide * 20"

			wide_t = wide.targets[0]
			wide_t.id = bpy.data.objects['RIG-Rain']
			wide_t.bone_target = c.subtarget
			wide_t.transform_space = 'LOCAL_SPACE'
			wide_t.transform_type = 'LOC_Z'
			d.make_real(c, "influence")
			