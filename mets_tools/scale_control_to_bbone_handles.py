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
			if(b.bbone_segments > 1):
				### Scale In/Out X/Z
				my_d = Driver()
				my_var = my_d.make_var("var")
				my_var.type = 'TRANSFORMS'
				
				var_tgt = my_var.targets[0]
				var_tgt.id = context.object
				var_tgt.transform_space = 'WORLD_SPACE'
				
				scale_var = my_d.make_var("scale")
				scale_var.type = 'TRANSFORMS'
				scale_tgt = scale_var.targets[0]
				scale_tgt.id = context.object
				scale_tgt.transform_space = 'WORLD_SPACE'
				scale_tgt.transform_type = 'SCALE_Y'
				
				my_d.expression = "var/scale"

				# Scale In X/Y
				if (b.bbone_handle_type_start == 'TANGENT' and b.bbone_custom_handle_start):
					var_tgt.bone_target = b.bbone_custom_handle_start.name

					var_tgt.transform_type = 'SCALE_X'
					my_d.make_real(pb, "bbone_scaleinx")

					var_tgt.transform_type = 'SCALE_Z'
					my_d.make_real(pb, "bbone_scaleiny")
				
				# Scale Out X/Y
				if (b.bbone_handle_type_end == 'TANGENT' and b.bbone_custom_handle_end):
					var_tgt.bone_target = b.bbone_custom_handle_end.name
					
					var_tgt.transform_type = 'SCALE_Z'
					my_d.make_real(pb, "bbone_scaleouty")

					var_tgt.transform_type = 'SCALE_X'
					my_d.make_real(pb, "bbone_scaleoutx")

				### Ease In/Out
				my_d = Driver()

				my_d.expression = "scale-Y"

				scale_var = my_d.make_var("scale")
				scale_var.type = 'TRANSFORMS'
				scale_tgt = scale_var.targets[0]
				scale_tgt.id = context.object
				scale_tgt.transform_type = 'SCALE_Y'
				scale_tgt.transform_space = 'LOCAL_SPACE'

				Y_var = my_d.make_var("Y")
				Y_var.type = 'TRANSFORMS'
				Y_tgt = Y_var.targets[0]
				Y_tgt.id = context.object
				Y_tgt.transform_type = 'SCALE_AVG'
				Y_tgt.transform_space = 'LOCAL_SPACE'

				# Ease In
				if (b.bbone_handle_type_start == 'TANGENT' and b.bbone_custom_handle_start):
					Y_tgt.bone_target = scale_tgt.bone_target = b.bbone_custom_handle_start.name
					my_d.make_real(pb, "bbone_easein")

				# Ease Out
				if (b.bbone_handle_type_end == 'TANGENT' and b.bbone_custom_handle_end):
					Y_tgt.bone_target = scale_tgt.bone_target = b.bbone_custom_handle_end.name
					my_d.make_real(pb, "bbone_easeout")

			else:
				return {'CANCELLED'}

		return {'FINISHED'}

def register():
	from bpy.utils import register_class
	register_class(Setup_BBone_Scale_Controls)

def unregister():
	from bpy.utils import unregister_class
	unregister_class(Setup_BBone_Scale_Controls)