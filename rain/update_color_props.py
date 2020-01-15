import bpy
from mets_tools.armature_nodes.driver import Driver

# This script is meant for maintaining Rain's Viewport Display rig UI
# Which lets us change viewport colors when the character is linked and proxied.
# as requested by the animation department.

# It updates the color properties that are stored in the rig properties
# And then updates the drivers that drive the viewport colors, so that they copy said rig properties.
# The rig color properties can then be displayed in the UI via cloudrig.py, and the colors can be changed even on a linked character.
# (This is just for viewport colors, not render)

rig = bpy.context.object
prop_dict = {}
for i, cp in enumerate(rig.rig_colorproperties):
	prop_dict[cp.name] = i

# Populate color properties
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
			