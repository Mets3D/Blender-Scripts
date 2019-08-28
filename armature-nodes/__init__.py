# Contributor(s): Demeter Dzadik (demeterdzadik@gmail.com)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
		"name": "Armature Nodes",
		"description": "Create a node tree to generate a control armature.",
		"author": "Demeter Dzadik",
		"version": (1, 0),
		"blender": (2, 81, 0),
		"location": "Properties > Armature > Nodes",
		"wiki_url": "http://my.wiki.url",   # TODO
		"tracker_url": "http://my.bugtracker.url", # TODO
		"support": "COMMUNITY",
		"category": "Rigging"
		}

import bpy

from . import auto_load
auto_load.init()
from . import armature_nodetree

def register():
	auto_load.register()
	print("Registered Armature Nodes")

def unregister():
	auto_load.unregister()
	armature_nodetree.unregister_manual()
	print("Unregistered Armature Nodes")