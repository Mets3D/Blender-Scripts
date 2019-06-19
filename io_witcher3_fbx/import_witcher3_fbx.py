# Blender Witcher 3 Importer Add-on
# Copyright (C) 2019 MetsSFM
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import bpy
import os
import bmesh
import xml.etree.ElementTree as ET
import sys
from mathutils import Vector
from mathutils import Euler
from math import pi
from bpy.props import *
from . import cleanup_mesh
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator

# TODO
# Idk where all the other TODOs went from here, maybe in the blend file.

# texarrays shouldn't be ignored, we can actually find them. They're in the root of the Uncooked folder!

class W3ImporterError(Exception):
	pass

def enable_print(bool):	
	# For suppressing prints from fbx importer and remove_doubles().
	if(not bool):
		sys.stdout = open(os.devnull, 'w')
	else:
		sys.stdout = sys.__stdout__

def readXML(xml_path):
	# Witcher 3 material info needs to be read from .xml files.
	with open(xml_path, 'r') as myFile:
		# Parsing the file directly doesn't work due to a bug in ET that rejects UTF-16, so we'll have to use fromstring().
		data=myFile.read()
		return ET.fromstring(data)

def append_resources():
	# Append Witcher 3 nodegroups from the .blend file of the addon.
	filename = "witcher3_materials.blend"
	filedir = os.path.dirname(os.path.realpath(__file__))
	blend_path = os.path.join(filedir, filename)
	
	with bpy.data.libraries.load(blend_path) as (data_from, data_to):
		for ng in data_from.node_groups:
			if(bpy.data.node_groups.get(ng) == None):
				data_to.node_groups.append(ng)

def order_elements_by_attribute(elements, order, attribute='name'):
	# Function that returns a list of Element objects ordered by the value of an attribute and an arbitrary order.
	# Used to order nodes so that more useful input nodes are at the top of the node graph, and misc nodes are at the bottom.
	ordered = []
	unordered = elements[:]
	for name in order:
		for p in elements:
			if(p.get('name')==name):
				ordered.append(p)
				if(p in unordered): 
					unordered.remove(p)
	ordered.extend(unordered)
	return ordered

