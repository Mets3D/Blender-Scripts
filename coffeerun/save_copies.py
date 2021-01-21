import bpy, os

# Save copies of this blend file under different names. Add extra renaming/processing/saving params as needed.

copies = 5  # Excluding self.

def get_collections():
    ret = []
    for c in bpy.data.collections:
        if c.name.startswith("CH-") or c.name.startswith("PR-"):
            ret.append(c)
    return ret

def get_rigs():
    ret = []
    for c in bpy.data.objects:
        if c.name.startswith("RIG-"):
            ret.append(c)
    return ret

def get_node_groups():
    ret = []
    for c in bpy.data.node_groups:
        if c.name.startswith("VA-"):
            ret.append(c)
    return ret

for i in range(0, copies):
    suffix = ".%d"%i
    for c in get_collections():
        if i > 0:
            c.name = "".join(c.name.split(".")[:-1])
        c.name = c.name + suffix
        
    for r in get_rigs():
        if i > 0:
            r.name = "".join(r.name.split(".")[:-1])
        r.name = r.name + suffix
        
    for n in get_node_groups():
        if i > 0:
            n.name = "".join(n.name.split(".")[:-1])
        n.name = n.name + suffix

    filepath = bpy.data.filepath.replace(".blend", ".%d.blend"%i)
    bpy.ops.wm.save_as_mainfile(filepath=filepath, copy=True)