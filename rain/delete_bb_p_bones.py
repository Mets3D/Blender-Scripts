import bpy
from mets_tools import utils

"""This was in the end not used because it broke the Auto+Tangent BBone setup... But, maybe there's a way to get rid of these bones without breaking that setup?"""

# P-BB bones are parents of BB- bones that hold constraints.
# They were originally created to hold Action constraints that affected location, since before 2.82 or so, such constraints would mess up the bone's rotation pivot.

# Take all bones that start with P-BB
# Find corresponding BB
# Go through every action
# Rename location curves from P-BB to BB
# If an Action constraint with the same name doesn't exist on BB, create it.
# Delete Action constraint from P-BB
# If there are no constraints remaining on P-BB, delete it.

armature = bpy.context.object
bones = armature.pose.bones

p_bb_bones = [b for b in bones if b.name.startswith("P-BB")]

def copy_drivers(armature, from_bone, to_bone, from_constraint=None, to_constraint=None):
	# Mirrors all drivers from one bone to another. from_bone and to_bone should be pose bones.
	# If from_constraint is specified, to_constraint also must be, and then copy and mirror drivers between constraints instead of bones.
	# TODO: This should use new abstraction implementation, and be split up to copy_driver and flip_driver, each of which should handle only one driver at a time.
	#	Actually, copy_driver would just be reading a driver into an abstract driver and then making it real somewhere else.
	if(not armature.animation_data): return	# No drivers to mirror.

	for d in armature.animation_data.drivers:					# Look through every driver on the armature
		if not ('pose.bones["' + from_bone.name + '"]' in d.data_path): continue		# Driver doesn't belong to source bone, skip.
		if("constraints[" in d.data_path and from_constraint==None): continue			# Driver is on a constraint, but no source constraint was given, skip.
		if(from_constraint!=None and from_constraint.name not in d.data_path): continue	# Driver is on a constraint other than the given source constraint, skip.
		
		### Copying mirrored driver to target bone...
		
		# The way drivers on bones work is weird af. You have to create the driver relative to the bone, but you have to read the driver relative to the armature. So d.data_path might look like "pose.bones["bone_name"].bone_property" but when we create a driver we just need the "bone_property" part.
		data_path_from_bone = d.data_path.split("].", 1)[1]
		new_d = None
		if("constraints[" in data_path_from_bone):
			data_path_from_constraint = data_path_from_bone.split("].", 1)[1]
			# Armature constraints need special special treatment...
			if(from_constraint.type=='ARMATURE' and "targets[" in data_path_from_constraint):
				target_idx = int(data_path_from_constraint.split("targets[")[1][0])
				target = to_constraint.targets[target_idx]
				# Weight is the only property that can have a driver on an Armature constraint's Target object.
				target.driver_remove("weight")
				new_d = target.driver_add("weight")
			else:
				to_constraint.driver_remove(data_path_from_constraint)
				new_d = to_constraint.driver_add(data_path_from_constraint)
		else:
			to_bone.driver_remove(data_path_from_bone)
			new_d = to_bone.driver_add(data_path_from_bone)
			
		expression = d.driver.expression
		
		# Copy the variables
		for from_var in d.driver.variables:
			to_var = new_d.driver.variables.new()
			to_var.type = from_var.type
			to_var.name = from_var.name
			
			for i in range(len(from_var.targets)):
				target_bone = from_var.targets[i].bone_target
				new_target_bone = utils.flip_name(target_bone)
				if(to_var.type == 'SINGLE_PROP'):
					to_var.targets[i].id_type			= from_var.targets[i].id_type
				to_var.targets[i].id 				= from_var.targets[i].id
				to_var.targets[i].bone_target 		= new_target_bone
				data_path = from_var.targets[i].data_path
				if "pose.bones" in data_path:
					bone_name = data_path.split('pose.bones["')[1].split('"')[0]
					flipped_name = utils.flip_name(bone_name, only=False)
					data_path = data_path.replace(bone_name, flipped_name)
				to_var.targets[i].data_path 		= data_path
				to_var.targets[i].transform_type 	= from_var.targets[i].transform_type
				to_var.targets[i].transform_space 	= from_var.targets[i].transform_space

		new_d.driver.expression = expression

for p_bb in p_bb_bones:
	bb_name = p_bb.name.replace("P-BB", "BB")
	bb_bone = bones.get(bb_name)
	if not bb_bone:
		print("Warning: Could not find BB bone: %s" %bb_name)
		continue
	
	for a in bpy.data.actions:
		for c in a.fcurves:
			if(p_bb.name in c.data_path):
				if "location" not in c.data_path: continue
				c.data_path = c.data_path.replace(p_bb.name, bb_name)
				group = a.groups.get(bb_name)
				if(not group):
					group = a.groups.new(bb_name)
				c.group = group
	
	for c in p_bb.constraints:
		bb_constraint = bb_bone.constraints.get(c.name)
		if not bb_constraint:
			bb_constraint = bb_bone.constraints.new(c.type)
		if c.type=='ARMATURE':
			for t in c.targets:
				bb_constraint.targets.neW()
		utils.copy_attributes(c, bb_constraint, recursive=True)
		copy_drivers(armature, p_bb, bb_bone, c, bb_constraint)