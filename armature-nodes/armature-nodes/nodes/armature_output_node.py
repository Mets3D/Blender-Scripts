import bpy
from .armature_node import ArmatureNode
from bpy.props import *
from bpy.types import Node

class ArmatureOutputNode(Node, ArmatureNode):
	'''Armature Output Node'''
	bl_idname = 'arn_ArmatureOutputNode'
	bl_label = "Output Node"

	bone_names: bpy.props.StringProperty()
	
	def init(self, context):
		self.inputs.new('arn_BoneSocket', "Bones")

	# Copy function to initialize a copied node from an existing one.
	def copy(self, node):
		print("Copying from node ", node)

	# Free function to clean up on removal.
	def free(self):
		print("Removing node ", self, ", Goodbye!")

	# Additional buttons displayed on the node.
	def draw_buttons(self, context, layout):
		layout.label(text="Node settings")

	# Optional: custom label
	# Explicit user label overrides this, but here we can define a label dynamically
	def draw_label(self):
		return "I am a custom node"