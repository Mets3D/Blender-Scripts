import bpy

# Expects WItcher3 skeleton to be selected, and MetsRig to be active.
# Expects Witcher3 skeleton to be named "Witcher3_Skeleton_Charname".

def combine_armatures(armatures, main_armature, face_to_char=False):
	# For combining Witcher 3 Skeletons into MetsRig.
	# Alternatively, for combining Face skeletons into Character skeletons.
	
	# Get the character name
	# Save the face bones' locations in said face bones' custom properties in the main armature.
	# Find non-duplicate bones(hair, clothes).
	# Create copies of the non-duplicate bones in the main armature(name, head, tail, parent)
	# Re-parent the child meshes and change their armature modifiers' target.
	
	bpy.ops.object.mode_set(mode='OBJECT')
	bpy.ops.object.select_all(action='DESELECT')
	
	face_bones = [
		"nose", 
		"upper_lip", 
		"right_nose1", 
		"right_eyebrow1", 
		"left_eyebrow1", 
		"nose_base", 
		"chin", 
		"lowwer_lip", 
		"lowwer_left_lip", 
		"upper_left_lip", 
		"upper_right_lip", 
		"right_nose2", 
		"left_nose2", 
		"right_nose3", 
		"lowwer_right_lip", 
		"left_forehead", 
		"right_forehead", 
		"left_temple", 
		"left_eyebrow3", 
		"left_eyebrow2", 
		"ears", 
		"left_chick4", 
		"left_chick3", 
		"left_mouth1", 
		"left_mouth2", 
		"left_mouth_fold1", 
		"left_mouth4", 
		"left_nose1", 
		"upper_left_eyelid_fold", 
		"left_chick2", 
		"left_mouth_fold3", 
		"left_mouth_fold4", 
		"left_chick1", 
		"left_mouth_fold2", 
		"left_mouth3", 
		"left_corner_lip1", 
		"left_corner_lip2", 
		"lowwer_left_eyelid_fold", 
		"left_nose3", 
		"lowwer_left_eyelid1", 
		"upper_left_eyelid1", 
		"upper_left_eyelid2", 
		"upper_left_eyelid3", 
		"lowwer_left_eyelid2", 
		"lowwer_left_eyelid3", 
		"right_temple", 
		"right_eyebrow3", 
		"right_eyebrow2", 
		"right_chick4", 
		"right_chick3", 
		"right_mouth1", 
		"right_mouth2", 
		"right_mouth_fold1", 
		"right_mouth4", 
		"upper_right_eyelid_fold", 
		"right_chick2", 
		"right_mouth_fold3", 
		"right_mouth_fold4", 
		"right_chick1", 
		"right_mouth_fold2", 
		"right_mouth3", 
		"right_corner_lip1", 
		"right_corner_lip2", 
		"lowwer_right_eyelid_fold", 
		"lowwer_right_eyelid1", 
		"upper_right_eyelid1", 
		"upper_right_eyelid2", 
		"upper_right_eyelid3", 
		"lowwer_right_eyelid2", 
		"lowwer_right_eyelid3", 
		"thyroid",
		"left_eye",
		"right_eye",
		"upper_left_eyelash",
		"upper_right_eyelash",
		"tongue1",
		"right_tongue_side",
		"tongue2",
		"left_tongue_side"
	]
	
	face_bone_dependents = {
		'left_eye' : ['Eye_LookAt.L'],
		'right_eye' : ['Eye_LookAt.R']
	}
	
	for a in armatures:
		# moving "left" and "right" to the beginning of the bone name, rather than the middle.
		# This way Blender will recognize that these bones are opposites of each other.
		for b in a.pose.bones:
			if('left_' in b.name):
				new_name = b.name.replace("left_", "")
				new_name = "left_" + new_name
				b.name = new_name
			elif('right_' in b.name):
				new_name = b.name.replace("right_", "")
				new_name = "right_" + new_name
				b.name = new_name

		if(a.type != 'ARMATURE'):
			continue
		if(a == main_armature):
			continue
		
		# Getting the character name
		char_name = ""
		if(face_to_char):
			assert "Witcher3_Skeleton_" in main_armature.name, "Expected target armature name to contain the string 'Witcher3_Skeleton_'. But it doesn't: " + main_armature.name
			char_name = main_armature.name.replace("Witcher3_Skeleton_", "")
		else:
			assert "Witcher3_Skeleton_" in a.name, "Expected armature name to contain the string 'Witcher3_Skeleton_'. But it doesn't: " + a.name
			char_name = a.name.replace("Witcher3_Skeleton_", "")
		if(char_name == ''): continue
		print("Character name: " + char_name)

		bpy.context.view_layer.objects.active = a
		bpy.ops.object.mode_set(mode='EDIT')	# We need the head coords from edit_bones.
		
		# Deleting "Bone" bone (TODO: make sure this works and is fine)
		shit = a.data.edit_bones.get('Bone')
		if(shit):
			a.data.edit_bones.remove(shit)
		
		# Saving face bones location into custom properties on the main armature's bones...
		for fb in face_bones:
			bone = a.data.edit_bones.get(fb)
			if(bone==None): continue
			main_arm_pbone = main_armature.pose.bones.get(fb)
			if(not main_arm_pbone): continue
			main_arm_pbone[fb+"_"+char_name] = bone.head
			# Doing same for dependent bones - TODO make sure this works.
			if(fb in face_bone_dependents.keys()):
				for d in face_bone_depentents[fb]:
					main_armature.pose.bones[d][d+"_"+char_name] = bone.head
		
		# Finding bones that exist in the main armature, and saving the parent of those that do not.
		duplicates = []
		parents = {}
		for b in a.data.bones:
			if(b.name in main_armature.data.bones):
				duplicates.append(b.name)
			else:
				if(b.parent):
					parents[b.name] = b.parent.name
		
		# Deleting the duplicate bones
		bpy.context.view_layer.objects.active = a
		bpy.ops.object.mode_set(mode='EDIT')
		for eb in duplicates:
			a.data.edit_bones.remove(a.data.edit_bones.get(eb))
		bpy.ops.object.mode_set(mode='OBJECT')
		
		# Parenting child meshes of this armature to main armature (They need to be enabled and visible since we use bpy.ops - could probably not use bpy.ops)
		for o in a.children:
			o.select_set(True)
			o.modifiers.clear()
		main_armature.select_set(True)
		bpy.context.view_layer.objects.active = main_armature
		bpy.ops.object.parent_set(type='ARMATURE')
		
		# Joining this armature with the main armature
		bpy.ops.object.select_all(action='DESELECT')
		a.select_set(True)
		main_armature.select_set(True)
		bpy.context.view_layer.objects.active = main_armature
		bpy.ops.object.join()
		
		# Parenting the bones back
		bpy.context.view_layer.objects.active = main_armature
		bpy.ops.object.mode_set(mode='EDIT')
		for b in parents.keys():
			eb = main_armature.data.edit_bones[b]
			parent = parents.get(b)
			if(eb.parent == None and parent != None):
				eb.parent = main_armature.data.edit_bones.get(parent)
	return main_armature

combine_armatures(bpy.context.selected_objects, bpy.context.object, True)