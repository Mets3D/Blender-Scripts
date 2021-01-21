# Script to copy over action slots from one metarig to another.

import bpy

rex_rig = bpy.data.objects['META-rex']
ellie_rig = bpy.data.objects['META-ellie']

# It is expected that a copy of one metarig's actions exist in the blend file, with the other character's name in it.
# (eg. RIG.Rex_Lips_Wide -> RIG.Ellie_Lips_Wide)
char_from = "Rex"
char_to = "Ellie"

for aslot in rex_rig.data.cloudrig_parameters.action_slots:
	new_slot = ellie_rig.data.cloudrig_parameters.action_slots.add()
	new_slot.action = bpy.data.actions[aslot.action.name.replace(char_from, char_to)]
	new_slot.is_corrective = aslot.is_corrective
	new_slot.corrective_type = aslot.corrective_type
	new_slot.frame_start = aslot.frame_start
	new_slot.frame_end = aslot.frame_end
	if aslot.trigger_action_a:
		new_slot.trigger_action_a = bpy.data.actions[aslot.trigger_action_a.name.replace(char_from, char_to)]
	if aslot.trigger_action_b:
		new_slot.trigger_action_b = bpy.data.actions[aslot.trigger_action_b.name.replace(char_from, char_to)]
	
	new_slot.target_space = aslot.target_space
	new_slot.transform_channel = aslot.transform_channel
	new_slot.subtarget = aslot.subtarget
	
	new_slot.trans_min = aslot.trans_min
	new_slot.trans_max = aslot.trans_max