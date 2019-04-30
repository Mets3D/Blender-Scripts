bl_info = {
	"name": "Distance Weighted Weight Transfer",
	"description": "Smart Transfer Weights operator",
	"author": "Mets 3D",
	"version": (1, 0),
	"blender": (2, 80, 0),
	"location": "Space -> Smart Weight Transfer",
	"category": "Object"
}

import bpy
import mathutils
from mathutils import Vector
import math
from bpy.props import *

def build_weight_dict(obj, vgroups=None, mask_vgroup=None, bone_combine_dict=None):
	# Returns a dictionary that matches the vertex indicies of the object to a list of tuples containing the vertex group names that the vertex belongs to and the weight of the vertex in that group.
	# Optionally, if vgroups is passed, don't bother saving groups that aren't in vgroups.
	# Also optionally, bone_combine_dict can be specified if we want some bones to be merged into others, eg. passing in {'Toe_Main' : ['Toe1', 'Toe2', 'Toe3']} will combine the weights in the listed toe bones into Toe_Main. You would do this when transferring weights from a model of actual feet onto shoes.
	
	weight_dict = {}	# {vert index : [('vgroup_name', vgroup_value), ...], ...}
	
	if(vgroups==None):
		vgroups = obj.vertex_groups
	
	for v in obj.data.vertices:
		# TODO: instead of looking through all vgroups we should be able to get only the groups that this vert is assigned to via v.groups[0].group which gives the group id which we can use to get the group via Object.vertex_groups[id]
		# With this maybe it's useless altogether to save the weights into a dict? idk.
		# Although the reason we are doing it this way is because we wanted some bones to be considered the same as others. (eg. toe bones should be considered a single combined bone)
		for vg in vgroups:
			w = 0
			try:
				w = vg.weight(v.index)
			except:
				pass
			
			# Adding the weights from any sub-vertexgroups defined in bone_combine_dict
			if(vg.name in bone_combine_dict.keys()):
				for sub_vg_name in bone_combine_dict[vg.name]:
					sub_vg = obj.vertex_groups.get(sub_vg_name)
					if(sub_vg==None): continue
					try:
						w = w + sub_vg.weight(v.index)
					except RuntimeError:
						pass
			
			if(w==0): continue
			
			# Masking transfer influence
			if(mask_vgroup):
				try:
					multiplier = mask_vgroup.weight(v.index)
					w = w * multiplier
				except:
					pass
			
			# Create or append entry in the dict.
			if(v.index not in weight_dict):
				weight_dict[v.index] = [(vg.name, w)]
			else:
				weight_dict[v.index].append((vg.name, w))
	
	return weight_dict
			
def build_kdtree(obj):
	kd = mathutils.kdtree.KDTree(len(obj.data.vertices))
	for i, v in enumerate(obj.data.vertices):
		kd.insert(v.co, i)
	kd.balance()
	return kd

