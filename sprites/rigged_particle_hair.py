import bpy
################################################################################
# Script written initially by Sergey Sharybin to bind hair particles to a proxy mesh.
# This is done because although hair particles cannot directly be rigged with an armature, the proxy mesh can.
# So this allows the particle hair to be rigged with an armature, although indirectly.

# The hair object name string below should be replaced by each character's post-rig-generation script with the object name of the scalp objects.
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
        for hair_object in bpy.data.objects:
            if hair_object.name != hairname:
                continue
            if not hair_object.visible_get():
                continue

            for particle_system in hair_object.particle_systems:
                mesh_object_name = hair_object.name + "-" + particle_system.name
                for mesh_object in bpy.data.objects:
                    if mesh_object.name != mesh_object_name:
                        continue
                    if not mesh_object.visible_get():
                        continue

                    mesh_object_eval = mesh_object.evaluated_get(depsgraph)
                    mesh_to_hair(depsgraph, mesh_object_eval, hair_object, particle_system)

def render_pre(scene):
    for hairname in hair_object_names:
        hair_object = bpy.data.objects.get(hairname)
        if not hair_object.visible_get():
	        hair_object.hide_viewport = False
	        scene.collection.objects.link(hair_object)

def render_post(scene):
    for hairname in hair_object_names:
        hair_object = bpy.data.objects.get(hairname)
        if hair_object.name in scene.collection.objects:
	        scene.collection.objects.unlink(hair_object)

def mesh_to_hair_test_continuous():
    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_post_handler)
    bpy.app.handlers.frame_change_post.append(depsgraph_update_post_handler)
    bpy.app.handlers.render_pre.append(render_pre)
    bpy.app.handlers.render_post.append(render_post)

# TODO: Add a toggle to disable updating of the particle hair for the sake of grooming.

mesh_to_hair_test_continuous()