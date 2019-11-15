import bpy
from mets_tools.armature_nodes.driver import Driver

rig = bpy.context.object
prop_dict = {}
for i, cp in enumerate(rig.rig_colorproperties):
	prop_dict[cp.name] = i

rig.rig_colorproperties.clear()
mats_done = []
for o in rig.children:
	for ms in o.material_slots:
		m = ms.material
		if m in mats_done: continue
		mats_done.append(m)
		cp = rig.rig_colorproperties.add()
		cp.name = m.name
		cp.default = cp.color = m.diffuse_color[:-1]

for o in rig.children:
	for ms in o.material_slots:
		m = ms.material
		
		# If this errors, ensure the properties are up date with populate_color_properties.py
		cpi = prop_dict[m.name]
		
		# Add drivers to the first 3 values of the material color
		for i in range(3):
			d = Driver()
			d.type = 'SUM'

			var = d.make_var("var")
			var.type = 'SINGLE_PROP'

			var_t = var.targets[0]
			var_t.id = rig
			var_t.data_path = 'rig_colorproperties[' + str(cpi) + '].color[' + str(i) + ']'
			d.make_real(m, "diffuse_color", index=i)
			