def setup_w3_material(material, mat_data, obj):
	# Checks for duplicate materials
	# Saves XML data in custom properties
	# Creates nodes
	# Loads images
	# TODO: This function got really long, might want to split it up.
	addon_prefs = bpy.context.preferences.addons[__package__].preferences
	uncook_path = addon_prefs.uncook_path
	
	mat_base = mat_data.get('base')		# Path to the .w2mg or .w2mi file.
	params = {}
	for p in mat_data:
		params[p.get('name')] = p.get('value')
		
	# Setting blend mode
	material.blend_method = 'CLIP'
	
	shader_type = mat_base.split("\\")[-1][:-5]	# The .w2mg or .w2mi file, minus the extension.
	
	nodes = material.node_tree.nodes
	links = material.node_tree.links
	
	##########################
	### Duplicate checking ###
	##########################
	
	# Checking the custom properties that we created in previously imported materials
	for m in bpy.data.materials:
		if(#'Material' not in m.name and	# To avoid matching any previous failed imports. TODO delete if this is no longer needed.
		'witcher3_mat_params' in m and
		mat_base == m['witcher3_mat_base'] and
		params == m['witcher3_mat_params'].to_dict()):	# Comparing parameter dictionaries, this is the important part.
			return m
	
	# Backing up all the info from the XML into custom properties. This is used for duplicate checking.
	material['witcher3_mat_base'] = mat_base
	material['witcher3_mat_params'] = params
	
	###################################
	### Handling material instances ###
	###################################
	# The XML contains little to no info about these, but the FBX importer has imported some image nodes we can use.
	if(mat_base.endswith(".w2mi")):
		# Guesssing the shader type.
		if('hair' in shader_type):
			shader_type = 'pbr_hair'
		elif('skin' in shader_type):
			shader_type = 'pbr_skin'
		elif('eye' in shader_type):
			shader_type = 'pbr_eye'
		else:
			shader_type = 'pbr_std'
		
		# We will turn the nodes into params, so that the later code can process it like a normal material.
		# It may seem weird that we're deleting some nodes only to re-make them later, but these nodes aren't set up the way I want them, so this seems the cleanest way to do it.
		for n in material.node_tree.nodes:
			if(n.type == 'TEX_IMAGE'):
				# Since we want to compare this to what is in the .xml, we will replace the extension with .xbm.
				image_filename = n.image.filepath.split("\\")[-1].split(".")[0]+".xbm"
				
				# Check if this image is already a param
				found = False
				for param in mat_data:
					type = param.get('type')
					value = param.get('value')
					if(type != 'handle:ITexture' or value=='NULL' ): continue
					filename = value.split("\\")[-1]
					if(filename == image_filename):
						found = True
						# If the image is already a param in the XML file, we don't need to worry about it.
						break
				
				# If the image is not referenced by the XML file, it's time to turn the node into a param.
				if(not found):
					# Create a param and guessing the texture's type.
					new_param = ET.SubElement(mat_data, 'param')
					new_param.set('name', 'Unknown')
					new_param.set('type', 'handle:ITexture')
					
					# By the textures' naming conventions, there seem to be two places in the texture name that can tell us what type of texture it is:
					# some_texture_d.xbm	"d" is the 5th character from the back
					# some_texture_d01.xbm	"d" is the 7th character from the back
					letter = n.image.filepath[-5]
					
					if(letter in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']):
						letter = n.image.filepath[-7]
					
					if(letter == 'd'):
						new_param.set('name', 'Diffuse')
					elif(letter == 'n'):
						new_param.set('name', 'Normal')
					elif(letter == 's'):
						new_param.set('name', 'SpecularTexture')
					elif(letter == 'a'):
						if(shader_type == 'pbr_skin'):
							new_param.set('name', 'Ambient')
						else:
							new_param.set('name', 'TintMask')
					else:
						print("Could not guess texture type: " + image_filename + " (THIS SHOULD NOT HAPPEN!)")
					
					# The 'value' needs to be the texture path relative to the uncook folder.
					split_path = uncook_path.split("\\")
					uncook_folder_name = split_path[-1].lower()
					if(uncook_folder_name == ""):
						uncook_folder_name = split_path[-2].lower()
					rel_path = os.path.abspath(n.image.filepath).lower().split(uncook_folder_name)[-1]
					new_param.set('value', rel_path)
	
	################################################
	### Determine and create the right nodegroup ###
	################################################
	
	# List of Witcher 3 shaders that will use Witcher3_Main nodegroup. (This is currently redundant since we will default to this anyways)
	material_main = ['pbr_std',
		'pbr_std_colorshift',
		'pbr_std_tint_mask_2det',
		'pbr_std_tint_mask_2det_fresnel',
		'pbr_std_tint_mask_det',
		'pbr_std_tint_mask_det_fresnel',
		'pbr_std_tint_mask_det_pattern',
		'pbr_spec_tint_mask_det',
		'pbr_spec',
		'transparent_lit',
		'transparent_lit_vert',
		'transparent_reflective',
		'pbr_simple',
		'pbr_simple_noemissive',
		'pbr_det']
	
	# List of Witcher 3 shaders that will use Witcher3_Skin nodegroup.
	material_skin = ['pbr_skin',
		'pbr_skin_decal',
		'pbr_skin_simple',
		'pbr_skin_normalblend',
		'pbr_skin_morph']
	
	# List of Witcher 3 shaders that will use Witcher3_Hair nodegroup.
	material_hair = ['pbr_hair',
		'pbr_hair_simple',
		'pbr_hair_moving']
	
	# List of Witcher 3 shaders that will use Witcher3_Eye nodegroup.
	material_eye = ['pbr_eye']
	
	ng = None		# Nodegroup node tree  (bpy.types.ShaderNodeTree)
	node_ng = None	# Nodegroup group node (bpy.types.ShaderNodeGroup)
	
	if(shader_type in material_main):
		ng = bpy.data.node_groups.get('Witcher3_Main')
	elif(shader_type in material_skin):
		ng = bpy.data.node_groups.get('Witcher3_Skin')
	elif(shader_type in material_hair):
		ng = bpy.data.node_groups.get('Witcher3_Hair')
	elif(shader_type in material_eye):
		ng = bpy.data.node_groups.get('Witcher3_Main')
		#ng = bpy.data.node_groups.get('Witcher3_Eye')
	else:
		ng = bpy.data.node_groups.get('Witcher3_Main')
	
	if(ng != None):
		# Wiping nodes created by fbx importer.
		nodes.clear()
		node_ng = nodes.new(type='ShaderNodeGroup')
		node_ng.node_tree = ng
	else:
		raise W3ImporterError('Error loading material: Missing Witcher 3 Nodegroups')
	
	node_ng.location = (500, 200)
	node_ng.width = 350
	
	#############################
	### Creating output nodeS ###
	#############################
	
	node_output_cycles = nodes.new(type='ShaderNodeOutputMaterial')
	node_output_cycles.target = 'CYCLES'
	node_output_cycles.location = (900, 200)
	node_output_cycles.name = mat_base
	node_output_cycles.label = shader_type
	links.new(node_ng.outputs[0], node_output_cycles.inputs[0])
	
	node_output_eevee = nodes.new(type='ShaderNodeOutputMaterial')
	node_output_eevee.target = 'EEVEE'
	node_output_eevee.location = (900, 0)
	node_output_eevee.name = mat_base
	node_output_eevee.label = shader_type
	links.new(node_ng.outputs[1], node_output_eevee.inputs[0])
	
	######################
	### Sorting params ###
	######################
	
	equivalent_params = {	# TODO: I should probably go about this in a better way. It should probably be a Pin:[Equivalents] dict, not an equivalent:pin dict.
		'Diffusemap' : 'Diffuse',
		'Normalmap' : 'Normal',
		'Ambientmap' : 'TintMask'
		}
	
	ignored_params = ['DetailRange',
	'Pattern_Array', 'Pattern_Mixer', 'Pattern_Index', 'Pattern_Offset', 'Pattern_Size', 'Pattern_DistortionPower', 'Pattern_Rotation', 'handle:CTextureArray', 'Pattern_Roughness_Influence', 'Pattern_Color1', 'Pattern_Color2', 'Pattern_Color3']	# These Pattern textures are hidden in a .texarr file so we can't get any use out of them.
	
	# Ordering the parameters so that the input nodes get created in this order, from top to bottom. Purely for neatness.
	order = ['Diffuse', 'Normal', 'Ambient', 'TintMask', 'SpecularTexture', 'SpecularColor', 
		'RSpecScale', 'RSpecBase', 
		'Anisotropy', 'SpecularShiftTexture', 'SpecularShiftUVScale', 'SpecularShiftScale', 
		'Translucency', 'TranslucencyRim', 'TranslucencyRimScale', 
		'FresnelStrength', 'FresnelPower', 
		'AOPower', 'AmbientPower', 
		'DetailPower', 
		'DetailNormal', 'DetailTile', 'DetailRange', 'DetailRotation', 
		'DetailNormal1', 'DetailTile1', 'DetailRange1', 'DetailRotation1', 
		'Detail1Normal', 'Detail1Tile', 'Detail1Range', 'Detail1Rotation', 
		'Detail2Normal', 'Detail2Tile', 'Detail2Range', 'Detail2Rotation', 
		'DetailNormal2', 'DetailTile2', 'DetailRange2', 'DetailRotation2', 
		]
	
	ordered_params = order_elements_by_attribute(mat_data, order, 'name')
	
	#################################
	### Loading params into nodes ###
	#################################
	
	y_loc = 1000	# Y location of the next node to spawn.
	for param in ordered_params:
		par_name = param.get('name')
		par_type = param.get('type')
		par_value = param.get('value')
		
		if(par_value == 'NULL' or 
			par_name in ignored_params):
			continue
		
		node_label = par_name
		y_loc_increment = -170
		node=None
		
		### Texture inputs  ###
		if(par_type=='handle:ITexture'):
			node = nodes.new(type="ShaderNodeTexImage")
			node.width = 300
			
			# Setting Color/Non-Color Data
			if(par_name not in ['Diffuse', 'SpecularTexture', 'TintMask']):
				if(node.image):
					node.image.colorspace_settings.name = 'Non-Color'
			
			### Some texture types need special treatment ###
			if(par_name == 'Normal'):
				roughness_pin = node_ng.inputs.get('Roughness')
				if(roughness_pin != None):
					links.new(node.outputs[1], roughness_pin)
			elif(par_name == 'Diffuse'):
				alpha_pin = node_ng.inputs.get('Alpha')
				if(alpha_pin != None):
					links.new(node.outputs[1], alpha_pin)
			elif( (('Normal' in par_name) and ('Detail' in par_name)) or
			'SpecularShiftTexture' == par_name):
				# DetailNormals need a Mapping node to apply the DetailScale and DetailRotation to.
				node_mapping = nodes.new(type='ShaderNodeMapping')
				node_mapping.location = (-600, y_loc-200)
				node_mapping.hide = True
				links.new(node_mapping.outputs[0], node.inputs[0])
				
				node_uv = nodes.new(type='ShaderNodeUVMap')
				node_uv.location = (node_mapping.location.x-200, node_mapping.location.y)
				node_uv.hide = True
				links.new(node_uv.outputs[0], node_mapping.inputs[0])
			
			#######################
			### Loading texture ###
			#######################
			tex_path = uncook_path + os.sep + par_value.replace(".xbm", ".tga")
			if( not os.path.isfile(tex_path) ):
				print("Image not found: " + tex_path)
				node_label = "MISSING:" + par_value
			else:
				img = node.image = bpy.data.images.load(tex_path, check_existing=True)
				# Moving images to local textures folder
				# TODO: why are we still referring to node.image instead of img?
				if(bpy.data.is_saved and len(node.image.packed_files) > 0):
					img.pack()
					node.image.unpack(method='WRITE_LOCAL')
				node.image.name = node.image.filepath.split("\\")[-1].split(".")[0]	# Yikes.
				# Setting color space and alpha mode (TODO: check that this works) (Other TODO: fix this when it gets broken by https://developer.blender.org/T60990)
				if(node.image):
					if( node.image.colorspace_settings.name == 'Non-Color' ):
						img.alpha_mode = 'CHANNEL_PACKED'
					else:
						img.alpha_mode = 'STRAIGHT'
					
			y_loc_increment = -320
			
		### Float inputs ###
		elif(par_type=='Float'):
			if('Rotation' in par_name):
				normal_node = nodes.get(par_name.replace('Rotation', 'Normal'))
				if(normal_node != None):
					mapping_node = normal_node.inputs[0].links[0].from_node
					mapping_node.rotation[2] = float(par_value)
					continue
			node = nodes.new(type='ShaderNodeValue')
			node.outputs[0].default_value = float(par_value)
			
		### Color inputs ###
		elif(par_type=='Color'):
			values = [float(f) for f in par_value.split("; ")]
			if(values[3] == 255):	# If the Alpha value is 1, use the better looking CombineRGB node. (Discarding the useless alpha)
				node = nodes.new(type='ShaderNodeCombineRGB')
				node.inputs[0].default_value = values[0]/255
				node.inputs[1].default_value = values[1]/255
				node.inputs[2].default_value = values[2]/255
				#map(lambda x: node.inputs[x].default_value = values[x]/255, range(3))
			else:					# Otherwise, use the uglier RGB node which supports Alpha.
				node = nodes.new(type='ShaderNodeRGB')
				node.outputs[0].default_value = (values[0]/255, values[1]/255, values[2]/255, values[3]/255)
		
		### Vector inputs ###
		elif(par_type=='Vector'):
			values = [float(f) for f in par_value.split("; ")]
			# Handling UV scale nodes for detail normals and SpecularShiftTextures
			if( ('Tile' in par_name) or ('SpecularShiftUVScale' in par_name) ):
				target_node = nodes.get(par_name.replace('Tile', 'Normal'))
				if(target_node == None): 
					target_node = nodes.get('SpecularShiftTexture')
				if(target_node != None):
					mapping_node = target_node.inputs[0].links[0].from_node
					mapping_node.scale[0] = values[0]
					mapping_node.scale[1] = values[1]
					continue
			if(values[3] != 1 and values[3] != 0):	# The 4th value on vectors is probably always useless, but just in case.
				print("Warning: Discarded vector 4th value: " + str(values) + " in parameter: " + par_name)
			node = nodes.new(type='ShaderNodeCombineXYZ')
			#map(lambda x: node.inputs[x].default_value = values[x], range(3))
			node.inputs[0].default_value = values[0]
			node.inputs[1].default_value = values[1]
			node.inputs[2].default_value = values[2]
		
		# Unknown inputs are created as an Attribute node.
		else:
			print("Unknown material parameter type: "+par_type)
			node = nodes.new(type="ShaderNodeAttribute")
			node_label = "Unknown type: " + par_type
			node.attribute_name = par_value
		
		node.location = (-450, y_loc)
		node.name = par_name
		node.label = node_label
		y_loc = y_loc + y_loc_increment
		
		# Linking the node to the nodegroup
		if( node.label in equivalent_params ):
			input_pin = node_ng.inputs.get(equivalent_params[node.label])
			if(input_pin != None and len(input_pin.links) == 0):
				links.new(node.outputs[0], input_pin)
		input_pin = node_ng.inputs.get(node.label)
		if(input_pin != None):
			links.new(node.outputs[0], input_pin)
		
		# Checking if node got connected and printing to console if not.
		if(len(node.outputs[0].links)==0):
			print("Unconnected node: " + node.name)
	
	if( len(node_ng.inputs[0].links) > 0 ):
		color_node = node_ng.inputs[0].links[0].from_node
		nodes.active = color_node
		if(color_node.image != None):
			material.name = color_node.image.name.split("_d0")[0].split("_d.")[0]
		else:
			print("Warning: No diffuse texture found for material: " + material.name)
	else:
		print("Warning: No diffuse texture was referenced by this material: " + material.name)
	
	# Setting material settings (these only affect the viewport) TODO make sure this works.
	material.metallic = 0
	material.roughness = 0.5
	material.diffuse_color = (0.3, 0.3, 0.3, 1)
	
	return material

def load_w3_materials(obj, xml_path):	
	# Reads XML and sets up all materials on the object.
	# It unavoidably requires that materials were not yet renamed after the FBX import.
	root = readXML(xml_path)
	
	for rootelement in root:
		if(rootelement.tag=='materials'):
			for mat_data in rootelement:
				mat_name = mat_data.get('name')
				# Finding corresponding blender material
				target_mat = None
				for m in obj.data.materials:
					# Comparing the number at the end of the blender material name "MaterialX" to the last character of the XML material.
					if("Material" in m.name and 
						m.name[8] == mat_name[-1]):
						target_mat = m
						break
				if(target_mat == None):	
					# If we didn't find a matching blender material, it's a material for the LOD meshes, ignore it.
					continue
				
				finished_mat = setup_w3_material(target_mat, mat_data, obj)
				obj.material_slots[target_mat.name].material = finished_mat

def parent_w3_bones(armature):	
	# Parent bones using a child:parent name dictionary. 
	parent_dict = {
		# spine
		'pelvis': 'torso',
		'torso2': 'torso',
		'torso3': 'torso2',
		'neck': 'torso3',
		'head': 'neck',
		
		# breasts
		'l_boob': 'torso3',
		'r_boob': 'torso3',
		
		#right leg
		'r_thigh': 'pelvis',
		'r_legRoll': 'torso',
		'r_legRoll2': 'torso',
		'r_shin': 'r_thigh',
		'r_kneeRoll': 'r_shin',
		'r_foot': 'r_shin',
		'r_toe': 'r_foot',
		
		#right arm
		'r_shoulder': 'torso3',
		'r_shoulderRoll': 'r_shoulder',
		'r_bicep': 'r_shoulder',
		'r_bicep2': 'r_bicep',
		'r_elbowRoll': 'r_bicep',
		'r_forearmRoll1': 'r_elbowRoll',
		'r_forearmRoll2': 'r_elbowRoll',
		'r_handRoll': 'r_elbowRoll',
		
		#right hand
		'r_hand': 'r_elbowRoll',
		'r_pinky0': 'r_hand',
		
		'r_thumb1': 'r_hand',
		'r_thumb_roll': 'r_hand',
		'r_thumb2': 'r_thumb1',
		'r_thumb3': 'r_thumb2',
		
		'r_index_knuckleRoll': 'r_hand',
		'r_index1': 'r_hand',
		'r_index2': 'r_index1',
		'r_index3': 'r_index2',
		
		'r_middle_knuckleRoll': 'r_hand',
		'r_middle1': 'r_hand',
		'r_middle2': 'r_middle1',
		'r_middle3': 'r_middle2',
		
		'r_ring_knuckleRoll': 'r_hand',
		'r_ring1': 'r_hand',
		'r_ring2': 'r_ring1',
		'r_ring3': 'r_ring2',
		
		'r_pinky_knuckleRoll': 'r_hand',
		'r_pinky1': 'r_pinky0',
		'r_pinky2': 'r_pinky1',
		'r_pinky3': 'r_pinky2',
		
		#left leg
		'l_thigh': 'pelvis',
		'l_legRoll': 'torso',
		'l_legRoll2': 'torso',
		'l_shin': 'l_thigh',
		'l_kneeRoll': 'l_shin',
		'l_foot': 'l_shin',
		'l_toe': 'l_foot',
		
		#left arm
		'l_shoulder': 'torso3',
		'l_shoulderRoll': 'l_shoulder',
		'l_bicep': 'l_shoulder',
		'l_bicep2': 'l_bicep',
		'l_elbowRoll': 'l_bicep',
		'l_forearmRoll1': 'l_elbowRoll',
		'l_forearmRoll2': 'l_elbowRoll',
		'l_handRoll': 'l_elbowRoll',
		
		#left hand
		'l_hand': 'l_elbowRoll',
		'l_pinky0': 'l_hand',
		
		'l_thumb1': 'l_hand',
		'l_thumb_roll': 'l_hand',
		'l_thumb2': 'l_thumb1',
		'l_thumb3': 'l_thumb2',
		
		'l_index_knuckleRoll': 'l_hand',
		'l_index1': 'l_hand',
		'l_index2': 'l_index1',
		'l_index3': 'l_index2',
		
		'l_middle_knuckleRoll': 'l_hand',
		'l_middle1': 'l_hand',
		'l_middle2': 'l_middle1',
		'l_middle3': 'l_middle2',
		
		'l_ring_knuckleRoll': 'l_hand',
		'l_ring1': 'l_hand',
		'l_ring2': 'l_ring1',
		'l_ring3': 'l_ring2',
		
		'l_pinky_knuckleRoll': 'l_hand',
		'l_pinky1': 'l_pinky0',
		'l_pinky2': 'l_pinky1',
		'l_pinky3': 'l_pinky2',
		
		#head / face
		'thyroid': 'head',
		'hroll': 'head',
		'jaw': 'head',
		'ears': 'head',
		'nose': 'head',
		'nose_base': 'head',
		'lowwer_lip': 'jaw',
		'upper_lip': 'head',
		'chin': 'jaw',
		
		'right_temple': 'head',
		'right_forehead': 'head',
		'right_chick1': 'head',
		'right_chick2': 'head',
		'right_chick3': 'head',
		'right_chick4': 'head',
		'right_nose1': 'head',
		'right_nose2': 'head',
		'right_nose3': 'head',
		'right_eyebrow1': 'head',
		'right_eyebrow2': 'head',
		'right_eyebrow3': 'head',
		'right_eye': 'head',
		
		'upper_right_eyelid1': 'head',
		'upper_right_eyelid2': 'head',
		'upper_right_eyelid3': 'head',
		'upper_right_eyelid_fold': 'head',
		'lowwer_right_eyelid1': 'head',
		'lowwer_right_eyelid2': 'head',
		'lowwer_right_eyelid3': 'head',
		'lowwer_right_eyelid_fold': 'head',
		
		'tongue_left_side' : 'tongue2',
		'tongue_right_side' : 'tongue2',
		'tongue1' : 'jaw',
		
		'right_chick2': 'head',
		'right_chick3': 'head',
		'right_mouth_fold1': 'jaw',
		'right_mouth2': 'jaw',
		'right_mouth1': 'jaw',
		'upper_right_lip': 'head',
		'lowwer_right_lip': 'jaw',
		'right_corner_lip2': 'jaw',
		'right_corner_lip1': 'head',
		'right_mouth3': 'head',
		'right_mouth4': 'head',
		'right_mouth_fold2': 'head',
		'right_mouth_fold3': 'head',
		'right_mouth_fold4': 'head',
		
		'left_temple': 'head',
		'left_forehead': 'head',
		'left_chick1': 'head',
		'left_chick2': 'head',
		'left_chick3': 'head',
		'left_chick4': 'head',
		'left_nose1': 'head',
		'left_nose2': 'head',
		'left_nose3': 'head',
		'left_eyebrow1': 'head',
		'left_eyebrow2': 'head',
		'left_eyebrow3': 'head',
		'left_eye': 'head',
		
		'upper_left_eyelid1': 'head',
		'upper_left_eyelid2': 'head',
		'upper_left_eyelid3': 'head',
		'upper_left_eyelid_fold': 'head',
		'lowwer_left_eyelid1': 'head',
		'lowwer_left_eyelid2': 'head',
		'lowwer_left_eyelid3': 'head',
		'lowwer_left_eyelid_fold': 'head',

		'upper_left_eyelash' : 'upper_left_eyelid2',  
		'upper_right_eyelash' : 'upper_right_eyelid2',  
		
		'left_chick2': 'head',
		'left_chick3': 'head',
		'left_mouth_fold1': 'jaw',
		'left_mouth2': 'jaw',
		'left_mouth1': 'jaw',
		'upper_left_lip': 'head',
		'lowwer_left_lip': 'jaw',
		'left_corner_lip2': 'jaw',
		'left_corner_lip1': 'head',
		'left_mouth3': 'head',
		'left_mouth4': 'head',
		'left_mouth_fold2': 'head',
		'left_mouth_fold3': 'head',
		'left_mouth_fold4': 'head',
		
		#util
		'dyng_frontbag_01': 'torso',
		'dyng_backbag_01' : 'pelvis',
		'hinge_frontrag' : 'pelvis',
		'dyng_back_belt_01' : 'torso2',
		'dyng_front_belt_01' : 'torso2',
		
		#succubus
		'dyng_tail_01': 'torso',
		
		# weapons
		'steel_sword_scabbard_3' : 'steel_sword_scabbard_2',
		'steel_sword_scabbard_2' : 'steel_sword_scabbard_1',
		'steel_sword_scabbard_1' : 'torso3',
		
		'dyng_dagger_01' : 'pelvis',
		
		# medallions, necklaces
		'dyng_pendant_01' : 'head',
		'dyng_necklace_01' : 'torso3',
		
		'medalion_main_01' : 'r_medalion_03',
		'r_medalion_03' : 'r_medalion_02',
		'r_medalion_02' : 'torso3',
		'l_medalion_03' : 'l_medalion_02',
		'l_medalion_02' : 'torso3',
		
		'vesemir_medalion_main_01' : 'r_vesemir_medalion_02',
		'r_vesemir_medalion_01' : 'torso3',
		'l_vesemir_medalion_01' : 'torso3',
		
		'dyng_r_necklace_01' : 'torso3',
		'dyng_l_necklace_01' : 'torso3',
		'dyng_m_necklace_01' : 'dyng_l_necklace_02',
		
		# random clothes
		'dyng_l_double_earing_01' : 'head',
		'dyng_r_double_earing_01' : 'head',
		
		'hinge_l_collar' : 'torso3',
		'hinge_r_collar' : 'torso3'
	}
	
	# Mode management
	bpy.ops.object.mode_set(mode='OBJECT')
	bpy.ops.object.select_all(action='DESELECT')
	bpy.context.view_layer.objects.active = armature
	bpy.ops.object.mode_set(mode='EDIT')
	eb = armature.data.edit_bones
	
	def nearest_parent(bone_name):
		# Recursive function to find a parent for a bone even if its direct parent bone is missing. 
		if(bone_name == None):
			return None
		parent_name = parent_dict.get(bone_name)
		if(parent_name != None): 
			parent = eb.get(parent_name)
			if(parent != None):
				return parent
			else:
				# Recursion to keep searching for the nearest parent in the dictionary.
				return nearest_parent(parent_name)
			
		# If we haven't returned yet, parent was not found in dictionary.
		
		# Bones ending in a number will be automatically parented to the bone with the same name but lower number.
		try:
			number = int(bone_name[-1])	# If the last character of the bone name is a number, just find the bone with the lower number.
			if(number==1 and 'hair' in bone_name):
				# This lets us avoid having to put every hair1 bone in the dict.
				return eb.get('head')
			else:
				parent_name = bone_name[:-1] + str(number-1)
				return eb.get(parent_name)
		except ValueError:
			# If converting to an int fails
			pass
		
		# If we got this far, then we couldn't find a parent.
		return None
	
	### Parenting the bones ###
	for bone in eb:
		parent = nearest_parent(bone.name)
		if(parent != None):
			bone.parent = parent
		else:
			continue
	
	bpy.ops.object.mode_set(mode='OBJECT')

def delete_unused_bones(armature):
	# Unused meaning bones that don't have a vertex group on any of the armature's child meshes.
	# TODO make this a separate operator.
	
	# Mode management
	bpy.ops.object.mode_set(mode='OBJECT')
	bpy.ops.object.select_all(action='DESELECT')
	bpy.context.view_layer.objects.active = armature
	bpy.ops.object.mode_set(mode='EDIT')
	
	vgs = []	# List to store all vertex groups' names used by all of the armature's child meshes.
	for o in armature.children:
		if(o.type != 'MESH'): continue
		for vg in o.vertex_groups:
			if(vg not in vgs):
				vgs.append(vg.name)
	
	# Deleting bones that don't have a corresponding name in vgs.
	bpy.context.view_layer.objects.active = armature
	bpy.ops.object.mode_set(mode='EDIT')
	for eb in reversed(armature.data.edit_bones):
		if(eb.name not in vgs):
			armature.data.edit_bones.remove(eb)
	bpy.ops.object.mode_set(mode='OBJECT')

def combine_armatures(armatures, main_armature=None):
	# Combine a list of armatures into one while preventing duplicate bones.
	# Child meshes will also be parented to the combined armature, and their armature modifier's target will be replaced.
	# Note: Does not combine hierarchies. parent_w3_bones should be called on the resulting armature.
	
	if(len(armatures)==0):return

	if(main_armature == None):
		main_armature = armatures[0]
	
	bpy.ops.object.mode_set(mode='OBJECT')
	bpy.ops.object.select_all(action='DESELECT')
	
	for a in armatures:
		if(a.type != 'ARMATURE'):
			continue
		if(a == main_armature):
			continue
		
		# Finding bones that exist in the main armature
		duplicates = []
		for b in a.data.bones:
			if(b.name in main_armature.data.bones):
				duplicates.append(b.name)
		
		# Deleting the bones that were found
		bpy.context.view_layer.objects.active = a
		bpy.ops.object.mode_set(mode='EDIT')
		for eb in duplicates:
			a.data.edit_bones.remove(a.data.edit_bones.get(eb))
		bpy.ops.object.mode_set(mode='OBJECT')
		
		# Parenting child meshes of this armature to main armature
		for o in a.children:
			o.select_set(True)
		main_armature.select_set(True)
		bpy.context.view_layer.objects.active = main_armature
		bpy.ops.object.parent_set(type='ARMATURE')
		
		# Joining this armature with the main armature
		bpy.ops.object.select_all(action='DESELECT')
		a.select_set(True)
		main_armature.select_set(True)
		bpy.context.view_layer.objects.active = main_armature
		bpy.ops.object.join()
		
	return main_armature

def fix_bone_tail(edit_bones, bone=None):
	# Recursive function to go through a bone hierarchy and move the bone tails to useful positions.
	# Requires the armature to be in edit mode because I don't want to switch between object/edit in a recursive function.
	
	if(len(edit_bones) == 0):
		raise W3ImporterError("Armature needs to be in edit mode for fix_bone_tail().")
	
	# Dictionary to help connect the bone tails to specific bone heads
	connect_dict = {
		'l_shoulder' 			: 'l_bicep'		,
		'l_bicep' 				: 'l_elbowRoll'	,
		'l_elbowRoll' 			: 'l_hand'		,
		'l_hand' 				: 'l_middle1'	,
		'l_thigh' 				: 'l_shin'		,
		'l_shin' 				: 'l_foot'		,
		'l_foot' 				: 'l_toe'		,
		'l_index_knuckleRoll' 	: 'l_index2'	,
		'l_middle_knuckleRoll' 	: 'l_middle2'	,
		'l_ring_knuckleRoll' 	: 'l_ring2'		,

		'r_shoulder' 			: 'r_bicep'		,
		'r_bicep' 				: 'r_elbowRoll'	,
		'r_elbowRoll' 			: 'r_hand'		,
		'r_hand' 				: 'r_middle1'	,
		'r_thigh' 				: 'r_shin'		,
		'r_shin' 				: 'r_foot'		,
		'r_foot' 				: 'r_toe'		,
		'r_index_knuckleRoll' 	: 'r_index2'	,
		'r_middle_knuckleRoll' 	: 'r_middle2'	,
		'r_ring_knuckleRoll' 	: 'r_ring2'		,

		'pelvis' 				: 'None'		,
		'torso' 				: 'torso2'		,
		'torso2' 				: 'torso3'		,
		'torso3' 				: 'neck'		,
		'neck' 					: 'head'		,
		'head' 					: 'None'		,
		'jaw' 					: 'chin'		,
		'tongue2' 				: 'lowwer_lip'	,
	}
	
	if(bone == None):
		bone=edit_bones[0]
	
	# If a bone is in connect_dict, just move its tail to the bone specified in the dictionary.
	if(bone.name in connect_dict):
		target = edit_bones.get(connect_dict[bone.name])
		if(target != None):
			bone.tail = target.head
	else:
		# For bones with children, we'll just connect the bone to the first child.
		if(len(bone.children) > 0):
			bone.tail = bone.children[0].head
		
		# For bones with no children...
		else:
			if(bone.parent != None):
				# Get the parent's head->tail vector
				parent_vec = bone.parent.tail - bone.parent.head
				# If the bone has siblings, set the scale to an arbitrary amount.
				if( len(bone.parent.children) > 1): 
					scale = 0.1
					if('tongue' in bone.name): scale = 0.03
					bone.tail = bone.head + parent_vec.normalized() * scale	# Todo change this number to .05 if the apply_transforms() gets fixed.
				# If no siblings, just use the parents transforms.
				else:
					bone.tail = bone.head + parent_vec
				
				# Special treatment for the children of some bones
				if(bone.parent.name in ['head', 'jaw']):
					bone.tail = bone.head+Vector((0, 0, .02))
	
	# Recursion over this bone's children.
	for c in bone.children:
		fix_bone_tail(edit_bones, c)

def cleanup_w3_armature(arm, char_name = ''):
	# For scaling bones, fixing hierarchy, recalculating rolls, renaming unique bones, cleaning unused bones, enabling x-ray.
	
	# Mode management
	bpy.ops.object.mode_set(mode='OBJECT')
	bpy.ops.object.select_all(action='DESELECT')
	bpy.context.view_layer.objects.active = arm
	bpy.ops.object.mode_set(mode='EDIT')
	ebones = arm.data.edit_bones
	
	# Scaling bones to an absolute scale(all bones the same size)
	for eb in ebones:
		scale = .1
		eb.tail = eb.head + Vector.normalized(eb.tail-eb.head) * scale
	
	# Fixing hierarchy
	parent_w3_bones(arm)
	
	# Fixing bone tails and rotations
	bpy.ops.object.mode_set(mode='EDIT')
	root_bone = ebones.get('torso')
	if(root_bone == None):
		root_bone = ebones[0]
	fix_bone_tail(arm.data.edit_bones, root_bone)
	bpy.ops.armature.calculate_roll(type='GLOBAL_POS_Y')
	bpy.ops.object.mode_set(mode='OBJECT')
	
	# Renaming unique bones (which are the ones that begin with 'dyng_')
	if(char_name != ''):
		for b in arm.data.bones:
			b.name = b.name.replace('dyng', char_name)
			
	# Cleaning unused bones
	delete_unused_bones(arm)
	
	# Enabling X-Ray
	arm.show_in_front = True
	
	print("Armature cleaned up: "+arm.name)

def import_w3_fbx(filepath, uncook_path, remove_doubles=True, keep_lod_meshes=False, quadrangulate=True, fix_armature=True):
	append_resources()
	
	if filepath.endswith(".fbx"):
		filename = filepath.split("\\")[-1].split(".")[0]
		print("...Importing FBX: "+filename)
		enable_print(False)
		bpy.ops.import_scene.fbx( filepath = filepath )	# The imported objects automatically became selected on import.
		enable_print(True)
		obj_name = filename
		
		# Discarding LOD meshes.
		if(not keep_lod_meshes):
			for o in reversed(bpy.context.selected_objects):
				if( ("lod1" in o.name) or ("lod2" in o.name) or ("lod3" in o.name) ):
					bpy.data.objects.remove(o)
		
		armatures = []
		meshes = []
		for o in bpy.context.selected_objects:
			bpy.ops.object.select_all(action='DESELECT')
			assert o.type != 'EMPTY', "You didn't fix import_fbx.py"
			if(o.type == 'MESH'):
				meshes.append(o)
				o.name = obj_name
				enable_print(False)
				cleanup_mesh.cleanup_mesh(o, remove_doubles, quadrangulate, weight_normals=True, seams_from_islands=True)
				enable_print(True)
				load_w3_materials(o, filepath.replace(".fbx", ".xml"))
			if(o.type == 'ARMATURE'):
				o.name = obj_name + "_Skeleton"
				armatures.append(o)
				if(fix_armature):
					cleanup_w3_armature(o)
			o.data.name = "Data_" + o.name
		
		bpy.ops.object.mode_set(mode='OBJECT')
		bpy.ops.object.select_all(action='DESELECT')
		
		for o in meshes:
			o.select_set(True)
			# Todo: Re-write this area when transforms_apply() and skeleton transforms in general get unfucked. They are incredibly broken in 2.8 right now...
			o.scale = (.01, .01, .01)
			o.rotation_euler = Euler((0, 0, pi), 'XYZ')
			o.modifiers.clear()
		
		# Applying rotation and scale (Armatures import with 180 rotation on Z and .01 scale.
		# Due to a bug in current 2.80 beta I must first unparent the objects, then apply the scale, then reparent the objects, in order to be futureproof in case they fix transforms_apply() and I won't bother to update the script.
		# if I do bother to update the script: TODO delete this and just do transforms_apply() twice. Then all we need to do here is make sure all meshes and armature are selected.
		bpy.ops.object.parent_clear(type='CLEAR')
		
		if(len(armatures)>0):
			armatures[0].rotation_euler = Euler((0, 0, pi), 'XYZ')
			armatures[0].select_set(True)
			bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
			bpy.context.view_layer.objects.active=armatures[0]
			bpy.ops.object.parent_set(type='ARMATURE')
			
		return [meshes, armatures]
	return [[], []]

def batch_import_w3_fbx(paths, uncook_path, char_name = '', recursive=False, keep_lod_meshes=False, remove_doubles=True, quadrangulate=True, combined_armatures=True):
	# Importing FBX's
	all_objects = [[], []]	# First list is for meshes, second list is armatures.
	
	# Assume paths is a list of filepaths.
	if(type(paths)==list):
		for filepath in paths:
			objects = import_w3_fbx(filepath, uncook_path, remove_doubles, keep_lod_meshes, quadrangulate, fix_armature=False)
			all_objects[0].extend(objects[0])
			all_objects[1].extend(objects[1])
	# Assume paths is a folder path.
	else:
		import_path = paths
		for subdir, dirs, files in os.walk(import_path):
			for file in files:
				filepath = subdir + os.sep + file
				objects = import_w3_fbx(filepath, uncook_path, remove_doubles, keep_lod_meshes, quadrangulate, fix_armature=False)
				all_objects[0].extend(objects[0])
				all_objects[1].extend(objects[1])
			if(not recursive): break;
	
	armatures = all_objects[1]
	
	# Combine armatures & clean up
	if(combined_armatures):
		main_armature = combine_armatures(all_objects[1])
		if(main_armature):
			main_armature.name = 'Witcher3_Skeleton_' + char_name
			cleanup_w3_armature(main_armature, char_name)
			armatures = [main_armature]
	
	for a in armatures:
		# Cleaning unused bones
		delete_unused_bones(a)
		# Fixing bone hierarchy
		parent_w3_bones(a)
	
	# Create a collection with all imported objects
	coll = bpy.data.collections.new(char_name)
	bpy.context.scene.collection.children.link(coll)
	for o in all_objects[0] + armatures:
		# Remove from active collection
		active_coll = bpy.context.collection
		active_coll.objects.unlink(o)
		# Add to the new collection
		coll.objects.link(o)
	
class BatchImportW3FBX(Operator, ImportHelper):
	"""MAKE SURE YOU HAVE SYSTEM CONSOLE OPEN. Select an entire character folder or single FBX file. If you select multiple characters, all their skeletons will be merged into one, not recommended."""
	bl_idname = "import_scene.witcher3_fbx_batch"
	bl_label = "Batch Import Witcher 3 FBX"
	bl_options = {'REGISTER', 'UNDO'}
	
	# ImportHelper mixin class uses this
	filename_ext = ".fbx"

	filter_glob: StringProperty(
		default="*.fbx",
		options={'HIDDEN'}
	)
	
	char_name: StringProperty(
		name="Character Name",
		default="Character Name",
		description="Used for naming of the skeleton, bones and collection."
	)
	
	recursive: BoolProperty(
		name="Recursive",
		default=True,
		description="Disable to ignore subfolders of the selected folder."
	)
	
	keep_lod_meshes: BoolProperty(
		name="Keep LODs",
		default=False,
		description="If enabled, it will keep low quality meshes and materials"
	)

	remove_doubles: BoolProperty(
		name="Remove Doubles",
		default=True,
		description="Disable this if you get incorrectly merged verts."
	)
	
	quadrangulate: BoolProperty(
		name="Tris to Quads",
		default=True,
		description="Runs the Tris to Quads operator on imported meshes with UV seams enabled. Therefore it shouldn't break anything"
	)
	
	combined_armatures: BoolProperty(
		name="Combine Armatures",
		default=True,
		description="Merge all armatures into one"
	)
	
	files: CollectionProperty(
		name="File Path",
		description=(
			"File path used for importing"
		),
		type=bpy.types.OperatorFileListElement)

	directory: StringProperty()	

	def execute(self, context):
		addon_prefs = bpy.context.preferences.addons[__package__].preferences
	
		char_name = self.char_name
		uncook_path = addon_prefs.uncook_path
		import_path = self.filepath	# self.filepath provided by ImportHelper.
		recursive = self.recursive
		keep_lod_meshes = self.keep_lod_meshes
		remove_doubles = self.remove_doubles
		quadrangulate = self.quadrangulate
		combined_armatures = self.combined_armatures
		
		paths = [os.path.join(self.directory, name.name)
			for name in self.files]

		if not paths:
			paths.append(self.filepath)
		
		print("Paths:")
		for path in paths:
			print(path)
			print("---------")
		
		# If the user didn't change the uncook path from the default
		if(uncook_path == 'E:\\Path_to_your_uncooked_folder\\Uncooked\\'):
			raise W3ImporterError("Please browse your Uncooked folder in the Addon Preferences UI in Edit->Preferences->Addons->Witcher 3 FBX Import Tools.")
		
		# If a single file was selected
		if(import_path.endswith(".fbx") and len(paths)==1):
			import_w3_fbx(import_path, uncook_path, remove_doubles, keep_lod_meshes, quadrangulate, fix_armature=True)
			pass
		# If multiple files were selected
		elif(len(paths) > 1):
			if(char_name == "" or char_name== "Character Name"):	# If no character name is specified, use folder name.
				char_name = os.path.dirname(import_path).split("\\")[-1].capitalize()
			batch_import_w3_fbx(paths, uncook_path, char_name, recursive, keep_lod_meshes, remove_doubles, quadrangulate, combined_armatures)
		# No files were selected, so we import the entire folder
		else:
			batch_import_w3_fbx(import_path, uncook_path, char_name, recursive, keep_lod_meshes, remove_doubles, quadrangulate, combined_armatures)
		return {'FINISHED'}

def menu_func_import(self, context):
	self.layout.operator(BatchImportW3FBX.bl_idname, text="Witcher 3 FBX")
	
class ImportW3FBX(Operator):
	"""Import a single Witcher 3 FBX"""
	bl_idname = "import_scene.witcher3_fbx"
	bl_label = "Import Witcher 3 FBX"
	bl_options = {'REGISTER', 'UNDO'}
	
	import_now: BoolProperty(
		name="Import now!",
		description="Enable this once all your settings are correct. You should have a console open. Once you pressed it, do not change any settings until you untick this, or the operator will run again",
		default=False,
		options={'SKIP_SAVE'}
	)
	
	keep_lod_meshes: BoolProperty(
		name="Keep LODs",
		default=False,
		description="If enabled, it will keep low quality meshes and materials"
	)
	
	fix_armature: BoolProperty(
		name="Fix Armature",
		default=True,
		description="Fix bone hierarchy, rotations, etc."
	)

	remove_doubles: BoolProperty(
		name="Remove Doubles",
		default=False,
		description="DON'T ENABLE THIS IF YOU DON'T KNOW THE RISKS! That said, you should learn about the risks and enable this for best results. Merge verts that are in the same location. Prone to error"
	)
	
	quadrangulate: BoolProperty(
		name="Tris to Quads",
		default=True,
		description="Runs the Tris to Quads operator on imported meshes with UV seams enabled. Therefore it shouldn't break anything"
	)
	
	import_path: StringProperty(
		name="Import Path",
		subtype="FILE_PATH",
		default="E:\\3D\\Witcher3\\Export\\BaseGame\\characters\\models\\main_npc\\ciri\\",
		description="Path to the character's folder containing their .fbx and .xbm files that were exported by wcc_lite.exe. If it's the same as the uncook path, you can leave this empty"	# TODO: default this to "" and make sure we use uncook path if it is "".
	)
	
	def execute(self, context):
		preferences = context.preferences
		addon_prefs = preferences.addons[__package__].preferences
		uncook_path = addon_prefs.uncook_path
		
		import_path = self.import_path
		keep_lod_meshes = self.keep_lod_meshes
		remove_doubles = self.remove_doubles
		quadrangulate = self.quadrangulate
		import_now = self.import_now
		fix_armature = self.fix_armature
		
		if(import_now):
			import_w3_fbx(import_path, uncook_path, remove_doubles, keep_lod_meshes, quadrangulate, fix_armature)
		return {'FINISHED'}

class CombineArmatures(Operator):
	"""Combine selected armatures into one."""
	bl_idname = "object.smart_join_armatures"
	bl_label = "Smart Join Armatures"
	bl_options = {'REGISTER', 'UNDO'}
	
	def execute(self, context):
		selected_armatures = [o for o in bpy.context.selected_objects if o.type=='ARMATURE']
		active_armature = bpy.context.object if bpy.context.object.type=='ARMATURE' else None
		
		combined_armature = combine_armatures(selected_armatures, active_armature)
		cleanup_w3_armature(combined_armature)
		
		return {'FINISHED'}

def register():
	bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
	from bpy.utils import register_class
	bpy.utils.register_class(BatchImportW3FBX)
	bpy.utils.register_class(ImportW3FBX)
	bpy.utils.register_class(CombineArmatures)

def unregister():
	bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
	from bpy.utils import unregister_class
	bpy.utils.unregister_class(BatchImportW3FBX)
	bpy.utils.unregister_class(ImportW3FBX)
	bpy.utils.unregister_class(CombineArmatures)