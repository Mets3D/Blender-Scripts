import bpy

#########################################################
# TODO
# - implement exceptions
# - fix accumulation of python scripts
# - expand usability for character.modeling.blend
#   -> (transfer more data: weight maps, modifiers, etc.)
#########################################################

def col_rename(col, suf = '.tmp'):
    if col != None: 
        for el in col:
            el.name = el.name+suf
            col_rename(el.children, suf)
        return col
    return None

def suffix_hierarchy(col, suffix='.tmp'):
    
    obj_tmp = col.all_objects
    for obj in obj_tmp:
        obj.name = obj.name+suffix
        if obj.data != None:
            obj.data.name = obj.data.name+suffix
    col_rename([col], suf=suffix)
    return obj_tmp
    

def setup_update_shading():
    ch_name = bpy.context.scene.character_update_settings.ch_name
    
    col = bpy.data.collections['CH-'+ch_name]
    
    obj_rig = suffix_hierarchy(col, suffix='.rig')
    
    for mat in bpy.data.materials:
        mat.name = mat.name+'.rig'
    for grp in bpy.data.node_groups:
        grp.name = grp.name+'.rig'
    
    bpy.ops.wm.append(directory=bpy.path.abspath('//'+ch_name+'.shading.blend')+'\\Collection\\', filename='CH-'+ch_name, active_collection=False)
    
    col = bpy.data.collections['CH-'+ch_name]
    
    obj_mat = suffix_hierarchy(col, suffix='.mat')
    
    return obj_mat, obj_rig

def setup_update_rig():
    ch_name = bpy.context.scene.character_update_settings.ch_name
    
    col = bpy.data.collections['CH-'+ch_name]
    
    obj_mat = suffix_hierarchy(col, suffix='.mat')
    
    bpy.ops.wm.append(directory=bpy.path.abspath('//'+ch_name+'.rig.blend')+'\\Collection\\', filename='CH-'+ch_name, active_collection=False)
    
    col = bpy.data.collections['CH-'+ch_name]
    
    obj_rig = suffix_hierarchy(col, suffix='.rig')
    return obj_mat, obj_rig



def setup_update_all():
    ch_name = bpy.context.scene.character_update_settings.ch_name
    
    col = bpy.data.collections['CH-'+ch_name]
    col.user_clear()
    bpy.data.collections.remove(col)
    
    for i in range(6): bpy.ops.outliner.orphans_purge()
    
    bpy.ops.wm.append(directory=bpy.path.abspath('//'+ch_name+'.rig.blend')+'\\Collection\\', filename='CH-'+ch_name, active_collection=False)
    
    col = bpy.data.collections['CH-'+ch_name]
    
    obj_rig = suffix_hierarchy(col, suffix='.rig')
    
    bpy.ops.wm.append(directory=bpy.path.abspath('//'+ch_name+'.shading.blend')+'\\Collection\\', filename='CH-'+ch_name, active_collection=False)
    
    col = bpy.data.collections['CH-'+ch_name]
    
    obj_mat = suffix_hierarchy(col, suffix='.mat')
    
    return obj_mat, obj_rig

def transfer(obj_mat, obj_rig, imp_mat=True, imp_uv=True, imp_vcol=True):

    print(obj_mat.keys())

    for obj in obj_rig:
        if obj.name[:-4]+'.mat' not in obj_mat.keys():
            print('%s not found'%(obj.name[:-4]))
            continue
        if obj.data != None:
            obj_ref = obj_mat[obj.name[:-4]+'.mat']
            for idx, m_slot in enumerate(obj.material_slots):
                m_slot.material = obj_ref.material_slots[idx].material
            if imp_uv:
                if obj.type == 'MESH':
                    for uv_layer_ref in obj_ref.data.uv_layers:
                        if not uv_layer_ref.name in obj.data.uv_layers:
                            uv_layer = obj.data.uv_layers.new(name = uv_layer_ref.name, do_init = False)
                        else:
                            uv_layer = obj.data.uv_layers[uv_layer_ref.name]
                        for loop in obj.data.loops:
                            try:
                                uv_layer.data[loop.index].uv = uv_layer_ref.data[loop.index].uv
                            except:
                                print('no UVs transferred for %s'%(obj.name))
                                pass #TODO: This triggers when a mesh gets new vertices in the rig file.
            
            if imp_vcol:
                if obj.type == 'MESH':
                    for vcol_ref in obj_ref.data.vertex_colors:
                        if not vcol_ref.name in obj.data.vertex_colors:
                            vcol = obj.data.vertex_colors.new(name = vcol_ref.name)
                        else:
                            vcol = obj.data.vertex_colors[vcol_ref.name]
                        for loop in obj.data.loops :
                            try:
                                vcol.data[loop.index].color = vcol_ref.data[loop.index].color
                            except:
                                print('no Vertex Colors transferred for %s'%(obj.name))
                                pass #TODO: This triggers when a mesh gets new vertices in the rig file.
        
    return

