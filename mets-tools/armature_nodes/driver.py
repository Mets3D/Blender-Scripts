from .id import *

# Container and utilities for storing Driver data and creating Drivers.

class Driver(ID):
	def __init__(self):
		super().__init__()
		self.expression = ""
		self.variables = [DriverVariable()]
		self.use_self = False
		self.type = ['SCRIPTED', 'AVERAGE', 'SUM', 'MIN', 'MAX'][0]

	def make_real(self, target, data_path, index=-1):
		"""Add this driver to a property."""
		assert self.data_path != "", "No data path specified for driver." #TODO warning, not error.
		assert target.hasattr("driver_add"), "Target does not have driver_add(): " + str(target)
		driver_removed = target.driver_remove(data_path, index)
		fcurve = target.driver_add(data_path, index)
		driver = fcurve.driver

		super().make_real(driver)

		for v in self.variables:
			v.make_real(driver)

			d_var = driver.variables.new()
			v.make_real(d_var)

class DriverVariable(ID):
	def __init__(self):
		super().__init__()
		self.targets = []
		self.name = "var"
		self.type = ['SINGLE_PROP', 'TRANSFORMS', 'ROTATION_DIFF', 'LOC_DIFF'][0]
	
	def make_real(self, driver):
		"""Add this variable to a driver."""
		d_var = driver.variables.new()
		super().make_real(d_var)
		for i, t in enumerate(self.targets):
			t.make_real(d_var, i)

class DriverVariableTarget(ID):
	def __init__(self):
		super().__init__()
		self.type = ""
		self.id_type = 'OBJECT'
		self.id_data = None # ID
		self.bone_target = ''
		self.transform_type = 'ROT_X'
		self.transform_space = 'LOCAL_SPACE'
		self.rotation_mode = 'AUTO'

	def make_real(self, variable, index):
		"""Set this target on a variable."""
		super().make_real(variable.targets[index])
