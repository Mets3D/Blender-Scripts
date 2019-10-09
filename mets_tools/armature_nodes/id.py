import bpy

class ID:
	def __init__(self):
		self.name = ""
		self.custom_properties = {}

	def __str__(self):
		return self.name

	def make_real(self, target, skip=[]):
		for prop in self.__dict__.keys():
			if hasattr(target, prop):
				if "bpy_prop_" in str(type(getattr(target, prop))) : continue
				if prop in skip: continue
				setattr(target, prop, getattr(self, prop))