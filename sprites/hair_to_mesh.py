import bpy
from bpy.types import (Operator, Panel)
from bpy.utils import register_class

class HairException(Exception):
    pass


################################################################################
# Hair to mesh conversion.

def get_mesh_name_for_hair(object, particle_system):
    """
    Get name for object which will hold strand data as mesh edges
    """
    return f"{object.name}-{particle_system.name}"


def prepare_mesh_object_for_hair(context, object, particle_system):
    """
    Get object ready to accept the hair strand data

    The name of the mesh object is derived from the name of the object with
    haie and the hair particle system name. If such object already exists in
    the main database it is reused.

    The object is always returned with empty mesh. The object is linked to the
    scene collection ans is never becoming selected or active.
    """

    mesh_name = get_mesh_name_for_hair(object, particle_system)

    mesh_object = bpy.data.objects.get(mesh_name, None)
    if mesh_object is not None:
        mesh_object.data.clear_geometry()
        return mesh_object

    scene = context.scene
    layer = context.view_layer

    mesh = bpy.data.meshes.new(name=mesh_name)
    mesh_object = bpy.data.objects.new(mesh_name, mesh)

    layer_collection = context.layer_collection or layer.active_layer_collection
    scene_collection = layer_collection.collection
    scene_collection.objects.link(mesh_object)

    return mesh_object


class HairToMeshContext:
    """
    Context which is used across the hair-to-mesh conversion

    Contains all non-trivial-to-calculate fields which are accessed from different
    steps of the conversion.
    """

    def __init__(self, particle_system):
        self.particle_system = particle_system
        self.num_total_hair_keys = 0
        self.num_total_hair_segments = 0

        for particle in particle_system.particles:
            num_hair_keys = len(particle.hair_keys)
            self.num_total_hair_keys += num_hair_keys

        num_particles = len(particle_system.particles)
        self.num_total_hair_segments = self.num_total_hair_keys - num_particles


def hair_keys_to_vertices(hair_to_mesh_ctx, mesh):
    """
    Convert hair key coordinates to mesh vertices

    The mesh becomes a point cloud after this step.
    """

    particle_system = hair_to_mesh_ctx.particle_system

    mesh.vertices.add(hair_to_mesh_ctx.num_total_hair_keys)
    
    vertex_index = 0
    vertices = mesh.vertices
    for particle in particle_system.particles:
        for hair_key in particle.hair_keys:
            vertices[vertex_index].co = hair_key.co
            vertex_index += 1


def hair_keys_to_edges(hair_to_mesh_ctx, mesh):
    """
    Connect vertices to represent hair strands
    
    Vertices are to be added to the mesh prior to this step.
    """

    particle_system = hair_to_mesh_ctx.particle_system

    mesh.edges.add(hair_to_mesh_ctx.num_total_hair_segments)
    
    vertex_index = 0
    edge_index = 0
    edges = mesh.edges
    for particle in particle_system.particles:
        num_hair_keys = len(particle.hair_keys)
        for segment_index in range(num_hair_keys - 1):
            start_vertex_index = vertex_index + segment_index;
            edges[edge_index].vertices = (start_vertex_index, start_vertex_index + 1)
            edge_index += 1
        vertex_index += num_hair_keys


def hair_to_mesh(context, object, particle_system):
    """
    Convert hair particle system to mesh
    """

    settings = particle_system.settings
    if settings.type != "HAIR":
        raise HairException("Can only operate on hair type of particle system")

    mesh_object = prepare_mesh_object_for_hair(context, object, particle_system)
    mesh_object.matrix_world = object.matrix_world
    mesh = mesh_object.data

    hair_to_mesh_ctx = HairToMeshContext(particle_system)
    hair_keys_to_vertices(hair_to_mesh_ctx, mesh)
    hair_keys_to_edges(hair_to_mesh_ctx, mesh)
    
    mesh.update(calc_edges=True, calc_edges_loose=True)

    return mesh_object

class HAIR_OT_hair_to_mesh(Operator):
    """Convert hair system to mesh"""

    bl_idname = "hair.hair_to_mesh"
    bl_label = "Hair To Mesh"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        depsgraph = context.evaluated_depsgraph_get()

        object = context.object
        if not object:
            self.report({'ERROR'}, "No active object to operate on")
            return {'CANCELLED'}

        particle_system_index = object.particle_systems.active_index

        object_eval = object.evaluated_get(depsgraph)
        particle_system_eval = object_eval.particle_systems[particle_system_index]

        mesh_object = hair_to_mesh(context, object_eval, particle_system_eval)

        return {'FINISHED'}

class HAIR_PT_rig(Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "particle"
    bl_label = "Hair Rig"

    @classmethod
    def poll(cls, context):
        engine = context.engine
        return context.particle_system

    def draw(self, context):
        layout = self.layout
        layout.operator("hair.hair_to_mesh")


################################################################################
# Registration

def register():
    register_class(HAIR_OT_hair_to_mesh)
    register_class(HAIR_PT_rig)


def unregister():
    unregister_class(HAIR_OT_hair_to_mesh)
    unregister_class(HAIR_PT_rig)

if __name__ == "__main__":
    register()