def transfer_weights_distance_weighted_avg(obj_from, obj_to, weights, max_verts=30, max_dist=10, dist_multiplier=1000, ):
	# This is a smart weight transfer algo.
	# The number of nearby verts which it searches for depends on how far the nearest vert is. (This is controlled by max_verts, max_dist and dist_multiplier)
	#	This means if a very close vert is found, it won't look for any more verts
	#	If the nearest vert is quite far away(or you set dist_multiplier very high), it will average the influences of quite a few verts
	# The averaging of the influences is also weighted by their distance.
	# This means that a vertex which is twice as far away will contribute to the final influence half as much.
	
	kd = build_kdtree(obj_from)
	
	for v in obj_to.data.vertices:
		weights_avg = {}
		
		# Finding singular nearest vertex
		nearest_co, nearest_idx, nearest_dist = kd.find(v.co)

		# Depending on how close the nearest vertex is, check more verts. (If the nearest vertex is very very close, no other verts will be checked)
		number_of_source_verts = 1 + round( pow( (nearest_dist * dist_multiplier), 2 ) )
		number_of_source_verts = max_verts if number_of_source_verts > max_verts else number_of_source_verts
		
		#print("# of verts: " + str(number_of_source_verts)) 
		source_verts = [((nearest_idx, nearest_dist))]
		source_verts = []	# List of vert index-distance tuples that we'll be copying the weights from.
		
		for(co, index, dist) in kd.find_n(v.co, number_of_source_verts):
			if( (index not in weights) or (dist > max_dist) ):	# If the found vert doesn't have any weights OR is too far away
				continue
			source_verts.append((index, dist))
		
		# Sort valid verts by distance (least to most distance)
		source_verts.sort(key=lambda tup: tup[1])
		
		# Iterating through the verts, from closest to furthest.
		for i in range(0, len(source_verts)):
			vert = source_verts[i]
			# The closest vert's weights are multiplied by the farthest vert's distance, and vice versa. The 2nd closest will use the 2nd farthest, etc.
			# The magnitude of the distance vectors doesn't matter because at the end they will be normalized anyways.
			pair_distance = source_verts[-i-1][1]
			for vg_name, vg_weight in weights[vert[0]]:
				new_weight = vg_weight * pair_distance
				if(vg_name not in weights_avg):
					weights_avg[vg_name] = new_weight
				else:
					weights_avg[vg_name] = weights_avg[vg_name] + new_weight
		
		# The sum is used to normalize the weights. This is important because otherwise the values would depend on object scale, and in the case of very small or very large objects, stuff could get culled.
		weights_sum = sum(weights_avg.values())
		
		# Assigning final weights to the vertex groups.
		for vg_avg in weights_avg.keys():
			target_vg = obj_to.vertex_groups.get(vg_avg)
			if(target_vg == None):
				target_vg = obj_to.vertex_groups.new(name=vg_avg)
			target_vg.add([v.index], weights_avg[vg_avg]/weights_sum, 'REPLACE')
	
	bpy.ops.object.mode_set(mode='WEIGHT_PAINT')

bone_dict = {
	'pelvis' : ['Gens_Root', 'Vagoo_Root', 'Anus_Root', 'Gens_Mid', 'Butt_Mid', 
	'Vagoo_Top', 'Vagoo.L', 'Vagoo.R', 'Vagoo_Bottom', 
	'Anus_Top', 'Anus_Bottom', 
	'Anus.L.004', 'Anus.L.003', 'Anus.L.002', 'Anus.L.001', 'Anus.L', 
	'Anus.R', 'Anus.R.001', 'Anus.R.002', 'Anus.R.003', 'Anus.R.004'],

	'Butt.L' : ['Butt_Top.L', 'Butt_Inner.L', 'Butt_Bot.L', 'Butt_Outer.L'],

	'Butt.R' : ['Butt_Top.R', 'Butt_Outer.R', 'Butt_Bot.R', 'Butt_Inner.R'],

	'l_boob' : ['Breast_Top.L', 'Breast_Outer.L', 'Breast_Inner.L', 'Breast_Bot.L', 'Breast_Nipple.L'],

	'r_boob' : ['Breast_Top.R', 'Breast_Inner.R', 'Breast_Outer.R', 'Breast_Bot.R'],

	'l_toe' : ['Toe_Thumb1.L', 'Toe_Thumb2.L', 'Toe_Index1.L', 'Toe_Index2.L', 'Toe_Middle1.L', 'Toe_Middle2.L', 'Toe_Ring1.L', 'Toe_Ring2.L', 'Toe_Pinky1.L', 'Toe_Pinky2.L'],

	'r_toe' : ['Toe_Thumb1.R', 'Toe_Thumb2.R', 'Toe_Index1.R', 'Toe_Index2.R', 'Toe_Middle1.R', 'Toe_Middle2.R', 'Toe_Ring1.R', 'Toe_Ring2.R', 'Toe_Pinky1.R', 'Toe_Pinky2.R'],

	'l_hand' : ['l_thumb_roll', 'l_pinky0', 'l_index_knuckleRoll', 'l_middle_knuckleRoll', 'l_ring_knuckleRoll'],

	'r_hand' : ['r_thumb_roll', 'r_pinky0', 'r_index_knuckleRoll', 'r_middle_knuckleRoll', 'r_ring_knuckleRoll'],
}

