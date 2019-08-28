import bpy
from bpy.types import NodeSocket
from bpy.props import *

# Custom socket type
class EditBoneListSocket(NodeSocket):
	bl_idname = 'arn_EditBoneListSocket'
	bl_label = "Edit Bone List Socket"

	bone_names: CollectionProperty(type=StringProperty)

	# Optional function for drawing the socket input value
	def draw(self, context, layout, node, text):
		layout.label(text=text)
		
	# Socket color
	def draw_color(self, context, node):
		return (0.5, 0.5, 0.5, 1.0)