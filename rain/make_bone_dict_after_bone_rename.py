import bpy
from pprint import pprint

old_armature = bpy.data.objects['RIG-Rain.001']
new_armature = bpy.data.objects['RIG-Rain']

def get_bone_index(armature, bone_name):
	for i, b in enumerate(armature.pose.bones):
		if b.name==bone_name: return i
	
bone_dict = {}

for b in old_armature.pose.bones:
	index = get_bone_index(old_armature, b.name)
	new_bone_name = new_armature.pose.bones[index].name
	if b.name != new_bone_name:
		bone_dict[b.name] = new_bone_name

pprint(bone_dict)