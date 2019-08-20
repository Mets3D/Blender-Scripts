
import bpy
from . import utils

# TODO: Should find a way to select the X axis verts before doing Remove Doubles, or don't Remove Doubles at all. Also need to select the Basis shape before doing Remove Doubles.
# TODO: Implement our own Remove Doubles algo with kdtree, which would average the vertex weights of the merged verts rather than just picking the weights of one of them at random.

class ForceApplyMirror(bpy.types.Operator):
	""" Force apply mirror modifier by duplicating the object and flipping it on the X axis. """
	bl_idname = "object.force_apply_mirror_modifier"
	bl_label = "Force Apply Mirror Modifier"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		# Remove Mirror Modifier
		# Copy mesh
		# Scale it -1 on X
		# Flip vgroup names
		# Join into original mesh
		# Remove doubles
		# Recalc Normals
		# Weight Normals

		o = context.object
		bpy.ops.object.mode_set(mode='OBJECT')
		bpy.ops.object.select_all(action='DESELECT')
		org_scale = o.scale[:]
		for m in o.modifiers:
			if(m.type=='MIRROR'):
				o.modifiers.remove(m)
				o.select_set(True)
				context.view_layer.objects.active = o
				
				# Removing Doubles - This should print out removed 0, otherwise we're gonna remove some important verts.
				#print("Checking for doubles pre-mirror. If it doesn't say Removed 0 vertices, you should undo.")
				#bpy.ops.object.mode_set(mode='EDIT')
				#bpy.ops.mesh.remove_doubles(use_unselected=True)
				
				# Reset scale
				#bpy.ops.object.mode_set(mode='OBJECT')
				o.scale = (1, 1, 1)

				bpy.ops.object.duplicate() 	# Duplicated object becomes selected and active
				
				# We continue operating on the original half, since it shouldn't matter
				o.scale = (-1, 1, 1)
				
				done = []	# Don't flip names twice...

				# Flipping vertex group names
				for vg in o.vertex_groups:
					if(vg in done): continue
					old_name = vg.name
					flipped_name = utils.flip_name(vg.name)
					if(old_name == flipped_name): continue
					
					if(flipped_name in o.vertex_groups):			# If the target name is already taken
						vg.name = "temp_lskjghsjdfkhbnsdf"			# Rename this to some garbage
						opp_group = o.vertex_groups[flipped_name]	# Find the other group that's taking the name
						opp_group.name = old_name					# Rename it to our original name
						done.append(opp_group)

					vg.name = flipped_name
					done.append(vg)
				
				o.select_set(True)
				context.view_layer.objects.active = o	# We want to be sure the original is the active so the object name doesn't get a .001
				bpy.ops.object.join()
				bpy.ops.object.mode_set(mode='EDIT')
				bpy.ops.mesh.select_all(action='SELECT')
				bpy.ops.mesh.normals_make_consistent(inside=False)
				#bpy.ops.mesh.remove_doubles()
				bpy.ops.object.mode_set(mode='OBJECT')
				bpy.ops.object.calculate_weighted_normals()
			break
		context.object.scale = org_scale
		return {'FINISHED'}

def register():
	from bpy.utils import register_class
	register_class(ForceApplyMirror)

def unregister():
	from bpy.utils import unregister_class
	unregister_class(ForceApplyMirror)