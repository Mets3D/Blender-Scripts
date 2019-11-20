import bpy

# Whenever committing, run this thing with rigging=False.

# In order to not accidentally put location keyframes for bones that I shouldn't, I want to lock location of some bones while working. Needs to be unlocked before commits though, for animators.

rigging = False

for b in bpy.data.objects['RIG-Rain'].pose.bones:
	if b.name.startswith("P-BB-") or b.name.startswith("P-GRP-"):
		b.lock_rotation = [rigging] * 3
		b.lock_rotation_w = rigging
	elif b.name.startswith("BB-") or b.name.startswith("GRP-"):
		b.lock_location = [rigging]*3

body = bpy.data.objects['GEO-rain_body']

rig = bpy.data.objects['RIG-Rain']
for o in rig.children:
	o.show_only_shape_key = False

if not rigging:
	rig.animation_data.action = bpy.data.actions['Rain_Defaults']