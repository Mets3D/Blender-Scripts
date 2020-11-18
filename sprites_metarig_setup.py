import bpy

rigify_params = bpy.types.PropertyGroup.bl_rna_get_subclass_py("RigifyParameters")

metarig = bpy.context.object
rig = metarig.data.rigify_target_rig

rig_type_hierarchy = {
	'cloud_base' : {
		'cloud_chain' : {
			'cloud_face_chain' : {
				'cloud_eyelid' : {}
			},
			'cloud_fk_chain' : {
				'cloud_spine' : {},
				'cloud_shoulder' : {},
				'cloud_ik_chain' : {
					'cloud_limb' : {
						'cloud_leg' : {}
					}
				},
				'cloud_physics_chain' : {}
			}
		},
		'cloud_curve' : {
			'cloud_spline_ik' : {}
		},
		'cloud_aim' : {},
		'cloud_copy' : {},
		'cloud_tweak' : {}
	}
}

def get_rig_type_hierarchy(search, parent_list=[], hierarchy=rig_type_hierarchy):
	"""Build a list consisting of the parent rig types and the rig type itself."""
	for key in hierarchy.keys():
		parent_list.append(key)
		if key==search:
			return parent_list
		found = get_rig_type_hierarchy(search, parent_list, hierarchy[key])
		if not found:
			parent_list.remove(key)
		else:
			return found

def match_param_to_type(type_name, param_name):
	"""Determine whether a rigify parameter belongs on a given rig type."""
	matching_types = get_rig_type_hierarchy(type_name, parent_list=[], hierarchy=rig_type_hierarchy)
	param_name = param_name.replace("CR_", "")
	for t in matching_types:
		if param_name.startswith(t.replace("cloud_", "")):
			return True
	return False

# Layers
metarig.data.layers = [i in [0, 1, 3] for i in range(32)]

# Generator params
metarig.data.cloudrig_parameters.generate_test_action = False
metarig.data.cloudrig_parameters.double_root = True
metarig.data.rigify_force_widget_update = True

# Rigify Layer names
for i in range(32):
	if len(metarig.data.rigify_layers) < i:
		metarig.data.rigify_layers.add()
	l = metarig.data.rigify_layers[i]
	l.selset = False
	if i == 0:
		l.name = "IK"
		l.row = 1
	if i == 1:
		l.name = "FK"
		l.row = 2
	if i == 2:
		l.name = "Stretch"
		l.row = 3
	if i == 3:
		l.name = "Face"
		l.row = 4
	if i == 4:
		l.name = "Mouth"
		l.row = 5
	if i == 5:
		l.name = "Fingers"
		l.row = 6
	if i == 6:
		l.name = "Hair"
		l.row = 7
	if i == 7:
		l.name = "Clothes"
		l.row = 8
	if i == 8:
		l.name = "Tracking"
		l.row = 30

	if i == 16:
		l.name = "IK Secondary"
		l.row = 1
	if i == 17:
		l.name = "FK Secondary"
		l.row = 2
	if i == 18:
		l.name = "Deform"
		l.row = 3
	if i == 19:
		l.name = "Face Secondary"
		l.row = 4
	if i == 20:
		l.name = "Teeth"
		l.row = 5
	if i == 21:
		l.name = "Fingers Stretch"
		l.row = 6
	if i == 22:
		l.name = "Hair Stretch"
		l.row = 7
		
	if i == 28:
		l.name = "$Unused"
		l.row = 32
	if i == 29:
		l.name = "$DEF"
		l.row = 32
	if i == 30:
		l.name = "$MCH"
		l.row = 32
	if i == 31:
		l.name = "$ORG"
		l.row = 32

