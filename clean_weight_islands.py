import bpy
import bmesh
import sys

# Select linked verts if they are in the given vertex group.
def select_linked_verts(bvert, mesh, group_index):
	bvert.select_set(True)			# Select starting vert
	for be in bvert.link_edges:		# For each edge connected to the vert
		for bv in be.verts:			# For each of the edge's 2 verts
			if(not bv.select):		# If this vert is not selected yet
				for g in mesh.vertices[bv.index].groups:		# For each group this vertex belongs to
					if(g.group == group_index):					# If this vert IS in the group
						select_linked_verts(bv, mesh, group_index)	# Continue recursion

def clean_weight_islands(o, groups=None, use_influence=False):
	# Removes weight "Islands" in all vertex groups in all selected objects.
	
	if(groups==None):
		groups = o.vertex_groups
	
	# Saving state
	start_object = bpy.context.object
	start_mode = bpy.context.object.mode

	# Cleaning 0-weights
	bpy.context.view_layer.objects.active = o
	bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
	bpy.ops.object.vertex_group_clean(group_select_mode='ALL', limit=0)
	
	mesh = o.data
	for group in groups:
		print("group: " + group.name)
		bpy.ops.object.mode_set(mode='EDIT')
		bm = bmesh.from_edit_mesh(mesh)
		bm.verts.ensure_lookup_table()
		
		# Deselecting all verts
		bpy.ops.mesh.select_all(action='DESELECT')

		islands = []	# list of integer lists.
		checked_verts = []

		# Finding a random vert in the vertex group
		for v in mesh.vertices:
			if(v.index not in checked_verts):
				checked_verts.append(v.index)
				for g in v.groups:
					if(group.index == g.group):	# If we found one
						sys.setrecursionlimit(10000)
						select_linked_verts(bm.verts[v.index], o.data, group.index)
						sys.setrecursionlimit(1000)
						island = []
						for bv in bm.verts:
							if(bv.select == True):
								checked_verts.append(bv.index)
								island.append(bv.index)
						islands.append(island)
						bpy.ops.mesh.select_all(action='DESELECT')

		marked_verts = []	# Verts marked for deletion from the vertex group due to not being part of the biggest island

		winning_island = []	# Verts of the current biggest island
		max_influence = 0	# Greatest total influence of an island
		max_verts = 0 # Greatest number of verts in an island

		for isl in islands:
			if(use_influence):
				total_influence = 0
				for i in isl:
					vert = mesh.vertices[i]
					for g in vert.groups:
						if(g.group == group.index):
							total_influence = total_influence + g.weight
				if(total_influence > max_influence):
					max_influence = total_influence
					marked_verts.extend(winning_island)
					winning_island = isl
				else:
					marked_verts.extend(isl)
			else:
				if(len(isl) > max_verts):
					max_verts = len(isl)
					marked_verts.extend(winning_island)
					winning_island = isl
				else:
					marked_verts.extend(isl)
		bpy.ops.object.mode_set(mode='OBJECT')
		group.remove(marked_verts)


	# Resetting state
	bpy.context.view_layer.objects.active = start_object
	bpy.ops.object.mode_set(mode=start_mode)

for o in bpy.context.selected_objects:
	clean_weight_islands(o)