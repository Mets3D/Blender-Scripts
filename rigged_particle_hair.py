import bpy

################################################################################
# Script written initially by Sergey Sharybin to bind hair particles to a proxy mesh.
# This is done because although hair particles cannot directly be rigged with an armature, the proxy mesh can.
# So this allows the particle hair to be rigged with an armature, although indirectly.

# The "HAIR_OBJECT_NAME" below should be replaced by each character's post-rig-generation script with the object name of the scalp objects.
hair_object_names = ["HAIR_OBJECT_NAME"]

def find_modifier_for_particle_system(object, particle_system):
    for modifier in object.modifiers:
        if modifier.type != "PARTICLE_SYSTEM":
            continue
        if modifier.particle_system == particle_system:
            return modifier
    return None

def mesh_to_hair(depsgraph, mesh_object, hair_object, particle_system):
    particle_modifier = find_modifier_for_particle_system(hair_object, particle_system)

    hair_object_eval = hair_object.evaluated_get(depsgraph)
    particle_modifier_eval = hair_object_eval.modifiers[particle_modifier.name]
    particle_system_eval = particle_modifier_eval.particle_system

    mesh = mesh_object.data
    vertices = mesh.vertices

    num_particles = len(particle_system.particles)
    vertex_index = 0
    for particle_index in range(num_particles):
        particle = particle_system.particles[particle_index]
        particle_eval = particle_system_eval.particles[particle_index]
        num_hair_keys = len(particle_eval.hair_keys)
        for hair_key_index in range(num_hair_keys):
            co = vertices[vertex_index].co
            hair_key = particle.hair_keys[hair_key_index]
            hair_key.co_object_set(hair_object_eval, particle_modifier_eval, particle_eval, co)
            vertex_index += 1


def depsgraph_update_post_handler(scene, depsgraph):
    global hair_object_names
    for hairname in hair_object_names:
        hair_object = bpy.data.objects.get(hairname)
        if not hair_object:
            print("ERROR: Hair object not found: " + hairname)
            continue
        if not hair_object.visible_get(): return
        
        for particle_system in hair_object.particle_systems:
            mesh_object = bpy.data.objects.get(hair_object.name + "-" + particle_system.name)
            if not mesh_object:
                continue

            mesh_object_eval = mesh_object.evaluated_get(depsgraph)
            mesh_to_hair(depsgraph, mesh_object_eval, hair_object, particle_system)

def mesh_to_hair_test_continuous():
    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_post_handler)
    bpy.app.handlers.frame_change_post.append(depsgraph_update_post_handler)


# TODO: Add a toggle to disable updating of the particle hair for the sake of grooming.

if False:
    # If the hair objects are linked, we must make them local and add a "library" custom property to keep track of where it was linked from.
    for hairname in hair_object_names:
        hair_object = bpy.data.objects.get(hairname)
        if not hair_object: continue

        # If hair object is linked and/or overridden, make it local and save the library as a custom property for subsequent executions.
        if hair_object.library or hair_object.override_library:
            library = hair_object.library
            if not library:
                library = hair_object.override_library.reference.library
            local_object = hair_object.make_local()
            local_object['library'] = library

        # If the hair object is local, it is expected to have a 'library' custom property.
        # The hair object should be deleted, linked from this library, then overridden again.
        else:
            library = hair_object['library']
            
            # https://docs.blender.org/api/current/bpy.types.BlendDataLibraries.html
            # the loaded objects can be accessed from 'data_to' outside of the context
            # since loading the data replaces the strings for the datablocks or None
            # if the datablock could not be loaded.

            with bpy.data.libraries.load(library.filepath) as (data_from, data_to):
                data_to.objects = [hairname]



# If they are local but have a "library" custom property, they should be linked and made local again.

mesh_to_hair_test_continuous()

