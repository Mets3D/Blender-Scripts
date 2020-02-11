# Save copies of this blend file under different names. Add extra renaming/processing/saving params as needed.

import bpy, os

copies = 8  # Excluding self.

for i in range(0, copies):
    filepath = bpy.data.filepath.replace(".blend", ".%d.blend"%i)
    bpy.ops.wm.save_as_mainfile(filepath=filepath, copy=True)