bone_dict_string = """{
	'pelvis' : ['Gens_Root', 'Vagoo_Root', 'Anus_Root', 'Gens_Mid', 'Butt_Mid', 
	'Vagoo_Top', 'Vagoo.L', 'Vagoo.R', 'Vagoo_Bottom', 
	'Anus_Top', 'Anus_Bottom', 
	'Anus.L.004', 'Anus.L.003', 'Anus.L.002', 'Anus.L.001', 'Anus.L', 
	'Anus.R', 'Anus.R.001', 'Anus.R.002', 'Anus.R.003', 'Anus.R.004'],

	'Butt.L' : ['Butt_Top.L', 'Butt_Inner.L', 'Butt_Bot.L', 'Butt_Outer.L'],

	'Butt.R' : ['Butt_Top.R', 'Butt_Outer.R', 'Butt_Bot.R', 'Butt_Inner.R'],

	'l_boob' : ['Breast_Top.L', 'Breast_Outer.L', 'Breast_Inner.L', 'Breast_Bot.L', 'Breast_Nipple.L'],

	'r_boob' : ['Breast_Top.R', 'Breast_Inner.R', 'Breast_Outer.R', 'Breast_Bot.R'],

	'l_toe' : ['Toe_Thumb1.L', 'Toe_Thumb2.L', 'Toe_Index1.L', 'Toe_Index2.L', 'Toe_Middle1.L', 'Toe_Middle2.L', 'Toe_Ring1.L', 'Toe_Ring2.L', 'Toe_Pinky1.L', 'Toe_Pinky2.L'],

	'r_toe' : ['Toe_Thumb1.R', 'Toe_Thumb2.R', 'Toe_Index1.R', 'Toe_Index2.R', 'Toe_Middle1.R', 'Toe_Middle2.R', 'Toe_Ring1.R', 'Toe_Ring2.R', 'Toe_Pinky1.R', 'Toe_Pinky2.R'],

	'l_hand' : ['l_thumb_roll', 'l_pinky0', 'l_index_knuckleRoll', 'l_middle_knuckleRoll', 'l_ring_knuckleRoll'],

	'r_hand' : ['r_thumb_roll', 'r_pinky0', 'r_index_knuckleRoll', 'r_middle_knuckleRoll', 'r_ring_knuckleRoll'],
}"""

vgroup_names = ['head', 'neck', 'pelvis', 'r_shoulder', 'l_shoulder', 'torso3', 'l_boob', 'r_boob', 'torso2', 'torso', 'r_foot', 'r_toe', 'r_shin', 'Butt.R', 'r_thigh', 'Adjust_Thigh_Front.R', 'Adjust_Thigh_Side.R', 'l_foot', 'l_toe', 'l_shin', 'Butt.L', 'l_thigh', 'Adjust_Thigh_Front.L', 'Adjust_Thigh_Side.L', 'r_bicep', 'Adjust_Elbow_Back.R', 'r_elbowRoll', 'r_hand', 'l_bicep', 'Adjust_Elbow_Back.L', 'l_elbowRoll', 'l_hand', 'r_bicep2', 'r_shoulderRoll', 'l_shoulderRoll', 'l_bicep2', 'l_forearmRoll1', 'l_forearmRoll2', 'l_handRoll', 'l_kneeRoll', 'r_forearmRoll1', 'r_forearmRoll2', 'r_handRoll', 'r_kneeRoll', 'Twist_Leg_1.R', 'Twist_Leg_1.L']

