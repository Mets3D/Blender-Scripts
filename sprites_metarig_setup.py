import bpy

metarig = bpy.context.object
rig = metarig.data.rigify_target_rig

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

    # Neck
    if b.name=='Neck':
        bpy.ops.object.mode_set(mode='EDIT')
        eb = metarig.data.edit_bones.get(b.name)
        eb.use_connect = False
        bpy.ops.object.mode_set(mode='OBJECT')

    # Teeth
    if 'Tooth' in b.name:
        b.bone.layers = [i==20 for i in range(32)]
    if b.name.startswith('Gum_'):
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