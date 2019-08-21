import bpy
from bpy.props import *

class ChangeWPBrush(bpy.types.Operator):
	""" Just change the weight paint brush to an actual specific brush rather than a vague tool """
	bl_idname = "brush.set_specific"
	bl_label = "Set WP Brush"
	bl_options = {'REGISTER', 'UNDO'}

	brush: EnumProperty(name="Brush",
	items=[("ADD", "Add", "Add"),
			("SUBTRACT", "Subtract", "Subtract"),
			("BLUR", "Blur", "Blur"),
			],
	default="ADD")

	def execute(self, context):
		brush = self.brush

		if(brush == 'ADD'):
			bpy.context.tool_settings.weight_paint.brush = bpy.data.brushes['Add']
		elif(brush == 'SUBTRACT'):
			bpy.context.tool_settings.weight_paint.brush = bpy.data.brushes['Subtract']
		elif(brush == 'BLUR'):
			bpy.context.tool_settings.weight_paint.brush = bpy.data.brushes['Blur']

		return { 'FINISHED' }

def register():
	from bpy.utils import register_class
	register_class(ChangeWPBrush)

def unregister():
	from bpy.utils import unregister_class
	unregister_class(ChangeWPBrush)