class SmartWeightTransferOperator(bpy.types.Operator):
	"""Transfer weights from active to selected objects based on weighted vert distances."""
	bl_idname = "object.smart_weight_transfer"
	bl_label = "Smart Transfer Weights"
	bl_options = {'REGISTER', 'UNDO'}
	
	opt_wipe_originals: BoolProperty(name="Wipe originals", 
		default=True, 
		description="Wipe original vertex groups before transferring. Recommended.")
	
	opt_max_verts: IntProperty(name="Max considered verts", 
		default=5, 
		description="Higher = more verts allowed to be considered. Higher numbers Allow for but don't guarantee smoother weights. Setting this to 1 will give same result as normal transfer weights operator. Should increase this if your mesh is very high poly or decrease for very low poly.")
	
	opt_max_dist: FloatProperty(name="Max distance", 
		default=1000, 
		description="Higher numbers allow weights from further away verts to be considered.")
	
	opt_dist_multiplier: FloatProperty(name="Smoothness", 
		default=1000, 
		description="Higher values will consider more verts based on the distance of the closest vert. Has less effect on verts that are close to the source mesh. If the source and the target mesh are exactly the same, this has no effect. Increasing this after a certain point will have no effect since the maximum allowed verts will be reached before the maximum distance.")
	
	def get_vgroups(self, context):
		items = [('None', 'None', 'None')]
		for vg in context.object.vertex_groups:
			items.append((vg.name, vg.name, vg.name))
		return items
	
	opt_mask_vgroup: EnumProperty(name="Operator Mask",
		items=get_vgroups,
		description="The operator's effect will be masked by this vertex group, unless 'None'.")
	
	opt_bone_combine_dict: StringProperty(name='Combine Dict',
		description="If you want some vertgroups to be considered part of others, you can enter them here in the following format: {'Toe_Main.L' : ['Toe1.L', 'Toe2.L'], 'Toe_Main.R' : ['Toe1.R', 'Toe2.R']}. It  needs to evaluate to a valid Python dictionary where the keys are strings and values are lists of strings.",
		default=bone_dict_string
	)
	
	def execute(self, context):
		bone_dict = eval(self.opt_bone_combine_dict)
	
		source_obj = bpy.context.object
		for o in bpy.context.selected_objects:
			if(o==source_obj or o.type!='MESH'): continue
			bpy.ops.object.mode_set(mode='OBJECT')
			bpy.ops.object.select_all(action='DESELECT')
		
			vgroups = []
			# Saving vertex groups of selected pose bones (Assuming user is in weight paint mode, so the active object is a mesh but there are still selected pose bones in a pose mode armature)
			if(bpy.context.selected_pose_bones):
				vgroups = [source_obj.vertex_groups.get(b.name) for b in bpy.context.selected_pose_bones]
			
			# If no bones are selected, use all.
			if(vgroups==None):
				vgroups = o.vertex_groups
			
			# Using hard coded vertex group names. 	
			# TODO delet this
			# and delet bone_dict
			# and delet vgroups list
			# maybe. Or meaybe just leave them. Or maybe implement them as a feature. idk!
			vgroups = [source_obj.vertex_groups.get(vgn) for vgn in vgroup_names]
			
			# Cleaning up vgroups
			vgroups = [vg for vg in vgroups if vg != None]
			
			# Delete the vertex groups from the destination mesh first...
			if(self.opt_wipe_originals):
				for vg in vgroups:
					if(vg.name in o.vertex_groups):
						o.vertex_groups.remove(o.vertex_groups.get(vg.name))
			
			mask_vgroup = o.vertex_groups.get(self.opt_mask_vgroup)
			
			weights = build_weight_dict(source_obj, vgroups, mask_vgroup, bone_dict)
			
			transfer_weights_distance_weighted_avg(source_obj, o, weights, self.opt_max_verts, self.opt_max_dist, self.opt_dist_multiplier)
			
			bpy.context.view_layer.objects.active = o
			bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
		
		return { 'FINISHED' }

def register():
	from bpy.utils import register_class
	register_class(SmartWeightTransferOperator)

def unregister():
	from bpy.utils import unregister_class
	unregister_class(SmartWeightTransferOperator)

register()