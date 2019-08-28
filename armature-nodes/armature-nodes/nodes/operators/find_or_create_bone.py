import bpy
from ..armature_node import ArmatureNode
from bpy.props import *

class FindOrCreateBoneNode(ArmatureNode):
	bl_idname = 'arn_ArmatureOutputNode'
	bl_label = "Find/Create"
	
	def init(self, context):
		self.inputs.new('NodeSocketString', "Name")
		self.outputs.new('arn_BoneSocket', "Bone")
	
	def execute(self, context):
		org_mode = context.object.mode
		bpy.ops.object.mode_set(mode='EDIT')
		print(self.inputs['Bone'].bone_name)
		self.bone = context.object.data.edit_bones.new(name=self.inputs['Bone'].bone_name)
		bpy.ops.object.mode_set(mode=org_mode)
		return self.bone