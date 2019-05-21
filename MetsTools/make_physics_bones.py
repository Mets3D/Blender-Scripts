import bpy
from bpy.props import *
import mathutils
import math

def make_physics_bone_chain(armature, bones):
	""" Apply physics to a single chain of bones. Armature needs to have clean transforms and be in rest pose.
		bones: list of bones in the chain, in correct hierarchical order"""
	# This function expects the armature with clean transforms and in rest pose.

	parent_bone = bones[0].parent	# Can be None.
	
	# Create physics mesh (It gets automatically selected)
	bpy.ops.mesh.primitive_plane_add(enter_editmode=True, location=bones[0].head)
	# The operator makes the new object active and in edit mode, but just to make it explicit...
	bpy.ops.object.mode_set(mode='EDIT')
	pMesh = bpy.context.object
	bpy.context.object.name = "_Phys_" + bones[0].name

	pVerts = pMesh.data.vertices

	# We can't deselect a single vert without bmesh and without knowing which edges and faces are connected to it.
	# So I just deselect everything then select what I need.
	bpy.ops.mesh.select_all(action='DESELECT')
	bpy.ops.object.mode_set(mode='OBJECT')

	# Need to select verts while in object mode for some reason.
	for i in range(1,4):
		pVerts[i].select=True

	bpy.ops.object.mode_set(mode='EDIT')
	bpy.ops.mesh.delete(type='VERT')
	bpy.ops.object.mode_set(mode='OBJECT')

	# Setting the last remaining vert to the object's location(first bone's head)
	pVerts[0].select=True
	pVerts[0].co = (0, 0, 0)

	bpy.ops.object.mode_set(mode='EDIT')

	# Extruding verts to each bone's head
	for i in range(0, len(bones)):
		bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value":(
		bones[i].tail.x - bones[i].head.x, 
		bones[i].tail.y - bones[i].head.y, 
		bones[i].tail.z - bones[i].head.z)})

	bpy.ops.object.mode_set(mode='OBJECT')

	for i in range(0, len(pVerts)):
		bpy.ops.object.vertex_group_add()   			# Create new vertex group
		pMesh.vertex_groups[i].add([i], 1.0, 'ADD')  # Adding vert to vertex group (vertexIndex, Weight, 'garbage')
		if(i == 0):
			pMesh.vertex_groups[i].name = "Pin"
		else:
			pMesh.vertex_groups[i].name = bones[i-1].name # Naming vGroup
			
	# Extruding all verts to have faces, which is necessary for collision.
	# Additionally, the Angular bending model won't move if it has faces with 0 area, so I'm spreading the verts out a tiny amount on the X axis.
	bpy.ops.object.mode_set(mode='EDIT')
	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value":(0.1, 0, 0)})
	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.transform.translate(value=(-0.05, 0, 0))
	bpy.ops.object.mode_set(mode='OBJECT')

	# Adding Cloth modifier
	bpy.ops.object.modifier_add(type='CLOTH')
	m_cloth = pMesh.modifiers["Cloth"]
	m_cloth.settings.vertex_group_mass = "Pin"

	if(parent_bone):
		bpy.ops.object.mode_set(mode='OBJECT')  		# Go to object mode
		bpy.ops.object.select_all(action='DESELECT')	# Deselect everything
		pMesh.select_set(True)  						# Select physics mesh
		armature.select_set(True)						# Select armature
		bpy.context.view_layer.objects.active = armature   # Make armature active
		bpy.ops.object.mode_set(mode='POSE')			# Go into pose mode
		bpy.ops.pose.select_all(action='DESELECT')  	# Deselect everything
		parent_bone.bone.select = True   				# Make parent bone select
		armature.data.bones.active = parent_bone.bone  # Make the parent bone active
		bpy.ops.object.parent_set(type='BONE')  		# Set parent (=Ctrl+P->Bone)
		parent_bone.bone.select = False

	# Setting up bone constraints
	bpy.context.view_layer.objects.active = armature
	for i, b in enumerate(bones):
		b.bone.select=True
		
		if(i==0 or armature.data.bones[b.name].use_connect == False):   # Copy Location constraint only needed on the first bone of the chain, or bones that have use_connect=False.
			CL = bones[i].constraints.new(type='COPY_LOCATION')
			CL.target = pMesh
			CL.subtarget = pMesh.vertex_groups[i].name
		
		DT = bones[i].constraints.new(type='DAMPED_TRACK')
		DT.target = pMesh
		DT.subtarget = pMesh.vertex_groups[i+1].name

	#bpy.ops.armature.separate() # Physics bones needs to be a separate armature to avoid dependency cycles.
	bpy.ops.object.mode_set(mode='POSE')

class MakePhysicsBones(bpy.types.Operator):
	""" Set up physics to all selected bone chains. Only the first bone of each chain should be selected. """
	bl_idname = "pose.make_physics_bones"
	bl_label = "Make Physics Bones"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):	
		armature = bpy.context.object

		if(armature.type!='ARMATURE'):
			print( "ERROR: Active object must be an armature. Select a chain of bones.")
			return { "CANCELLED" }

		# Set armature to Rest Position, and reset its transforms.
		org_pose = armature.data.pose_position
		armature.data.pose_position = 'REST'
		org_loc = armature.location[:]
		armature.location = (0,0,0)
		org_rot_euler = armature.rotation_euler[:]
		armature.rotation_euler = (0,0,0)
		org_rot_quat = armature.rotation_quaternion[:]
		armature.rotation_quaternion = (0,0,0,0)
		org_scale = armature.scale[:]
		armature.scale = (1,1,1)
		org_mode = armature.mode
		bpy.ops.object.mode_set(mode='POSE')
		
		def get_chain(bone, ret=[]):
			""" Recursively build a list of the first children. """
			ret.append(bone)
			if(len(bone.children) > 0):
				return get_chain(bone.children[0], ret)
			return ret

		bones = bpy.context.selected_pose_bones
		for b in bones:
			if(b.parent not in bones):
				chain = get_chain(b, [])	# I don't know why but I have to pass the empty list for it to reset the return list.
				make_physics_bone_chain(armature, chain)
		
		# Reset armature transforms.
		bpy.ops.object.mode_set(mode='OBJECT')
		armature.data.pose_position = org_pose
		armature.location = org_loc
		armature.rotation_euler = org_rot_euler
		armature.rotation_quaternion = org_rot_quat
		armature.scale = org_scale
		bpy.ops.object.mode_set(mode=org_mode)

		return { 'FINISHED' }

def draw_func_MakePhysicsBones(self, context):
	self.layout.operator(MakePhysicsBones.bl_idname, text=MakePhysicsBones.bl_label)

def register():
	from bpy.utils import register_class
	register_class(MakePhysicsBones)

def unregister():
	from bpy.utils import unregister_class
	unregister_class(MakePhysicsBones)