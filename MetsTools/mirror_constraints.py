import bpy
from . import utils

def copy_attributes(from_thing, to_thing):
	bad_stuff = ['__doc__', '__module__', '__slots__', 'active', 'bl_rna', 'error_location', 'error_rotation']
	for prop in dir(from_thing):
		if(prop in bad_stuff): continue
		if(hasattr(to_thing, prop)):
			value = getattr(from_thing, prop)
			try:
				setattr(to_thing, prop, value)
			except AttributeError:	# Read Only properties
				continue

class XMirrorConstraints(bpy.types.Operator):
	""" Mirror constraints to the opposite of all selected bones. """
	bl_idname = "armature.x_mirror_constraints"
	bl_label = "X Mirror Selected Bones' Constraints"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		for b in context.selected_pose_bones:
			#TODO: Finish adding all the constraint types.
			#TODO: Should also make sure constraints are in the correct order. - They should already be, though. Are we not wiping constraints before copying them? I thought we did.
			#TODO: Make a separate operator for "splitting" constraints in left/right parts. (by halving their influence, then mirror copying them onto the same bone)
			#TODO: mirror constraint's name.
			#TODO: copy axis locks and rotation mode.

			# would be cool if we could mirror on any axis, not just X. How on earth would that work though.
			# Maybe this can be done as an afterthought. Consider that during X mirroring, the X axis is the "mirror" axis, the Y axis is the forward axis and Z is the up axis.
			# If we wanted to mirror on the Y axis, it would be Y=Mirror, X = Forward, Z = Up
			# For Z axis mirroring though, X and Y are interchangable, are they not? I mean, neither of them are strictly forward or up. One of them is FOrward and the other is Left. 

			armature = context.object

			flipped_name = utils.flip_name(b.name)
			opp_b = armature.pose.bones.get(flipped_name)
			
			data_b = armature.data.bones.get(b.name)
			opp_data_b = armature.data.bones.get(opp_b.name)

			for c in b.constraints:
				opp_c = opp_b.constraints.get(c.name)
				if(not opp_c): 
					opp_c = opp_b.constraints.new(type=c.type)
				
				copy_attributes(c, opp_c)
					
				# Targets
				opp_c.target = c.target # TODO: could argue that this should be attempted to be flipped as well.
				opp_subtarget = utils.flip_name(c.subtarget)
				opp_c.subtarget = opp_subtarget
				
				if(c.type=='TRANSFORM'):
					###### SOURCES #######
					
					### Source Locations
					# X Loc: Flipped and Inverted
						opp_c.from_min_x = c.from_max_x *-1
						opp_c.from_max_x = c.from_min_x *-1
					# Y Loc: Same
					# Z Loc: Same

					### Source Rotations
					# X Rot: Same
					# Y Rot: Flipped and Inverted
						opp_c.from_min_y_rot = c.from_max_y_rot * -1
						opp_c.from_max_y_rot = c.from_min_y_rot * -1
					# Z Rot: Flipped and Inverted
						opp_c.from_min_z_rot = c.from_max_z_rot * -1
						opp_c.from_max_z_rot = c.from_min_z_rot * -1
					
					### Source Scales are same.
					
					###### DESTINATIONS #######
					
					### Destination Rotations
					
						### Location to Rotation
						if(c.map_from == 'LOCATION'):
							# X Loc to X Rot: Flipped
							if(c.map_to_x_from == 'X'):
								opp_c.to_min_x_rot = c.to_max_x_rot
								opp_c.to_max_x_rot = c.to_min_x_rot
							# X Loc to Y Rot: Same
							# X Loc to Z Rot: Flipped and Inverted
							if(c.map_to_z_from == 'X'):
								opp_c.to_min_z_rot = c.to_max_z_rot *-1
								opp_c.to_max_z_rot = c.to_min_z_rot *-1
							
							# Y Loc to X Rot: Same
							# Y Loc to Y Rot: Inverted
							if(c.map_to_y_from == 'Y'):
								opp_c.to_min_y_rot = c.to_min_y_rot *-1
								opp_c.to_max_y_rot = c.to_max_y_rot *-1
							# Y Loc to Z Rot: Inverted
							if(c.map_to_z_from == 'Y'):
								opp_c.to_min_z_rot = c.to_min_z_rot *-1
								opp_c.to_max_z_rot = c.to_max_z_rot *-1
							
							# Z Loc to X Rot: Same
							# Z Loc to Y Rot: Inverted
							if(c.map_to_y_from == 'Z'):
								opp_c.to_min_y_rot = c.to_min_y_rot *-1
								opp_c.to_max_y_rot = c.to_max_y_rot *-1
							# Z Loc to Z Rot: Inverted
							if(c.map_to_z_from == 'Z'):
								opp_c.to_min_z_rot = c.to_min_z_rot *-1
								opp_c.to_max_z_rot = c.to_max_z_rot *-1
					
						### Rotation to Rotation
						if(c.map_from == 'ROTATION'):
							# X Rot to X Rot: Same
							# X Rot to Y Rot: Inverted
							if(c.map_to_y_from == 'X'):
								opp_c.to_min_y_rot = c.to_min_y_rot *-1
								opp_c.to_max_y_rot = c.to_max_y_rot *-1
							# X Rot to Z Rot: Inverted
							if(c.map_to_z_from == 'X'):
								opp_c.to_min_z_rot = c.to_min_z_rot *-1
								opp_c.to_max_z_rot = c.to_max_z_rot *-1
							
							# Y Rot to X Rot: Flipped
							if(c.map_to_x_from == 'Y'):
								opp_c.to_min_x_rot = c.to_max_x_rot
								opp_c.to_max_x_rot = c.to_min_x_rot
							# Y Rot to Y Rot: Same
							# Y Rot to Z Rot: Flipped and Inverted
							if(c.map_to_z_from == 'Y'):
								opp_c.to_min_z_rot = c.to_max_z_rot * -1
								opp_c.to_max_z_rot = c.to_min_z_rot * -1
							
							# Z Rot to X Rot: Flipped
							if(c.map_to_x_from == 'Z'):
								opp_c.to_min_x_rot = c.to_max_x_rot
								opp_c.to_max_x_rot = c.to_min_x_rot
							# Z Rot to Y Rot: Flipped and Inverted
							if(c.map_to_y_from == 'Z'):
								opp_c.to_min_y_rot = c.to_max_y_rot * -1
								opp_c.to_max_y_rot = c.to_min_y_rot * -1
							# Z Rot to Z Rot: Flipped and Inverted
							if(c.map_to_z_from == 'Z'):
								opp_c.to_min_z_rot = c.to_max_z_rot * -1
								opp_c.to_max_z_rot = c.to_min_z_rot * -1
						
						### Scale to Rotation
						if(c.map_from == 'SCALE'):
							# ALL Scale to X Rot: Same
							# All Scale to Y Rot: Inverted
								opp_c.to_min_y_rot = c.to_min_y_rot *-1
								opp_c.to_max_y_rot = c.to_max_y_rot *-1
							# All Scale to Z Rot: Inverted
								opp_c.to_min_z_rot = c.to_min_z_rot *-1
								opp_c.to_max_z_rot = c.to_max_z_rot *-1
						
					### Destination Locations
						### Location to Location
						if(c.map_from == 'LOCATION'):
							# X Loc to X Loc: Flipped and Inverted
							if(c.map_to_x_from == 'X'):
								opp_c.to_min_x = c.to_max_x *-1
								opp_c.to_max_x = c.to_min_x *-1
							# X Loc to Y Loc: Flipped
							if(c.map_to_y_from == 'X'):
								opp_c.to_min_y = c.to_max_y
								opp_c.to_max_y = c.to_min_y
							# X Loc to Z Loc: Flipped
							if(c.map_to_z_from == 'X'):
								opp_c.to_min_z = c.to_max_z
								opp_c.to_max_z = c.to_min_z
							
							# Y Loc to X Loc: Inverted
							if(c.map_to_x_from == 'Y'):
								opp_c.to_min_x = c.to_min_x *-1
								opp_c.to_max_x = c.to_max_x *-1
							# Y Loc to Y Loc: Same
							# Y Loc to Z Loc: Same
							
							# Z Loc to X Loc: Inverted
							if(c.map_to_x_from == 'Z'):
								opp_c.to_min_x = c.to_min_x *-1
								opp_c.to_max_x = c.to_max_x *-1
							# Z Loc to Y Loc: Same
							# Z Loc to Z Loc: Same
						
						### Rotation to Location
						if(c.map_from == 'ROTATION'):
							# X Rot to X Loc: Inverted
							if(c.map_to_x_from == 'X'):
								opp_c.to_min_x = c.to_min_x * -1
								opp_c.to_max_x = c.to_max_x * -1
							# X Rot to Y Loc: Same
							# X Rot to Z Loc: Same
							
							# Y Rot to X Loc: Flipped and Inverted
							if(c.map_to_x_from == 'Y'):
								opp_c.to_min_x = c.to_max_x * -1
								opp_c.to_max_x = c.to_min_x * -1
							# Y Rot to Y Loc: Flipped
							if(c.map_to_y_from == 'Y'):
								opp_c.to_min_y = c.to_max_y
								opp_c.to_max_y = c.to_min_y
							# Y Rot to Z Loc: Flipped
							if(c.map_to_z_from == 'Y'):
								opp_c.to_min_z = c.to_max_z
								opp_c.to_max_z = c.to_min_z
							
							# Z Rot to X Loc: Flipped and inverted
							if(c.map_to_x_from == 'Z'):
								opp_c.to_min_x = c.to_max_x * -1
								opp_c.to_max_x = c.to_min_x * -1
							# Z Rot to Y Loc: Flipped
							if(c.map_to_y_from == 'Z'):
								opp_c.to_min_y = c.to_max_y
								opp_c.to_max_y = c.to_min_y
							# Z Rot to Z Loc: Flipped
							if(c.map_to_z_from == 'Z'):
								opp_c.to_min_z = c.to_max_z
								opp_c.to_max_z = c.to_min_z
						
						### Scale to Location
						if(c.map_from == 'SCALE'):
							# All Scale to X Loc: Inverted
							opp_c.to_min_x = c.to_min_x *-1
							opp_c.to_max_x = c.to_max_x *-1
							# All Scale to Y Loc: Same
							# All Scale to Z Loc: Same
					
					### Destination Scales
						# Location to Scale
						if(c.map_from == 'LOCATION'):
							# X Loc to All Scale: Flipped
							if(c.map_to_x_from == 'X'):
								opp_c.to_min_x_scale = c.to_max_x_scale
								opp_c.to_max_x_scale = c.to_min_x_scale
							if(c.map_to_y_from == 'X'):
								opp_c.to_min_y_scale = c.to_max_y_scale
								opp_c.to_max_y_scale = c.to_min_y_scale
							if(c.map_to_z_from == 'X'):
								opp_c.to_min_z_scale = c.to_max_z_scale
								opp_c.to_max_z_scale = c.to_min_z_scale
							# Y Loc to All Scale: Same
							# Z Loc to All Scale: Same
						
						# Rotation to Scale
						if(c.map_from == 'ROTATION'):
							# X Rot to All Scale: Same
							# Y Rot to All Scale: Flipped
							if(c.map_to_x_from == 'Y'):
								opp_c.to_min_x_scale = c.to_max_x_scale
								opp_c.to_max_x_scale = c.to_min_x_scale
							if(c.map_to_y_from == 'Y'):
								opp_c.to_min_y_scale = c.to_max_y_scale
								opp_c.to_max_y_scale = c.to_min_y_scale
							if(c.map_to_z_from == 'Y'):
								opp_c.to_min_z_scale = c.to_max_z_scale
								opp_c.to_max_z_scale = c.to_min_z_scale
							# Z Rot to All Scale: Flipped
							if(c.map_to_x_from == 'Z'):
								opp_c.to_min_x_scale = c.to_max_x_scale
								opp_c.to_max_x_scale = c.to_min_x_scale
							if(c.map_to_y_from == 'Z'):
								opp_c.to_min_y_scale = c.to_max_y_scale
								opp_c.to_max_y_scale = c.to_min_y_scale
							if(c.map_to_z_from == 'Z'):
								opp_c.to_min_z_scale = c.to_max_z_scale
								opp_c.to_max_z_scale = c.to_min_z_scale
						
						# Scale to Scale is all same.
		
			# Mirroring Bendy Bone settings
			opp_data_b.bbone_handle_type_start 		= data_b.bbone_handle_type_start
			opp_data_b.bbone_handle_type_end 		= data_b.bbone_handle_type_end
			if(data_b.bbone_custom_handle_start):
				opp_data_b.bbone_custom_handle_start 	= armature.data.bones.get(utils.flip_name(data_b.bbone_custom_handle_start.name))
			else:
				opp_data_b.bbone_custom_handle_start = None
			if(data_b.bbone_custom_handle_end):
				opp_data_b.bbone_custom_handle_end 		= armature.data.bones.get(utils.flip_name(data_b.bbone_custom_handle_end.name))
			else:
				opp_data_b.bbone_custom_handle_end = None
			opp_data_b.bbone_segments 				= data_b.bbone_segments
			# Inherit End Roll
			opp_data_b.use_endroll_as_inroll 		= data_b.use_endroll_as_inroll
			
			# Edit mode curve settings
			opp_data_b.bbone_curveinx = data_b.bbone_curveinx *-1
			opp_data_b.bbone_curveoutx = data_b.bbone_curveoutx *-1
			opp_data_b.bbone_curveiny = data_b.bbone_curveiny
			opp_data_b.bbone_curveouty = data_b.bbone_curveouty
			opp_data_b.bbone_rollin = data_b.bbone_rollin *-1
			opp_data_b.bbone_rollout = data_b.bbone_rollout *-1
			opp_data_b.bbone_scaleinx = data_b.bbone_scaleinx
			opp_data_b.bbone_scaleiny = data_b.bbone_scaleiny
			opp_data_b.bbone_scaleoutx = data_b.bbone_scaleoutx
			opp_data_b.bbone_scaleouty = data_b.bbone_scaleouty

			# Mirroring bone shape
			if(b.custom_shape):
				opp_b.custom_shape = bpy.data.objects.get(utils.flip_name(b.custom_shape.name))
				opp_data_b.show_wire = data_b.show_wire
				opp_b.custom_shape_scale = b.custom_shape_scale
				opp_b.use_custom_shape_bone_size = b.use_custom_shape_bone_size
				if(b.custom_shape_transform):
					opp_b.custom_shape_transform = armature.pose.bones.get(utils.flip_name(b.custom_shape_transform.name))


			#NOTE: curve values are not mirrored, since as far as my use cases go, they would always be the default values, unless there are drivers on them, and driver mirroring is a TODO.

		return {"FINISHED"}

def register():
	from bpy.utils import register_class
	register_class(XMirrorConstraints)

def unregister():
	from bpy.utils import unregister_class
	unregister_class(XMirrorConstraints)