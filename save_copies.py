import bpy, os

# Save copies of this blend file under different names. Add extra renaming/processing/saving params as needed.

copies = 6  # Excluding self.

def get_collections():
	ret = []
	for c in bpy.data.collections:
		if c.name.startswith("CH-"):
			ret.append(c)
	return ret

def get_rigs():
	ret = []
	for c in bpy.data.objects:
		if c.name.startswith("RIG-"):
			ret.append(c)
	return ret

for i in range(0, copies):
	suffix = ".%d"%i
	for c in get_collections():
		if i > 0:
			c.name = c.name[:-2]
		c.name = c.name + suffix
	for r in get_rigs():
		if i > 0:
			r.name = r.name[:-2]
		r.name = r.name + suffix

	filepath = bpy.data.filepath.replace(".blend", ".%d.blend"%i)
	bpy.ops.wm.save_as_mainfile(filepath=filepath, copy=True)