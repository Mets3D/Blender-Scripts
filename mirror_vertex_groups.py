import bpy
import mathutils
from mathutils import Vector

# Todo: Currently strictly mirrors from one side to the other. Could do something smart to figure out which side should be mirrored to which side. Or just forget about removing weights idk.

side_dict = {
'l_' : 'r_',
'L_' : 'R_',
'.l' : '.r',
'.L' : '.R',
'_l' : '_r',
'_L' : '_R',
'-l' : '-r',
'-L' : '-R',
'left_' : 'right_',
'Left_' : 'Right_',
'_left' : '_right',
'_Left' : '_Right',
}

def flip_side_dict():
	global side_dict
	new_dict = {}
	for s in side_dict.keys():
		new_dict[side_dict[s]] = s
	side_dict = new_dict

# Finding vertex group to mirror weights into
def find_mirrored_group(obj, vg, allow_same=True, right_to_left=False, create=True):
	if(right_to_left):
		flip_side_dict()
	for s in side_dict.keys():
		if(s in vg.name):
			mirrored_name = vg.name.replace(s, side_dict[s])
			mirrored_vg = obj.vertex_groups.get(mirrored_name)
			if((not mirrored_vg) and create):
				return obj.vertex_groups.new(name=mirrored_name)
			else:
				return mirrored_vg
	return vg if allow_same else None

def mirror_selected_pose_bones(right_to_left=False):
	if(not bpy.context.selected_pose_bones): return

	vgroups = []
	for b in bpy.context.selected_pose_bones:
		vg = obj.vertex_groups.get(b.name)
		if(not vg): continue
		vgroups.append(vg)
	mirror_vertex_groups(vgroups, right_to_left)

def mirror_vertex_groups(vgroups=None, right_to_left=False):
	obj = bpy.context.object
	if(obj.type!='MESH'): return
	
	# Creating KDTree
	kd = mathutils.kdtree.KDTree(len(obj.data.vertices))

	for i, v in enumerate(obj.data.vertices):
		kd.insert(v.co, i)
	
	kd.balance()
	for vg in vgroups:
		print("Group: " + vg.name)
		if(not vg): continue
		vg_opp = find_mirrored_group(obj, vg, allow_same=True, right_to_left=right_to_left)
		print("Opposite group: " + vg_opp.name)
		
		for v in obj.data.vertices:
			# Flipping coordinates on X axis
			mirrored_co = Vector((v.co.x*-1, v.co.y, v.co.z))
			
			# Finding vertex closest to the flipped coordinates
			co, index, dist = kd.find(mirrored_co)
			
			#if(index == v.index): continue
			
			side = mirrored_co.x > 0 if right_to_left else mirrored_co.x < 0
			
			#if(side):
			if(True):
				try:
					# Removing old weights
					vg_opp.add(range(index, index+1), 0, 'REPLACE')
					# Adding new weights
					vg_opp.add(range(index, index+1), vg.weight(v.index), 'REPLACE')
				except:
					continue

obj = bpy.context.object
group_names = ['Triss_Masquerade+M-Sleeves1']
groups = [obj.vertex_groups.get(g) for g in group_names]
#mirror_vertex_groups(groups, True)
mirror_selected_pose_bones()