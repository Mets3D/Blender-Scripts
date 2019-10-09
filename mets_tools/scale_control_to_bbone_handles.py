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
				my_d = Driver()
				my_var = my_d.make_var("var")
				my_var.type = 'TRANSFORMS'
				my_d.expression = "var"

				tgt = my_var.targets[0]
				tgt.id = context.object
				tgt.transform_type = 'SCALE_X'
				tgt.transform_space = 'WORLD_SPACE'
				tgt.bone_target = b.bbone_custom_handle_start.name
				my_d.make_real(pb, "bbone_scaleinx")
				
				tgt.transform_type = 'SCALE_Z'
				my_d.make_real(pb, "bbone_scaleiny")
				
				tgt.bone_target = b.bbone_custom_handle_end.name
				my_d.make_real(pb, "bbone_scaleouty")

				tgt.transform_type = 'SCALE_X'
				my_d.make_real(pb, "bbone_scaleoutx")

			else:
				return {'CANCELLED'}

		return {'FINISHED'}

def register():
	from bpy.utils import register_class
	register_class(Setup_BBone_Scale_Controls)

def unregister():
	from bpy.utils import unregister_class
	unregister_class(Setup_BBone_Scale_Controls)