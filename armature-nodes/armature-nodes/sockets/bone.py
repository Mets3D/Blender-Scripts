import bpy
from bpy.types import NodeSocket
from bpy.props import *

# Custom socket type
class BoneSocket(NodeSocket):
	'''Custom node socket type'''
	bl_idname = 'arn_BoneSocket'
	bl_label = "Bone Socket"

	bone_name: StringProperty(
		name="Bone Name",
		description="Bone Name",
		default="Bone"
	)
	bone: PointerProperty(type=bpy.types.Bone)

	# Optional function for drawing the socket input value
	def draw(self, context, layout, node, text):
		if self.is_output or self.is_linked:
			layout.label(text=text)
		else:
			layout.prop_search(self, "bone_name", context.object.data, "bones", text=text)

	# Socket color
	def draw_color(self, context, node):
		return (1.0, 1.0, 1.0, 1.0)
	
	# Execute finds and returns the value that this socket should have.
	@property
	def value(self):
		# TODO: If something is plugged into this socket, get the value of that socket to determine self.bone_name.
		#self.node.node_tree.armature.data.bones.get(self.bone_name)
		return context.object.data.bones.get(self.bone_name)