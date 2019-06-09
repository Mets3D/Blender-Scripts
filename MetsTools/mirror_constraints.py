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
				
				# Visibility
				opp_c.mute = c.mute
				
				# Influnce
				opp_c.influence = c.influence
				
				if(c.type=='TRANSFORM'):
					# Source->Destination mapping
						opp_c.map_from = c.map_from
						opp_c.map_to = c.map_to
						
						opp_c.map_to_x_from = c.map_to_x_from
						opp_c.map_to_y_from = c.map_to_y_from
						opp_c.map_to_z_from = c.map_to_z_from
					
					# Spaces
						opp_c.target_space = c.target_space
						opp_c.owner_space = c.owner_space
					
					# Extrapolate
						opp_c.use_motion_extrapolate = c.use_motion_extrapolate
					
					#########################
					###### TRANSFORMS #######
					#########################
					
					###### SOURCES #######
					
					### Source Rotations
					
					# X Rot: same
						opp_c.from_max_x_rot = c.from_max_x_rot
						opp_c.from_min_x_rot = c.from_min_x_rot
					
					# Y Rot: Todo
					
					# Z Rot: flipped and inverted
						opp_c.from_max_z_rot = c.from_min_z_rot * -1
						opp_c.from_min_z_rot = c.from_max_z_rot * -1
					
					### Source Locations (Everything is the same I think)
						opp_c.from_min_x = c.from_min_x
						opp_c.from_max_x = c.from_max_x
						
						opp_c.from_min_y = c.from_min_y
						opp_c.from_max_y = c.from_max_y
						
						opp_c.from_min_z = c.from_min_z
						opp_c.from_max_z = c.from_max_z
					
					###### DESTINATIONS #######
					
					### Destination Rotations
					
					### Destination Rotations when source is Rotation
						if(c.map_from == 'ROTATION'):
							if(c.map_to_x_from == 'X'):		# If the source is X rotation
								# X Rot: same
								opp_c.to_max_x_rot = c.to_max_x_rot
								opp_c.to_min_x_rot = c.to_min_x_rot
								
								# Y Rot: TODO
								
								# Z Rot: TODO
							
							# Source Y Rot: TODO
							
							if(c.map_to_x_from == 'Z'):		# If the source is Z rotation
								# X Rot: flipped
								opp_c.to_max_x_rot = c.to_min_x_rot
								opp_c.to_min_x_rot = c.to_max_x_rot
								
								# Y Rot: flipped and inverted
								opp_c.to_max_y_rot = c.to_min_y_rot * -1
								opp_c.to_min_y_rot = c.to_max_y_rot * -1
								
								# Z Rot: flipped and inverted
								opp_c.to_max_z_rot = c.to_min_z_rot * -1
								opp_c.to_min_z_rot = c.to_max_z_rot * -1
						
						### Destination Locations (TODO: the parts under identical if statements could be merged, of course)
						
						### Destination Locations when source is Rotation
						if(c.map_from == 'ROTATION'):
							if(c.map_to_x_from == 'X'):		# If the source is X rotation
								# X Loc: inverted
								opp_c.to_min_x = c.to_min_x * -1
								opp_c.to_max_x = c.to_max_x * -1
								
								# Y Loc: same
								opp_c.to_min_y = c.to_min_y
								opp_c.to_max_y = c.to_max_y
								
								# Z Loc: same
								opp_c.to_min_z = c.to_min_z
								opp_c.to_max_z = c.to_max_z
							elif(c.map_to_x_from == 'Z'):	# If the source is Z rotation
								# X Loc: flipped and inverted
								opp_c.to_min_x = c.to_max_x * -1
								opp_c.to_max_x = c.to_min_x * -1
								
								# Y Loc: flipped
								opp_c.to_min_y = c.to_max_y
								opp_c.to_max_y = c.to_min_y
								
								# Z Loc: TODO
								opp_c.to_min_z = c.to_min_z
								opp_c.to_max_z = c.to_max_z
						
						### Destination Locations when source is Location
						if(c.map_from == 'LOCATION'):
							if(c.map_to_x_from == 'X'):		# If the source is X rotation
								# X Loc: inverted
								opp_c.to_min_x = c.to_min_x	#TODO: the comment says this should be inverted, but it isn't. Which is right?
								opp_c.to_max_x = c.to_max_x
								
								# Y Loc: same
								opp_c.to_min_y = c.to_min_y
								opp_c.to_max_y = c.to_max_y
								
								# Z Loc: same
								opp_c.to_min_z = c.to_min_z
								opp_c.to_max_z = c.to_max_z
							
							if(c.map_to_x_from == 'Y'):		# If the source is Y rotation
								# X Loc: inverted
								opp_c.to_min_x = c.to_min_x *-1
								opp_c.to_max_x = c.to_max_x *-1
								
								# Y Loc: TODO
								
								# Z Loc: TODO
		
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