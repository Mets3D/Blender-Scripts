import bpy
from . import utils
from bpy.props import *

class SetupActionConstraints(bpy.types.Operator):
	""" Automatically manage action constraints of one action on all bones in an armature. """
	bl_idname = "armature.setup_action_constraints"
	bl_label = "Setup Action Constraints"
	bl_options = {'REGISTER', 'UNDO'}
	
	transform_channel: EnumProperty(name="Transform Channel",
		items=[("LOCATION_X", "X Location", "X Location"),
				("LOCATION_Y", "Y Location", "Y Location"),
				("LOCATION_Z", "Z Location", "Z Location"),
				("ROTATION_X", "X Rotation", "X Rotation"),
				("ROTATION_Y", "Y Rotation", "Y Rotation"),
				("ROTATION_Z", "Z Rotation", "Z Rotation"),
				("SCALE_X", "X Scale", "X Scale"),
				("SCALE_Y", "Y Scale", "Y Scale"),
				("SCALE_Z", "Z Scale", "Z Scale")
				],
		description="Transform channel",
		default="LOCATION_X")

	target_space: EnumProperty(name="Transform Space",
		items=[("WORLD", "World Space", "World Space"),
		("POSE", "Pose Space", "Pose Space"),
		("LOCAL_WITH_PARENT", "Local With Parent", "Local With Parent"),
		("LOCAL", "Local Space", "Local Space")
		],

		default="LOCAL"
	)

	frame_start: IntProperty(name="Start Frame")
	frame_end: IntProperty(name="End Frame",
		default=2)
	trans_min: FloatProperty(name="Min",
		default=-0.05)
	trans_max: FloatProperty(name="Max",
		default=0.05)
	target: StringProperty(name="Target")
	subtarget: StringProperty(name="String Property")
	action: StringProperty(name="Action")

	enabled: BoolProperty(name="Enabled", default=True)


	@classmethod
	def poll(cls, context):
		return context.object.type == 'ARMATURE' and context.object.mode in ['POSE', 'OBJECT']
	
	def execute(self, context):
		# Options
		armature = context.object
		target = None
		if(self.target!=""):
			target = context.scene.objects[self.target]
		else:
			target = armature
		action = bpy.data.actions[self.action]
		constraint_name = "Action_" + action.name.replace("Rain_", "")

		# Getting a list of pose bones on the active armature corresponding to the selected action's keyframes
		bones = []
		for fc in action.fcurves:
			# Extracting bone name from fcurve data path
			if("pose.bones" in fc.data_path):
				bone_name = fc.data_path.split('["')[1].split('"]')[0]
				bone = armature.pose.bones.get(bone_name)
				if(bone and bone not in bones):
					bones.append(bone)

		# Adding or updating Action constraint on the bones
		for b in bones:
			c = utils.find_or_create_constraint(b, 'ACTION', constraint_name)	# TODO: Hard coded action naming convention.
			c.target_space = self.target_space
			c.transform_channel = self.transform_channel
			c.target = target
			c.subtarget = self.subtarget
			c.action = action
			c.min = self.trans_min
			c.max = self.trans_max
			c.frame_start = self.frame_start
			c.frame_end = self.frame_end
			c.mute = not self.enabled

		# Deleting superfluous action constraints, if any
		for b in armature.pose.bones:
			for c in b.constraints:
				if(c.type=='ACTION'):
					# If the constraint targets this action but its name is wrong
					if(c.action == action):
						if(c.name != constraint_name):
							b.constraints.remove(c)
							continue
					# If the constraint is fine, but there is no associated keyframe
					if(c.name == constraint_name):
						if(b not in bones):
							b.constraints.remove(c)
							continue
					# Any action constraint with no action
					if(c.action == None):
						b.constraints.remove(c)
						continue
					# Warn for action constraint with suspicious names
					if(c.name == "Action" or ".00" in c.name):
						print("Warning: Suspicious action constraint on bone: " + b.name + " constraint: " + c.name )

		return { 'FINISHED' }

	def invoke(self, context, event):
		# When the operation is invoked, set the operator's target and action based on the context. If they are found, find the first bone with this action constraint, and pre-fill the operator settings based on that constraint.
		wm = context.window_manager
		self.target = context.object.name
		
		action = context.object.animation_data.action
		self.action = action.name

		if(action and context.object.type=='ARMATURE'):
			done = False
			for b in context.object.pose.bones:
				for c in b.constraints:
					if(
							c.type == 'ACTION' 
							and c.action.name == self.action ):
						self.subtarget = c.subtarget
						self.frame_start = c.frame_start
						self.frame_end = c.frame_end
						self.trans_min = c.min
						self.trans_max = c.max
						self.enabled = not c.mute

						self.target_space = c.target_space
						self.transform_channel = c.transform_channel
						done=True
						print("Updated operator values...")
						break
				if(done): break

		return wm.invoke_props_dialog(self)
	
	def draw(self, context):
		layout = self.layout
		layout.prop(self, "enabled", text="Enabled")

		layout.prop_search(self, "target", context.scene, "objects", text="Target")
		layout.prop_search(self, "subtarget", context.object.data, "bones", text="Bone")
		layout.prop_search(self, "action", bpy.data, "actions", text="Action")

		action_row = layout.row()
		action_row.prop(self, "frame_start", text="Start")
		action_row.prop(self, "frame_end", text="End")

		trans_row = layout.row()
		trans_row.use_property_decorate = False
		trans_row.prop(self, "target_space")
		trans_row.prop(self, "transform_channel")

		trans_row2 = layout.row()
		trans_row2.prop(self, "trans_min")
		trans_row2.prop(self, "trans_max")

def register():
	from bpy.utils import register_class
	register_class(SetupActionConstraints)

def unregister():
	from bpy.utils import unregister_class
	unregister_class(SetupActionConstraints)