def cleanup():
    ch_name = bpy.context.scene.character_update_settings.ch_name
    
    col = bpy.data.collections['CH-'+ch_name+'.mat']
    col.user_clear()
    bpy.data.collections.remove(col)
    
    for i in range(6): bpy.ops.outliner.orphans_purge()
    
    for col in bpy.data.collections:
        if col.name.endswith('.rig'):
            col.name = col.name[:-4]
    
    for obj in bpy.data.objects:
        if obj.name.endswith('.rig'):
            obj.name = obj.name[:-4]
            if obj.data != None:
                obj.data.name = obj.data.name[:-4]
            
    for col in bpy.data.collections:
        if col.name.startswith('rig_'):
            col.hide_viewport = True

    drivers_to_relink = []

    for grp in bpy.data.node_groups:
        if grp.name.startswith('DR-'):
            name = grp.name[3:]
            if not grp.animation_data: continue
            for d in grp.animation_data.drivers:
                drivers_to_relink.append(d.driver)
    
    for m in bpy.data.materials:
        if not m.animation_data: continue
        for d in m.animation_data.drivers:
            drivers_to_relink.append(d.driver)

    # If any variable targets have no target object, set the rig as the target object.
    for d in drivers_to_relink:
        for v in d.variables:
            for t in v.targets:
                if t.id_type=='OBJECT' and t.id==None:
                    t.id = bpy.data.objects[name]
        d.type = d.type

class CharacterUpdateSettings(bpy.types.PropertyGroup):
    imp_mat : bpy.props.BoolProperty(
        name = 'Materials',
        description = '',
        default = True,
        )
    imp_uv : bpy.props.BoolProperty(
        name = 'UVs',
        description = '',
        default = True,
        )
    imp_vcol : bpy.props.BoolProperty(
        name = 'Vertex Colors',
        description = '',
        default = True,
        )
        
    name = ''
    filename = bpy.path.basename(bpy.context.blend_data.filepath)
    for l in filename:
        if l == '.': break
        name += l
    
    ch_name : bpy.props.StringProperty(
        name = 'Character Name',
        default = name,
        )


class CharacterUpdate_UpdateShading(bpy.types.Operator):
    bl_idname = "char_update.update_shading"
    bl_label = "Update Shading"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        settings = context.scene.character_update_settings
        
        args = setup_update_shading()
        transfer(*args, imp_mat=settings.imp_mat, imp_uv=settings.imp_uv, imp_vcol=settings.imp_vcol)
        cleanup()
        
        return {'FINISHED'}

class CharacterUpdate_UpdateRig(bpy.types.Operator):
    bl_idname = "char_update.update_rig"
    bl_label = "Update Rig"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        settings = context.scene.character_update_settings
        
        args = setup_update_rig()
        transfer(*args, imp_mat=settings.imp_mat, imp_uv=settings.imp_uv, imp_vcol=settings.imp_vcol)
        cleanup()
        
        return {'FINISHED'}

class CharacterUpdate_UpdateAll(bpy.types.Operator):
    bl_idname = "char_update.update_all"
    bl_label = "Update All"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        settings = context.scene.character_update_settings
        
        args = setup_update_all()
        transfer(*args, imp_mat=settings.imp_mat, imp_uv=settings.imp_uv, imp_vcol=settings.imp_vcol)
        cleanup()
        
        return {'FINISHED'}
    
    

class CharacterUpdatePanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Character Update"
    bl_idname = "VIEW3D_PT_character_update"
    bl_category = 'Item'

    def draw(self, context):
        layout = self.layout
        
        settings = context.scene.character_update_settings
        
        layout.prop(settings, 'ch_name')
        
        col = layout.column()

        #row = col.row()
        #row.prop(settings, 'imp_mat')
        row = col.row()
        row.prop(settings, 'imp_uv')
        row = col.row()
        row.prop(settings, 'imp_vcol')
        
        row = col.row()        
        row.operator("char_update.update_shading", icon='SHADING_RENDERED', text="Update Shading")
        row = col.row()
        row.operator("char_update.update_rig", icon='OUTLINER_OB_ARMATURE', text="Update Rig & Mesh")
        row = col.row()
        row.operator("char_update.update_all", text="Update All")
        
def ensure_rig_hidden(context, scene):
    for c in bpy.data.collections:
        if c.name.startswith("rig_"):
            c.hide_viewport=True        

classes = (
    CharacterUpdateSettings,
    CharacterUpdate_UpdateShading,
    CharacterUpdate_UpdateRig,
    CharacterUpdate_UpdateAll,
    CharacterUpdatePanel,
)
    
def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.character_update_settings = bpy.props.PointerProperty(type=CharacterUpdateSettings)
    bpy.app.handlers.save_pre.append(ensure_rig_hidden)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
        bpy.app.handlers.save_pre.remove(ensure_rig_hidden)

register()