class ID:
	def __init__(self):
		self.name = ""
		self.custom_properties = {}

	def __str__(self):
		return self.name

	def make_real(self, target):
		for prop in self.__dict__.keys():
			if hasattr(target, prop):
				if( type(getattr(prop) == bpy.prop.collection)): continue
				setattr(target, prop, getattr(self, prop))