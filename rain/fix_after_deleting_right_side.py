import bpy
from mets_tools.utils import *

# For fixing some constraints after deleting right side bones (and hence breaking references to those bones) and then symmetrizing.

pbones = bpy.context.object.pose.bones
for b in pbones:
	if len(b.constraints)==0:
		b.bone.hide = True
		
	for c in b.constraints:
		if not c.is_valid:
			b.bone.hide = False
			if c.type == 'ARMATURE':
				# For broken Armature constraints, we assume that a subtarget is invalid, and that this missing target is supposed to be the opposite of the one before it.
				for i, t in enumerate(c.targets):
					if t.subtarget == "" and i  > 0:
						previous = c.targets[i-1].subtarget
						flip = flip_name(previous)
						if flip != previous and flip != "":
							t.subtarget = flip
							continue
			elif hasattr(c, "subtarget") and c.subtarget == "":
				# For any other type of constraint, we also assume that the subtarget is empty, and we assume that there is a constraint with the opposite name from this one. We want to grab the opposite subtarget.
				flip_const = b.constraints.get(flip_name(c.name))
				if flip_const and flip_const != c:
					unflip_subtarget = flip_name(flip_const.subtarget)
					if unflip_subtarget != "" and unflip_subtarget != flip_const.subtarget:
						c.subtarget = unflip_subtarget
						continue
			
			# If any constraint gets here, let me know via console.
			print("Constraint could not be auto-fixed on bone: " + b.name)
		else:
			b.bone.hide = True