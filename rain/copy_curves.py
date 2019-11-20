import bpy
from mets_tools import utils

# Copy animation from active to selected bones in active action.

active_bone = bpy.context.active_pose_bone
selected_bones = bpy.context.selected_pose_bones
action = bpy.context.object.animation_data.action

for cur in action.fcurves:
	if(active_bone.name in cur.data_path):
		# Copy this curve to all selected bones.	
		for b in selected_bones:
			if b == active_bone: continue
			
			# If curve already exists, delete it first.
			target_data_path = cur.data_path.replace(active_bone.name, b.name)
			old_cur = action.fcurves.find(target_data_path, index=cur.array_index)
			if old_cur:
				action.fcurves.remove(old_cur)
			
			# Create curve
			new_cur = action.fcurves.new(target_data_path, index=cur.array_index, action_group=b.name)
			utils.copy_attributes(cur, new_cur, skip=["data_path", "group"])
			
			# Copy keyframes
			for kf in cur.keyframe_points:
				new_kf = new_cur.keyframe_points.insert(kf.co[0], kf.co[1])
				utils.copy_attributes(kf, new_kf, skip=["data_path"])