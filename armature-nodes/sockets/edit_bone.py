import bpy
from bpy.types import NodeSocket

# Custom socket type
class EditBoneSocket(NodeSocket):
	bl_idname = 'arn_EditBoneSocket'
	bl_label = "Edit Bone Socket"

	bone_name: bpy.props.StringProperty(
		name="Bone Name",
		description="Bone Name",
		default='Bone'
	)

	# Optional function for drawing the socket input value
	def draw(self, context, layout, node, text):
		if self.is_output or self.is_linked:
			layout.label(text=text)
		else:
			layout.prop_search(self, "bone_name", context.object.data, "bones", text=text)

	# Socket color
	def draw_color(self, context, node):
		return (1.0, 1.0, 1.0, 1.0)