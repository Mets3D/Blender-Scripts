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

# The goal of this addon is to let us generate additional parts of the armature by taking in the current set of bones as the input.
# To do this, we implement a new nodegraph using the python API.
# The output node of this nodegraph takes a list of bones as its parameter, which should be created, and the rest of the nodegraph is responsible for generating this list of bones.
# For now for simplicity's sake, the nodegraph should only be executed by an operator which is explicitly called, but ideally this would have to be a live updated thing in the future, which would probably require a lot of optimization and low level implementation.
# Keeping it simple like this should let us implement something usable in just a few days!

# I think the code for some nodes could be generated.
# For example, nodes that get and set bone properties, would involve a lot of code duplication, so we could just set up a dummy python file with some keywords surrounded by <> that need to be filled in by some parameters in a generator, then we run basic replace functions over it to get the final .py file.

# Current folder structure:
# Maybe each folder can simply be a file instead. We should look at AnimationNodes.

# Initial goals: Build UI, let a node create a bone when node tree is manually executed.

from . import armature_nodetree
from . import armature_node_sockets
from . import node_test

def register():
    armature_node_sockets.register()
    node_test.register()
    armature_nodetree.register()

def unregister():
    armature_node_sockets.unregister()
    node_test.unregister()
    armature_nodetree.unregister()

if __name__ == "__main__":
    register()