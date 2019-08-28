import bpy
from bpy.types import NodeTree
import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem

# Derived from the NodeTree base type, similar to Menu, Operator, Panel, etc.
class ArmatureNodeTree(NodeTree):
	'''Node Tree for generating armatures.'''
	bl_idname = 'ArmatureNodeTree'
	bl_label = "Armature Node Editor"
	bl_icon = 'NODETREE'

### Node Categories ###
# Node categories are a python system for automatically
# extending the Add menu, toolbar panels and search operator.
# For more examples see release/scripts/startup/nodeitems_builtins.py

class MyNodeCategory(NodeCategory):
	@classmethod
	def poll(cls, context):
		return context.space_data.tree_type == 'ArmatureNodeTree'

# all categories in a list
node_categories = [
	# identifier, label, items list
	MyNodeCategory('ARMATURE_OUTPUT_NODES', "Output", items=[
		NodeItem("arn_ArmatureOutputNode"),
	]),
]

def register():
	nodeitems_utils.register_node_categories('ARMATURE_NODES', node_categories)

def unregister_manual():
	nodeitems_utils.unregister_node_categories('ARMATURE_NODES')