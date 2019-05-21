import bpy, sys
from . import utils

# Copy all drivers from active to one selected bone.
# Can also switch out driver variable targets and flip desired variable axes on the new drivers.

# To Mirror drivers, set target_dict to None and enable X and Y flip.

top_to_bottom_dict = {	"CTR-Lip_Top.L" : "CTR-Lip_Bot.L",
						"CTR-Lip_Corner_Top.L" : "CTR-Lip_Corner_Bot.L",
						"CTR-Lip_Top.M" : "CTR-Lip_Bot.M",
						"CTR-Lip_Top.R" : "CTR-Lip_Bot.R",
						"CTR-Lip_Corner_Top.R" : "CTR-Lip_Corner_Bot.R"}

lip_to_laughline_dict = {
	"CTR-Lip_Top.L" : "CTR-LaughLine.L.003",
	"CTR-Lip_Corner_Top.L" : "CTR-LaughLine.L.002",
	"CTR-Lip_Corner_Bot.L" : "CTR-LaughLine.L.001",
	"CTR-Lip_Bot.L" : "CTR-LaughLine.L",
	"CTR-Lip_Bot.M" : "CTR-LaughLine.M",
	
	"CTR-Lip_Top.R" : "CTR-LaughLine.R.003",
	"CTR-Lip_Corner_Top.R" : "CTR-LaughLine.R.002",
	"CTR-Lip_Corner_Bot.R" : "CTR-LaughLine.R.001",
	"CTR-Lip_Bot.R" : "CTR-LaughLine.R",
}

lip_to_eye_bot_l = {
	"CTR-Lip_Bot.M" : "CTR-Eyelid_Bot_1.L",
	"CTR-Lip_Bot.L" : "CTR-Eyelid_Bot_2.L",
	"CTR-Lip_Corner_Bot.L" : "CTR-Eyelid_Bot_3.L",
	"CTR-Lip_Corner_Top.L" : "CTR-Eyelid_Bot_4.L",
	"CTR-Lip_Top.L" : "CTR-Eyelid_Bot_5.L",
}

eye_bot_to_top = {
	"CTR-Eyelid_Bot_1.L" : "CTR-Eyelid_Top_1.L",
	"CTR-Eyelid_Bot_2.L" : "CTR-Eyelid_Top_2.L",
	"CTR-Eyelid_Bot_3.L" : "CTR-Eyelid_Top_3.L",
	"CTR-Eyelid_Bot_4.L" : "CTR-Eyelid_Top_4.L",
	"CTR-Eyelid_Bot_5.L" : "CTR-Eyelid_Top_5.L",
}

target_dict = None

flip_x = True
flip_y = True
flip_z = False

armature = bpy.context.object
bones = armature.pose.bones

from_bone = bpy.context.active_bone.name						# Bone to copy drivers from
to_bones = bpy.context.selected_pose_bones						# Bones to copy drivers to

for to_bone in to_bones:
	if(to_bone.name == from_bone):continue

	for d in armature.animation_data.drivers:					# Look through every driver on the armature
		if('pose.bones["' + from_bone + '"]' in d.data_path):	# If the driver belongs to the active bone
			### Copying driver to selected bone...
			
			# The way drivers on bones work is weird af. You have to create the driver relative to the bone, but you have to read the driver relative to the armature. So d.data_path might look like "pose.bones["bone_name"].bone_property" but when we create a driver we just need the "bone_property" part.
			data_path = d.data_path.split("].")[1]
			to_bone.driver_remove(data_path)
			new_d = to_bone.driver_add(data_path)
			
			expression = d.driver.expression
			
			print("")
			print(expression)
					
			# Copy the variables
			for from_var in d.driver.variables:
				to_var = new_d.driver.variables.new()
				to_var.type = from_var.type
				to_var.name = from_var.name
				print(to_var.name)
				print(from_var.targets[0].transform_type)
				
				target_bone = from_var.targets[0].bone_target
				if(target_dict == None):
					target_bone = utils.flip_name(target_bone)
				else:
					new_target_bone = target_dict.get(target_bone)
					if(new_target_bone):
						target_bone = new_target_bone
				
				to_var.targets[0].id 				= from_var.targets[0].id
				to_var.targets[0].bone_target 		= target_bone
				to_var.targets[0].data_path 		= from_var.targets[0].data_path#.replace(fb, to_bones[i])
				to_var.targets[0].transform_type 	= from_var.targets[0].transform_type
				to_var.targets[0].transform_space 	= from_var.targets[0].transform_space
				# TODO: If transform is X Rotation, have a "mirror" option, to invert it in the expression. Better yet, detect if the new_target_bone is the opposite of the original.
				
				print(from_var.targets[0].transform_type)
				if( to_var.targets[0].bone_target and
					"SCALE" not in from_var.targets[0].transform_type and
					(from_var.targets[0].transform_type.endswith("_X") and flip_x) or
					(from_var.targets[0].transform_type.endswith("_Y") and flip_y) or
					(from_var.targets[0].transform_type.endswith("_Z") and flip_z)
					):
					# This is painful, I know.
					if("-"+to_var.name in expression):
						expression = expression.replace("-"+to_var.name, "+"+to_var.name)
						print(1)
					elif("+ "+to_var.name in expression):
						expression = expression.replace("+ "+to_var.name, "- "+to_var.name)
						print(2)
					else:
						expression = expression.replace(to_var.name, "-"+to_var.name)
						print("3")
			
			# Copy the expression
			new_d.driver.expression = expression
			print(expression)