import bpy

D = bpy.context.object.data.driver_add("vertex_colors.active_index")

driver = D.driver

driver.expression = "skin-1"
var = driver.variables.new()
var.type = 'SINGLE_PROP'
var.name = "skin"
var.targets[0].id = bpy.data.objects["RIG-Rain"]
var.targets[0].data_path = 'pose.bones["Properties_Outfit_Default"]["Skin"]'