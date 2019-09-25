import bpy
import bmesh
from . import utils
from . import shape_key_utils

def mirror_mesh(obj):
	mesh = obj.data
	# Mirror shape keys...
	# We assume that all shape keys ending in .L actually deform both sides, but are masked with a vertex group, which also ends in .L.
	# If the .R version of the shape key exists, delete it.
	# Save and temporarily remove the vertex group mask
	# Enable pinning and make this shape key active
	# New Shape From Mix
	# Rename the new shape key to .R and re-add vgroup masks.
	shape_keys = mesh.shape_keys.key_blocks
	# Remove shape keys if they already exist.
	sk_names = [sk.name for sk in shape_keys]
	done = []
	for skn in sk_names:
		if(skn in done): continue
		sk = shape_keys.get(skn)
		flipped_name = utils.flip_name(sk.name)
		if(flipped_name == sk.name): continue

		if(flipped_name in shape_keys):
			obj.active_shape_key_index = shape_keys.find(flipped_name)
			bpy.ops.object.shape_key_remove()
			done.append(skn)
			done.append(flipped_name)

	sk_names = [sk.name for sk in shape_keys]
	for skn in sk_names:
		sk = shape_keys.get(skn)
		flipped_name = utils.flip_name(sk.name)
		if(flipped_name == sk.name): continue
		
		flipped_vg = ""
		if(sk.vertex_group != ""):
			flipped_vg = utils.flip_name(sk.vertex_group)

		split_dict = {	# TODO maybe this should be built into the split function as some sort of preset or make another function that calls that after doing this.
			flipped_name : flipped_vg,
			}
		shape_key_utils.split_shapekey(obj, sk.name, split_dict)


class MirrorRigOperator(bpy.types.Operator):
	""" Mirror rig stuff """
	bl_idname = "object.mirror_rig"
	bl_label = "Mirror Rig"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		# TODO (due to shortage of time, do these manually for now)
		### MESH ###
		# Delete all verts with X<0
		# Add and apply mirror modifier
		# Split shape keys to left/right (automating this part is WIP)
		# Copy and mirror drivers
			# Need to figure out how to determine whether a variable in a driver should be inverted or not based on the transform axis. If it can't be done here, I don't understand why it could be done in the constraint mirror script - Maybe I made some incorrect assumptions in there??
		# 

		for o in context.selected_objects:
			context.view_layer.objects.active = o
			if(o.type=='MESH'):
				mirror_mesh(o)
			if(o.type=='ARMATURE'):
				mirror_armature(o)
		
		return { 'FINISHED' }


def register():
	from bpy.utils import register_class
	register_class(MirrorRigOperator)

def unregister():
	from bpy.utils import unregister_class
	unregister_class(MirrorRigOperator)