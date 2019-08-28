from bpy.types import Node

# Armature Node Base Class
class ArmatureNode(Node):
	@classmethod
	def poll(cls, ntree):
		if(not super().poll(ntree)):
			return False
		return ntree.bl_idname == 'ArmatureNodeTree'
	
	# Called by the Generate Armature operator.
	def execute(self, context):
		for i in self.inputs:
			for l in i.links:
				from_node = l.from_node
				from_node.execute(context)
		return