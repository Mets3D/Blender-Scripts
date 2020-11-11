import bpy

rig = bpy.context.object
for b in rig.pose.bones:
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

# Layers
rig.data.layers = [i in [0, 1, 3] for i in range(32)]

# Generator params
rig.data.cloudrig_parameters.generate_test_action = False
rig.data.cloudrig_parameters.double_root = True
rig.data.rigify_force_widget_update = True