
def transfer_rig_data(object_dict: Dict[bpy.types.Object, bpy.types.Object]):
	""" Transfer vertex weights, shape keys, modifiers, drivers
		from one set of objects to another.
	"""

	for obj_from in object_dict.keys():
		obj_to = object_dict[obj_from]

		assert obj_from.type == obj_to.type, f"Error: Object Type mismatch: {obj_from.name}: {obj_from.type}, {obj_to.name}: {obj_to.type}"

		print(f"Transferring rig data from {obj_from.name} to {obj_to.name}")

		if obj_from.type=='ARMATURE':
			# Let's try nuking the bones of obj_to, then merging a duplicate of obj_from into it.
			bpy.ops.object.mode_set(mode='OBJECT')
			bpy.context.view_layer.objects.active = obj_to
			bpy.ops.object.select_all(action='DESELECT')
			bpy.ops.object.mode_set(mode='EDIT')
			for eb in obj_to.data.edit_bones[:]:
				obj_to.data.edit_bones.remove(eb)
			bpy.ops.object.mode_set(mode='OBJECT')

			bpy.context.view_layer.objects.active = obj_from
			obj_from.select_set(True)
			print("duplicating " + obj_from.name)
			bpy.ops.object.duplicate()
			print("duplicated... " + bpy.context.view_layer.objects.active.name)

			bpy.context.view_layer.objects.active = obj_to
			obj_to.select_set(True)
			print("selecting "+obj_to.name)

			bpy.ops.object.join()
			print("joined... " + bpy.context.view_layer.objects.active.name)

		# Wipe constraints
		for c in obj_to.constraints[:]:
			obj_to.constraints.remove(c)

		# Copy constraints
		for c_from in obj_from.constraints:
			c_to = obj_to.constraints.copy(c_from)
			if hasattr(c_to, 'target') and c_to.target and \
				c_to.target.type!='ARMATURE' and c_to.target in object_dict:
				c_to.target = object_dict[c_to.target]

		# Wipe modifiers
		for m in obj_to.modifiers[:]:
			obj_to.modifiers.remove(m)

		# Copy modifiers
		for m_from in obj_from.modifiers:
			m_to = obj_to.modifiers.new(type=m_from.type, name=m_from.name)
			copy_attributes(m_from, m_to)
			# Physics attributes
			if hasattr(m_from, 'settings'):
				copy_attributes(m_from.settings, m_to.settings)
			
			if hasattr(m_to, 'target') and m_to.target and \
				m_to.target.type!='ARMATURE' and m_to.target in object_dict:
				m_to.target = object_dict[m_to.target]

			# TODO: Multires data, binding data...

		# Rest of the code only applies to meshes.
		if obj_from.type != 'MESH': continue

		# Wipe vertex groups
		for vg in obj_to.vertex_groups[:]:
			obj_to.vertex_groups.remove(vg)

		# Copy vertex groups
		for vg_from in obj_from.vertex_groups:
			vg_to = obj_to.vertex_groups.new(name=vg_from.name)

		# Copy vertex weights
		if len(obj_to.data.vertices)==len(obj_from.data.vertices):
			# Transfer weights by vertex index
			for v in obj_from.data.vertices:
				for vg in obj_from.vertex_groups:
					w = 0
					try:
						w = vg.weight(v.index)
					except:
						pass
					if w==0: continue
					vg_to = obj_to.vertex_groups.get(vg.name)
					vg_to.add([v.index], w, 'REPLACE')
		else:
			# Transfer weights with data transfer operator. TODO
			pass

		# Update shape keys.
		if len(obj_to.data.vertices)==len(obj_from.data.vertices) and \
			obj_from.data.shape_keys:
			# Update shape keys by vertex index
			for sk_from in obj_from.data.shape_keys.key_blocks:
				sk_to = None
				if obj_to.data.shape_keys:
					sk_to = obj_to.data.shape_keys.key_blocks.get(sk_from.name)
				if not sk_to:
					sk_to = obj_to.shape_key_add(name=sk_from.name)

				for i, v in enumerate(sk_from.data):
					sk_to.data[i].co = v.co
		else:
			# Do something fancy... (surface deform?)
			print(f"WARNING: MISMATCHING VERTEX COUNTS ON {obj_from.name}. CANNOT TRANSFER SHAPE KEYS.")
			pass

		# Wipe drivers
		wipe_drivers(obj_to)
		wipe_drivers(obj_to.data)
		wipe_drivers(obj_to.data.shape_keys)

		# Copy drivers
		# copy_drivers(obj_from, obj_to)
		# copy_drivers(obj_from.data, obj_to.data)
		# copy_drivers(obj_from.data.shape_keys, obj_to.data.shape_keys)

def copy_drivers(from_db, to_db):
	if not hasattr(from_db, 'animation_data') \
		or not from_db.animation_data: 
		return
	
	for d in from_db.animation_data.drivers:
		to_db.driver_add(d.data_path)


def wipe_drivers(datablock):
	if not hasattr(datablock, 'animation_data') \
		or not datablock.animation_data: 
		return
	
	for d in datablock.animation_data.drivers:
		datablock.animation_data.drivers.remove(d)

def copy_attributes(a, b):
	keys = dir(a)
	for key in keys:
		if not key.startswith("_") \
		and not key.startswith("error_") \
		and key not in ["group", "is_valid", "rna_type", "bl_rna"]:
			try:
				setattr(b, key, getattr(a, key))
			except AttributeError:
				pass

def cleanup_rig_transfer(context):
	settings = context.scene.character_update_settings
	ch_name = settings.ch_name

	# Delete rig collection
	coll = bpy.data.collections['CH-'+ch_name+'.rig']
	coll.user_clear()
	bpy.data.collections.remove(coll)

	# Purge orphan data
	for i in range(7): bpy.ops.outliner.orphans_purge()

	# Remove .old from end of collection names
	for coll in bpy.data.collections:
		if coll.name.endswith('.old'):
			coll.name = coll.name[:-4]
	
	# Remove .old from end of object names
	for obj in bpy.data.objects:
		if obj.name.endswith('.old'):
			obj.name = obj.name[:-4]
			if obj.data != None:
				obj.data.name = obj.data.name[:-4]

	# Run additional update script if provided.
	# if settings.text_script:
	# 	exec(settings.text_script.as_string(), {})