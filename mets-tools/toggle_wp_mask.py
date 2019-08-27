import bpy
from bpy.props import *

class ToggleWeightPaintMask(bpy.types.Operator):
	""" Toggle last weight paint mask """
	bl_idname = "object.weight_paint_mask_toggle"
	bl_label = "Toggle Weight Paint Mode"
	bl_options = {'REGISTER'}

	action: EnumProperty(name="Action",
		items=[("TOGGLE_LAST", "Toggle Last", "Toggle Last"),
				("ENTER_FACE", "Enter Face", "Enter Face"),
				("ENTER_VERTEX", "Enter Vertex", "Enter Vertex"),
				("LEAVE", "Leave", "Leave")
				],
		description="Transform channel",
		default="TOGGLE_LAST")

	def execute(self, context):
		data = context.object.data

		if(self.action=='TOGGLE_LAST'):
			if(data.use_paint_mask_vertex or data.use_paint_mask):
				data['last_mask'] = 'vert' if data.use_paint_mask_vertex else 'face'
				data.use_paint_mask_vertex = False
				data.use_paint_mask = False
			else:
				if('last_mask' in data.keys()):
					if(data['last_mask'] == 'face'):
						data.use_paint_mask = True
					elif(data['last_mask'] == 'vert'):
						data.use_paint_mask_vertex = True
		elif(self.action=='ENTER_FACE'):
			data.use_paint_mask_vertex = False
			data.use_paint_mask = True
			data['last_mask'] = 'face'
		elif(self.action=='ENTER_FACE'):
			data.use_paint_mask_vertex = True
			data.use_paint_mask = False
			data['last_mask'] = 'vert'
		elif(self.action=='LEAVE'):
			if(data.use_paint_mask_vertex):
				data.use_paint_mask_vertex = False
				data['last_mask'] = 'vert'
			elif(data.use_paint_mask_face):
				data.use_paint_mask = False
				data['last_mask'] = 'face'

		return { 'FINISHED' }

def register():
	from bpy.utils import register_class
	register_class(ToggleWeightPaintMask)

def unregister():
	from bpy.utils import unregister_class
	unregister_class(ToggleWeightPaintMask)

register()