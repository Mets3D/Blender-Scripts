import bpy

print("START")
print("")

data_paths = {"": []} # Dictionary of data path to list of indices.

for d in bpy.context.object.animation_data.drivers:
	# Duplicate checking - A driver is a duplicate of another if they have the same data path and array index.
	if d.data_path in data_paths:
		if d.array_index in data_paths[d.data_path]:
			print("Duplicate driver: %s, index %s" %(d.data_path, d.array_index))
			d.data_path="DUPLICATE"
			continue
		else:
			data_paths[d.data_path].append(d.array_index)
	else:
		data_paths[d.data_path] = [d.array_index]
	
	if len(d.driver.variables)==0:
		print("Driver with no variables: %s" %(d.data_path))
		continue
	if "ORG" in d.driver.variables[0].targets[0].data_path:
		print("Driver with ORG: %s" %(d.data_path))
		print(d.driver.variables[0].targets[0].data_path)
		d.data_path = "ORG TRASH"