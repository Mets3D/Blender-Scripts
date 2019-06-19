# Blender Witcher 3 Importer Add-on
# Copyright (C) 2019 MetsSFM
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

bl_info = {
	"name": "Witcher 3 FBX Import Tools",
	"author": "Mets3D",
	"version": (1, 0),
	"blender": (2, 80, 0),
	"location": "File->Import->Witcher 3 FBX",
	"description": "For importing Witcher 3 characters that were extracted by wcc_lite.exe.",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Object"}
	
import bpy
from bpy.props import *
from . import import_witcher3_fbx
from . import weighted_normals
from . import cleanup_mesh

class Witcher3AddonPrefs(bpy.types.AddonPreferences):
	# this must match the addon name, use '__package__'
	# when defining this in a submodule of a python package.
	bl_idname = __package__

	uncook_path: StringProperty(
		name="Uncook Path",
		subtype='DIR_PATH',
		default='E:\\Path_to_your_uncooked_folder\\Uncooked\\',
		description="Path to where you uncooked the game using wcc_lite.exe or another tool. Will be searching for .tga textures here."
	)

	def draw(self, context):
		layout = self.layout
		layout.label(text="Witcher 3 FBX Importer settings:")
		layout.prop(self, "uncook_path")

def register():
	import_witcher3_fbx.register()
	weighted_normals.register()
	cleanup_mesh.register()
	bpy.utils.register_class(Witcher3AddonPrefs)
	
def unregister():
	import_witcher3_fbx.unregister()
	weighted_normals.unregister()
	cleanup_mesh.unregister()
	bpy.utils.unregister_class(Witcher3AddonPrefs)