import bpy

# This script is meant for maintaining Rain's Viewport Display rig UI
# Which lets us change viewport colors when the character is linked and proxied.
# as requested by the animation department.

# It updates the color properties that are stored in the rig properties
# And then updates the drivers that drive the viewport colors, so that they copy said rig properties.
# The rig color properties can then be displayed in the UI via cloudrig.py, and the colors can be changed even on a linked character.
# (This is just for viewport colors, not render)

rig = bpy.context.object

# Populate color properties
rig.cloud_colors.clear()
mats_done = []
for o in rig.children:
	for ms in o.material_slots:
		m = ms.material
		if m in mats_done: continue
		mats_done.append(m)
		cp = rig.cloud_colors.add()
		cp.name = m.name
		cp.default = cp.current = m.diffuse_color[:-1]

prop_dict = {}	# color property Name : Index map, which we will need for driver data paths, since we need to reference the color property by index then, but find it based on material name.
for i, cp in enumerate(rig.cloud_colors):
	prop_dict[cp.name] = i

for o in rig.children:
	for ms in o.material_slots:
		m = ms.material
		
		color_index = prop_dict[m.name]
		
		# Add drivers to the first 3 values of the material color
		for i in range(3):
			fcurve = m.driver_remove("diffuse_color", i)
			fcurve = m.driver_add("diffuse_color", i)
			d = fcurve.driver
			d.type = 'SUM'

			var = d.variables.new()
			var.type = 'SINGLE_PROP'

			var_t = var.targets[0]
			var_t.id = rig
			var_t.data_path = f"cloud_colors[{color_index}].current[{i}]"