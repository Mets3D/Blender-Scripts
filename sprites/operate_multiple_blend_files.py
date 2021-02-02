# Do something in multiple blend files. Useful for changing rig settings on all character rigs, or regenerating all characters when we are confident it will not break anything.

import bpy
from bpy.app.handlers import persistent

save = True

def eye_update():
    from rigify.feature_sets.CloudRig.cloud_generator import generate_rig
    # Find one metarig
    metarig = None
    for o in bpy.data.objects:
        if o.name.startswith('META'):
            metarig = o
            break
    
    # Set eye parameters
    for pb in metarig.pose.bones:
        if pb.rigify_type=='cloud_aim':
            pb.rigify_parameters.CR_aim_flatten = False
            pb.rigify_parameters.CR_aim_eye_highlight = True
    
    # Regenerate
    global save
    try:
        generate_rig(bpy.context, metarig)
    except:
        save = False

def rig_pull():
    bpy.ops.char_pipeline.update_rig()

@persistent
def load_handler(dummy):
    rig_pull()

bpy.app.handlers.load_post.append(load_handler)

# TODO: open all character files and pull the rig

rigging_files = [
    "pro/lib/char/rex/rex.rigging.blend"
    ,"pro/lib/char/victoria/victoria.rigging.blend"
    ,"pro/lib/char/ellie/ellie.rigging.blend"
    ,"pro/lib/char/jay/jay.rigging.blend"
    ,"pro/lib/char/phil/phil.rigging.blend"

    ,"pro/lib/char/sprite/sprite.rigging.blend"
]

character_files = [
    "pro/lib/char/rex/rex.blend"
    ,"pro/lib/char/victoria/victoria.blend"
    # ,"pro/lib/char/ellie/ellie.blend"
    ,"pro/lib/char/jay/jay.blend"
    ,"pro/lib/char/phil/phil.blend"

    ,"pro/lib/char/sprite/sprite.blend"

]

filepath_start = "/home/guest/SVN/SpriteFright/"
files = character_files

for filepath in files:
    # Reset save flag
    save = True
    # Open the file
    bpy.ops.wm.open_mainfile(filepath=filepath_start+filepath)
    if save:
        bpy.ops.wm.save_mainfile()

bpy.app.handlers.load_post.remove(load_handler)