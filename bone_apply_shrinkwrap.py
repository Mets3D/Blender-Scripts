# Rigging the Sprite Fright faces will have a pretty wild workflow it seems:

# Create a feature-less helper mesh of the head, which will be weight painted to the main head bones and used as a Shrinkwrap target.
# Let's call this the Shrinkwrap Mesh.
# Face control bones will use Shrinkwrap constraints to attach themselves to this mesh.
# We want to make sure though, that such control bones' rest position is the same as their constrained rest position.
# To do this, we want to apply the Shrinkwrap constraints' effect to the rest positions of the metarig bones.

# Perhaps even the process of adding these Shrinkwrap constraints to the correct bones could be automated...


# In Edit mode
# For all selected bones
    # Disconnect this bone and remember its previous connected-ness status.
    # Find and save a list of other bones at the same location.

# Switch to Pose mode
# For all selected bones
    # Check if any of its intersecting bones have a Shrinkwrap constraint
    # If not, add the Shrinkwrap constraint. (bottom of the stack)
    # Snap all intersecting bones to this one's world position so they intersect again. (ie. the shrinkwrap affects everyone)

# Apply transforms of selected bones

# In Edit mode
# For all selected bones
    # Move their tail to their nearest child's head.

# For all selected bones
    # Restore connected-ness status.

import bpy

rig = bpy.context.object
shrinkwrap_object = bpy.data.objects['GEO-rex_head_shrinkwrap']
threshold = 0.001

# Remove any shrinkwrap constraints.
bpy.ops.object.mode_set(mode='POSE')
selected_pose_bones = bpy.context.selected_pose_bones
for pb in selected_pose_bones:
    for c in pb.constraints[:]:
        if c.type=='SHRINKWRAP':
            pb.constraints.remove(c)

# Organize bones with matching head locations into groups, to ensure that only one shrinkwrap 
# constraint will be added per group.
groups = {}
for pb in selected_pose_bones:
    group = [pb.name]
    for other_pb in selected_pose_bones:
        if pb == other_pb: continue
        if (pb.bone.head_local - other_pb.bone.head_local).length < threshold:
            group.append(other_pb.name)
            groups[other_pb.name] = group
    groups[pb.name] = group

# Add shrinkwrap constraints and keep track of which bones they were added to.
shrinkwrap_bones = []
for pb in selected_pose_bones:
    group = groups[pb.name]
    group_member_with_constraint = None # Prefer to add the shrinkwrap constraint to a group member that already has any constraints.
    group_has_shrinkwrap = False
    for group_pb in [rig.pose.bones.get(name) for name in group]:
        # if group_pb == pb: continue
        for c in group_pb.constraints:
            group_member_with_constraint = group_pb
            if c.type=='SHRINKWRAP':
                group_has_shrinkwrap = True
                break
    if group_has_shrinkwrap:
        continue
    constraint_owner = pb
    if group_member_with_constraint:
        constraint_owner = group_member_with_constraint
    shrinkwrap = constraint_owner.constraints.new(type='SHRINKWRAP')
    shrinkwrap.shrinkwrap_type = 'TARGET_PROJECT'
    shrinkwrap.target = shrinkwrap_object
    shrinkwrap.name = "Srhinkwrap " + pb.name
    shrinkwrap_bones.append(constraint_owner.name)


bpy.ops.object.mode_set(mode='EDIT')

# Save connected state of each bone.
connected = {}
parents = {}
for eb in bpy.context.selected_editable_bones:
    parents[eb.name] = eb.parent.name if eb.parent else ""
    connected[eb.name] = eb.use_connect
    eb.use_connect = False
    eb.parent = None

# Update pose mode now that shrinkwrap constraints have been added and use_connect set to False.
bpy.ops.object.mode_set(mode='POSE')
bpy.ops.object.mode_set(mode='EDIT')

zero_x_vectors = []
for sw_bone in [rig.data.edit_bones.get(name) for name in shrinkwrap_bones]:
    # Brute force search for edit bone head/tail vectors that intersect with this shrinkwrap bone's head,
    # and make them share a pointer. This way when we change sw_bone's head, all the other vectors will move along with it
    # since until we leave edit mode, they are the same vector.
    vectors = [sw_bone.head]
    for eb in bpy.context.selected_editable_bones:
        # Save vectors whose X should remain at 0.
        if abs(eb.head.x) < threshold:
            zero_x_vectors.append(eb.head)
        if abs(eb.tail.x) < threshold:
            zero_x_vectors.append(eb.tail)

        if eb==sw_bone: continue

        if (eb.head - sw_bone.head).length < threshold:
            eb.head = sw_bone.head
            vectors.append(eb.head)
            # print("Matched head of " + eb.name)
        if (eb.tail - sw_bone.head).length < threshold:
            eb.tail = sw_bone.head
            vectors.append(eb.tail)
            # print("Matched tail of " + eb.name)

    # Move sw_bone's head to where it is in pose mode
    pose_bone = rig.pose.bones.get(sw_bone.name)
    loc = pose_bone.matrix.to_translation()
    for v in vectors:
        v[0] = loc[0]
        v[1] = loc[1]
        v[2] = loc[2]

for zero_x_vec in zero_x_vectors:
    zero_x_vec[0] = 0.0

for eb in bpy.context.selected_editable_bones:
    eb.use_connect = connected[eb.name]
    eb.parent = rig.data.edit_bones.get(parents[eb.name])

bpy.ops.object.mode_set(mode='POSE')
