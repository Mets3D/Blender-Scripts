import bpy
from .id import *

# Container and utilities for storing Driver data and creating Drivers.

class Driver(ID):
	def __init__(self):
		super().__init__()
		self.expression = ""
		self.variables = []
		self.use_self = False
		self.type = ['SCRIPTED', 'AVERAGE', 'SUM', 'MIN', 'MAX'][0]

	def make_var(self, name):
		new_var = DriverVariable(name)
		self.variables.append(new_var)
		return new_var

	def make_real(self, target, data_path, index=-1):
		"""Add this driver to a property."""
		assert hasattr(target, "driver_add"), "Target does not have driver_add(): " + str(target)
		driver_removed = target.driver_remove(data_path, index)
		BPY_fcurve = target.driver_add(data_path, index)
		BPY_driver = BPY_fcurve.driver

		super().make_real(BPY_driver)

		for v in self.variables:
			v.make_real(BPY_driver)

class DriverVariable(ID):
	def __init__(self, name="var"):
		super().__init__()
		self.targets = [DriverVariableTarget()] * 2
		self.name = name
		self.type = ['SINGLE_PROP', 'TRANSFORMS', 'ROTATION_DIFF', 'LOC_DIFF'][0]
	
	def make_real(self, BPY_driver):
		"""Add this variable to a driver."""
		BPY_d_var = BPY_driver.variables.new()
		super().make_real(BPY_d_var)
		for i, t in enumerate(self.targets):
			t.make_real(BPY_d_var, i)

class DriverVariableTarget(ID):
	def __init__(self):
		super().__init__()
		self.id_type = 'OBJECT'
		self.id = None
		self.bone_target = ""
		self.transform_type = 'ROT_X'
		self.transform_space = 'LOCAL_SPACE'
		self.rotation_mode = 'AUTO'

	def make_real(self, BPY_variable, index):
		"""Set this target on a variable."""
		skip = []
		if BPY_variable.type != 'SINGLE_PROP':
			skip = ['id_type']
		if len(BPY_variable.targets) > index:
			super().make_real(BPY_variable.targets[index], skip)
		else:
			pass