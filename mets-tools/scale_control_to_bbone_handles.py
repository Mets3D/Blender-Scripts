import bpy
from .armature_nodes.driver import *

class Setup_BBone_Scale_Controls(bpy.types.Operator):
	""" Set up drivers and settings to let bendy bones scale be controlled by their bbone handles. """
	bl_idname = "armature.bbone_scale_controls"
	bl_label = "Scale Drivers for BBone Handles"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return context.object.mode == 'POSE'

	def execute(self, context):
		for pb in context.selected_pose_bones:
			b = pb.bone
			# Make sure bone has both handles specified, and handle type is set to Tangent.
			if(b.bbone_segments > 1
					and b.bbone_handle_type_start == 'TANGENT'
					and b.bbone_handle_type_end == 'TANGENT'
					and b.bbone_custom_handle_start
					and b.bbone_custom_handle_end):
				pass

		return {'FINISHED'}

def register():
	from bpy.utils import register_class
	register_class(Setup_BBone_Scale_Controls)

def unregister():
	from bpy.utils import unregister_class
	unregister_class(Setup_BBone_Scale_Controls)