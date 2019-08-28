import bpy

# The general workflow we want to achieve, is to be able to sculpt a single shape in a shape key, 
# and then be able to split that shape up into multiple shape keys, masked by different vertex groups,
# and their value controlled by different bones (using drivers, which are created manually)

# We are relying on drivers not getting deleted when shape keys get deleted, so let's hope that's not a bug and never gets changed.

def normalize_vgroups(o, vgroups):
	""" Normalize a set of vertex groups in isolation """
	""" Used for creating mask vertex groups for splitting shape keys """
	for v in o.data.vertices:
		# Find sum of weights in specified vgroups
		# set weight to original/sum
		sum_weights = 0
		for vg in vgroups:
			w = 0
			try:
				sum_weights += vg.weight(v.index)
			except:
				pass
		for vg in vgroups:
			try:
				vg.add([v.index], vg.weight(v.index)/sum_weights, 'REPLACE')
			except:
				pass

def split_shapekey(o, source_name, split_names):
	""" Make copies of source shape key, rename them to target names, and assign a mask vertex group based on the naming convention: "SK:TargetName". """
	""" The use case is when we want to blend into a shape key using multiple masks. """
	
	# TODO: We will use this to split left/right halves as well, I suppose.
	# TODO: This fails when the source shape key has a keyframe on it that forces its value to be not 1.

	shape_keys = o.data.shape_keys.key_blocks
	# Ensure source shape key exists and set it to 1. (Let it stay on 1 after the operation is complete, since it will be disabled)
	source_sk = shape_keys.get(source_name)
	assert source_sk, "Error: Source shape key does not exist: " + source_name
	source_sk.value = 1

	# For performance we have to turn off subsurf (otherwise changing shape key order takes for ever)
	org_levels = None
	subsurf_mod = None
	for m in o.modifiers:
		if(m.type=='SUBSURF'):
			subsurf_mod = m
			org_levels = m.levels
			m.levels = 0

	# Save active shape key
	active_sk_name = o.active_shape_key.name

	# Disable all shape keys and save their states
	sk_dict = {}
	for sk in shape_keys:
		sk_dict[sk.name] = sk.mute
		sk.mute = True
	
	# Enable the source shape key
	source_sk.mute = False
	
	# Create copies
	for name in split_names:
		# If already exists, delete it
		index = None
		if(name in shape_keys):
			index = shape_keys.find(name)
			o.shape_key_remove(shape_keys[name])

		new_sk = o.shape_key_add(name=name, from_mix=True)
		vg = o.vertex_groups.get("SK:"+name)
		if(vg):
			new_sk.vertex_group = vg.name
		new_sk.mute=True

		# Restore shape key order
		o.active_shape_key_index = len(shape_keys) -1
		for i in range(index, len(shape_keys)-1):
			bpy.ops.object.shape_key_move(type='UP')
	
	# Restore shape key mute states
	for sk in shape_keys:
		sk.mute = sk_dict[sk.name]
	
	# Restore subsurf level
	if(subsurf_mod):
		subsurf_mod.levels = org_levels
	
	# Restore active shape key
	o.active_shape_key_index = shape_keys.find(active_sk_name)

o = bpy.context.object

vgroup_names = [
	"SK_FingerBends_Index.L",
	"SK_FingerBends_Middle.L",
	"SK_FingerBends_Ring.L",
	"SK_FingerBends_Pinky.L"
]

vgroups = [vg for vg in o.vertex_groups if vg.name in vgroup_names]

normalize_vgroups(o, vgroups)

finger_bends = [
	"Finger_Index1.L",
	"Finger_Middle1.L",
	"Finger_Ring1.L",
	"Finger_Pinky1.L",
]

split_shapekey(o, "FingerBends", finger_bends)