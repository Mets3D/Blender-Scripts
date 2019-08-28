import bpy
from bpy.types import NodeTree
import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem

# Derived from the NodeTree base type, similar to Menu, Operator, Panel, etc.
class ArmatureNodeTree(NodeTree):
    '''Node Tree for generating armatures.'''
    bl_idname = 'ArmatureNodeTree'
    bl_label = "Armature Node Tree"
    bl_icon = 'NODETREE'

# Mix-in class for all custom nodes in this tree type.
# Defines a poll function to enable instantiation.
class MyCustomTreeNode:
    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'ArmatureNodeTree'

### Node Categories ###
# Node categories are a python system for automatically
# extending the Add menu, toolbar panels and search operator.
# For more examples see release/scripts/startup/nodeitems_builtins.py

# our own base class with an appropriate poll function,
# so the categories only show up in our own tree type

class MyNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ArmatureNodeTree'

# all categories in a list
node_categories = [
    # identifier, label, items list
    MyNodeCategory('SOMENODES', "Some Nodes", items=[
        # our basic node
        NodeItem("CustomNodeType"),
    ]),
    MyNodeCategory('OTHERNODES', "Other Nodes", items=[
        # the node item can have additional settings,
        # which are applied to new nodes
        # NB: settings values are stored as string expressions,
        # for this reason they should be converted to strings using repr()
        NodeItem("CustomNodeType", label="Node A", settings={
            "my_string_prop": repr("Lorem ipsum dolor sit amet"),
            "my_float_prop": repr(1.0),
        }),
        NodeItem("CustomNodeType", label="Node B", settings={
            "my_string_prop": repr("consectetur adipisicing elit"),
            "my_float_prop": repr(2.0),
        }),
    ]),
]

classes = (
    ArmatureNodeTree,
)

def register():
    from bpy.utils import register_class
    for c in classes:
        register_class(c)

    nodeitems_utils.register_node_categories('CUSTOM_NODES', node_categories)

def unregister():
    nodeitems_utils.unregister_node_categories('CUSTOM_NODES')

    from bpy.utils import unregister_class
    for c in reversed(classes):
        unregister_class(c)