defaultless = []
for b in metarig.pose.bones:
	# Arms and Legs
	if b.rigify_type in ['cloud_limb', 'cloud_leg']:
		b.rigify_parameters.CR_limb_auto_hose_type = 'ELBOW_IN'
		b.rigify_parameters.CR_limb_double_ik = True
		b.rigify_parameters.CR_BG_LAYERS_ik_child_controls = [i==16 for i in range(32)]
		b.rigify_parameters.CR_fk_chain_test_animation_generate = True
		b.rigify_parameters.CR_fk_chain_test_animation_rotation_range[0] = -90
		b.rigify_parameters.CR_fk_chain_test_animation_rotation_range[1] = 90
		b.rigify_parameters.CR_fk_chain_test_animation_axes[1] = False
		# Just the Legs
		if b.rigify_type=='cloud_leg':
			b.rigify_parameters.CR_fk_chain_parent_candidates = True
			b.rigify_parameters.CR_leg_heel_bone = b.name.replace("Thigh", "HeelPivot")

	# Shoulder
	if 'UpperArm' in b.name:
		assert b.bone.use_connect == False, "Disconnect the shoulders."
	if b.rigify_type == 'cloud_shoulder':
		b.rigify_parameters.CR_chain_tip_control = False
		b.rigify_parameters.CR_fk_chain_parent_candidates = True
		b.rigify_parameters.CR_fk_chain_test_animation_generate = True
		b.rigify_parameters.CR_fk_chain_test_animation_rotation_range[0] = -45
		b.rigify_parameters.CR_fk_chain_test_animation_rotation_range[1] = 45
		b.rigify_parameters.CR_fk_chain_test_animation_axes[2] = False
		# Maybe this should use Parent to Deform?

	# Spine
	if b.rigify_type == 'cloud_spine':
		b.rigify_parameters.CR_fk_chain_parent_candidates = True
		b.rigify_parameters.CR_fk_chain_test_animation_generate = True
		b.rigify_parameters.CR_fk_chain_test_animation_rotation_range[0] = -110
		b.rigify_parameters.CR_fk_chain_test_animation_rotation_range[1] = 110

		b.rigify_parameters.CR_chain_tip_control = True
		b.rigify_parameters.CR_chain_bbone_density = 0
		b.rigify_parameters.CR_chain_unlock_deform = True
		b.rigify_parameters.CR_BG_LAYERS_deform_controls = [i==2 for i in range(32)]
		b.rigify_parameters.CR_BG_LAYERS_stretch_controls = [i==28 for i in range(32)]
		b.rigify_parameters.CR_BG_LAYERS_spine_ik_secondary = [i==28 for i in range(32)]

	# Head
	if b.name=='Head':
		b.rigify_parameters.CR_fk_chain_test_animation_generate = True
		b.rigify_parameters.CR_fk_chain_test_animation_rotation_range[0] = -90
		b.rigify_parameters.CR_fk_chain_test_animation_rotation_range[1] = 90
		b.rigify_parameters.CR_fk_chain_test_animation_axes[2] = False
		b.rigify_parameters.CR_fk_chain_parent_candidates = True

	# Fingers
	if 'Finger' in b.name and b.rigify_type!='':
		b.rigify_parameters.CR_fk_chain_test_animation_generate = True
		b.rigify_parameters.CR_fk_chain_test_animation_rotation_range[0] = -10
		b.rigify_parameters.CR_fk_chain_test_animation_rotation_range[1] = 130
		b.rigify_parameters.CR_fk_chain_test_animation_axes[1] = False
		b.rigify_parameters.CR_fk_chain_test_animation_axes[2] = False

	# Teeth
	if 'Tooth' in b.name:
		b.bone.layers = [i==20 for i in range(32)]
	if b.name.startswith('Gum_') and 'rigify_type' in b:
		b.rigify_parameters.CR_chain_bbone_density = 0
		b.rigify_parameters.CR_chain_unlock_deform = True
		b.rigify_parameters.CR_BG_LAYERS_deform_controls = [i==2 for i in range(32)]
		b.rigify_parameters.CR_BG_LAYERS_stretch_controls = [i==28 for i in range(32)]

	# Custom Properties
	if 'Properties_Character_' in b.name:
		for key in b.keys():
			value = b[key]
			if type(value) in [float, int]:
				# Make library overridable
				b.property_overridable_library_set(f'["{key}"]', True)

			if key.startswith("CR_"):
				print(f"Rigify Parameter is custom property: {b.name} -> {key}")

	# Rigify Parameters: Nuke all if no type assigned.
	if b.rigify_type=='' and 'rigify_type' in b.keys():
		del b['rigify_type']
		if 'rigify_parameters' in b.keys():
			print(f"Deleting Rigify Parameters with no rig type: {b.name}")
			del b['rigify_parameters']


	# Rigify Parameters
	for key in b.rigify_parameters.keys():
		if b.rigify_type=='':
			print("Why does this bone still have rigify parameters when it has no rigify type: " + b.name)
			continue
		value = b.rigify_parameters[key]
		if hasattr(rigify_params, key):
			if 'BG' not in key and not match_param_to_type(b.rigify_type, key):
				print(f"Parameter didn't belong on this rig type: {b.name} -> {key} ({b.rigify_type})")
				del b.rigify_parameters[key]
				continue
			definition = getattr(rigify_params, key)
			default_value = None # Covers PointerProperties
			if 'default' in definition[1]:
				default_value = definition[1]['default']
			else:
				if type(value) == bool:
					default_value = False
				elif type(value) == int:
					default_value = 0
				elif type(value) == float:
					default_value == 1.0
				elif type(value) == str:
					default_value == ""
				elif key not in defaultless:
					defaultless.append(key)
			if value == default_value:
				print(f"Set value matched default value: {b.name} -> {key} ({value})")
				del b.rigify_parameters[key]
		else:
			print(f"Outdated Rigify Parameter: {b.name} -> {key}")
			del b.rigify_parameters[key]
	
	# Neck
	# if b.name=='Neck':
	#	 bpy.ops.object.mode_set(mode='EDIT')
	#	 eb = metarig.data.edit_bones.get(b.name)
	#	 eb.use_connect = False
	#	 bpy.ops.object.mode_set(mode='OBJECT')

for key in defaultless:
	print("Couldn't determine a default value for Rigify Parameter: " + key)

print("")