# This script changes the speed of all objects' animation in the scene, while 
# ensuring that there is a keyframe on every frame, and no keyframes on sub-frames.

import bpy

old_framerate = 30
new_framerate = 24
scale = new_framerate / old_framerate

obj = bpy.context.object
action = obj.animation_data.action

for o in bpy.data.objects:
	if not hasattr(o, 'animation_data'): continue
	if not o.animation_data: continue
	if not o.animation_data.action: continue

	for fcurve in o.animation_data.action.fcurves:
		print(f"{fcurve.data_path} {fcurve.array_index}")

		# Scale time
		for kp in fcurve.keyframe_points:
			kp.co[0] *= scale
			kp.handle_left[0] *= scale
			kp.handle_right[0] *= scale

		# Ensure keyframe on every frame
		for i in range(int(fcurve.range()[0]), int(fcurve.range()[1])):
			value = fcurve.evaluate(i)
			fcurve.keyframe_points.insert(i, value)

		# Delete keyframes that aren't on an exact frame
		for kp in reversed(fcurve.keyframe_points):
			if kp.co[0] % 1.0 != 0.0:
				fcurve.keyframe_points.remove(kp)