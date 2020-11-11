import bpy

for b in bpy.context.object.pose.bones:
    # Arms and Legs
    if b.rigify_type in ['cloud_limb', 'cloud_leg']:
        b.rigify_parameters.CR_limb_auto_hose_type = 'ELBOW_IN'
        b.rigify_parameters.CR_limb_double_ik = True
        b.rigify_parameters.CR_BG_LAYERS_ik_child_controls = [i==16 for i in range(32)]
        # Just the Legs
        if b.rigify_type=='cloud_leg':
            b.rigify_parameters.CR_leg_heel_bone = b.name.replace("Thigh", "HeelPivot")
    
    # Shoulder
    if 'UpperArm' in b.name:
        assert b.bone.use_connect == False, "Disconnect the shoulders."
    if b.rigify_type == 'cloud_shoulder':
        b.rigify_parameters.CR_chain_tip_control = False
        b.rigify_parameters.CR_fk_chain_parent_candidates = True
        # Maybe this should use Parent to Deform?
    
    # Spine
    if b.rigify_type == 'cloud_spine':
        b.rigify_parameters.CR_fk_chain_parent_candidates = True

    # Head
    if b.name=='Head':
        b.rigify_parameters.CR_fk_chain_parent_candidates = True
    
    # (TODO)
    # Layers
    # Generator params
