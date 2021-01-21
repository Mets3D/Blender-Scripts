#Version V1.1
#Removed eye constraining
#2016.05.26

import vs
import random
import re
import os

###################################################################################
###						What this script does differently						###
###	 Finds spine and limb bones based on regular expressions and bone hierarchy	###
###		Moves bones and flexes into groups, filtered using regular expressions	###
###		     Sets up rig_footroll for any model that has feet and toe bones		###
###					  Should be compatible with almost any model				###
###################################################################################
###############################  MetsSFM.tumblr.com  ##############################
###################################################################################

### Below is a list of ideas that could be implemented if I had the motivation	###
# Remove groups that only have 1-2 controls, and move them to their parents.
# Make toes and clavicles optional
# Multilimb support
# Could stop making rig handles for things that don't need it(spines) and just rename the bones. Would make exporting and importing animations better due to not losing keyframe locations.

# Shower thought - It would be enough to find the hand and feet bones for the rig. Then just read their parents to find the shoulders, clavicles, knees, thighs. Why didn't I realize this when back when I actually cared?


### These variables should be accessible from anywhere in the script ###
shot = 		sfm.GetCurrentShot()
animSet = 	sfm.GetCurrentAnimationSet()
gameModel = animSet.gameModel
rootGroup = animSet.GetRootControlGroup()
rootBone = 	gameModel.children[0]

#==================================================================================================
# Recursive function to find every child of an SFM dag object. Used to get a list of bones.
#==================================================================================================
def getChildren(dag):	
	bones = []
	for i in dag.children:
		bones += [i]
		if i.children : 		#if it's not empty
			bones += getChildren(i)
	return bones

allBones = getChildren(gameModel)
controlGroups = getChildren(animSet.rootControlGroup)

Color1 = 		vs.Color( 0, 128, 255, 255 )	# Eg. "Face"
Color2 = 		vs.Color( 15, 128, 55, 255 )	# Eg. "Eyes"
Color3 = 		vs.Color( 30, 185, 85, 255 )	# Eg. "Eyebrows"
RightColor = 	vs.Color( 255, 0, 0, 255 )		# Eg. "Right Fingers"
LeftColor = 	vs.Color( 0, 255, 0, 255 )		# Eg. "Left Fingers"
GenitalColor = 	vs.Color( 230, 30, 200, 255 )	# Eg. "Vagina"

#==================================================================================================
# This allows me to write to the actual SFM console, rather than the script editor console (which is where print() writes)
#==================================================================================================
class MetsRigError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)
		

#==================================================================================================
# Sets groupNames control groups as hidden.
#==================================================================================================
def HideControlGroups( rig, rootGroup, *groupNames ):	
	for name in groupNames:	
		group = rootGroup.FindChildByName( name, False )
		if ( group != None ):
			rig.HideControlGroup( group )

#==================================================================================================
# Create the reverse foot control and operators for the foot on the specified side (rig_footroll)
#==================================================================================================
def CreateReverseFoot( controlName, sideName, helperControlGroup, footControlGroup ) :
	footRollDefault = 0.5
	rotationAxis = vs.Vector( 1, 0, 0 )
		
	# Construct the name of the dag nodes of the foot and toe for the specified side
	footName = "rig_foot_" + sideName
	toeName = "rig_toe_" + sideName	
	
	# Get the world space position and orientation of the foot and toe
	footPos = sfm.GetPosition( footName )
	footRot = sfm.GetRotation( footName )
	toePos = sfm.GetPosition( toeName )
	
	# Setup the reverse foot hierarchy such that the foot is the parent of all the foot transforms, the 
	# reverse heel is the parent of the heel, so it can be used for rotations around the ball of the 
	# foot that will move the heel, the heel is the parent of the foot IK handle so that it can perform
	# rotations around the heel and move the foot IK handle, resulting in moving all the foot bones.
	# root
	#   + rig_foot_R
	#	   + rig_knee_R
	#	   + rig_reverseHeel_R
	#		   + rig_heel_R
	#			   + rig_footIK_R
	
	# Construct the reverse heel joint this will be used to rotate the heel around the toe, and as
	# such is positioned at the toe, but using the rotation of the foot which will be its parent, 
	# so that it has no local rotation once parented to the foot.
	reverseHeelName = "rig_reverseHeel_" + sideName
	reverseHeelDag = sfm.CreateRigHandle( reverseHeelName, pos=toePos, rot=footRot, rotControl=False )
	sfmUtils.Parent( reverseHeelName, footName, vs.REPARENT_LOGS_OVERWRITE )
	
	# Construct the heel joint, this will be used to rotate the foot around the back of the heel so it 
	# is created at the heel location (offset from the foot) and also given the rotation of its parent.
	heelName = "rig_heel_" + sideName
	heelRot = sfm.GetRotation( reverseHeelName )
	heelDag = sfm.CreateRigHandle( heelName, pos=footPos, rot=footRot, posControl=True, rotControl=False )
	sfmUtils.Parent( heelName, reverseHeelName, vs.REPARENT_LOGS_OVERWRITE )
	
	# Create the ik handle which will be used as the target for the ik chain for the leg
	ikHandleName = "rig_footIK_" + sideName   
	ikHandleDag = sfmUtils.CreateHandleAt( ikHandleName, footName )
	sfmUtils.Parent( ikHandleName, heelName, vs.REPARENT_LOGS_OVERWRITE )
					
	# Create an orient constraint which causes the toe's orientation to match the foot's orientation
	footRollControlName = controlName + "_" + sideName
	toeOrientTarget = sfm.OrientConstraint( footName, toeName, mo=True, controls=False )
	footRollControl, footRollValue = sfmUtils.CreateControlledValue( footRollControlName, "value", vs.AT_FLOAT, footRollDefault, animSet, shot )
	
	# Create the expressions to re-map the footroll slider value for use in the constraint and rotation operators
	toeOrientExprName = "expr_toeOrientEnable_" + sideName	
	toeOrientExpr = sfmUtils.CreateExpression( toeOrientExprName, "inrange( footRoll, 0.5001, 1.0 )", animSet )
	toeOrientExpr.SetValue( "footRoll", footRollDefault )
	
	toeRotateExprName = "expr_toeRotation_" + sideName
	toeRotateExpr = sfmUtils.CreateExpression( toeRotateExprName, "max( 0, (footRoll - 0.5) ) * 140", animSet )
	toeRotateExpr.SetValue( "footRoll", footRollDefault )
							
	heelRotateExprName = "expr_heelRotation_" + sideName
	heelRotateExpr = sfmUtils.CreateExpression( heelRotateExprName, "max( 0, (0.5 - footRoll) ) * -100", animSet )
	heelRotateExpr.SetValue( "footRoll", footRollDefault )
		
	# Create a connection from the footroll value to all of the expressions that require it
	footRollConnName = "conn_footRoll_" + sideName
	footRollConn = sfmUtils.CreateConnection( footRollConnName, footRollValue, "value", animSet )
	footRollConn.AddOutput( toeOrientExpr, "footRoll" )
	footRollConn.AddOutput( toeRotateExpr, "footRoll" )
	footRollConn.AddOutput( heelRotateExpr, "footRoll" )
	
	# Create the connection from the toe orientation enable expression to the target weight of the 
	# toe orientation constraint, this will turn the constraint on an off based on the footRoll value
	toeOrientConnName = "conn_toeOrientExpr_" + sideName;
	toeOrientConn = sfmUtils.CreateConnection( toeOrientConnName, toeOrientExpr, "result", animSet )
	toeOrientConn.AddOutput( toeOrientTarget, "targetWeight" )
	
	# Create a rotation constraint to drive the toe rotation and connect its input to the 
	# toe rotation expression and connect its output to the reverse heel dag's orientation
	toeRotateConstraintName = "rotationConstraint_toe_" + sideName
	toeRotateConstraint = sfmUtils.CreateRotationConstraint( toeRotateConstraintName, rotationAxis, reverseHeelDag, animSet )
	
	toeRotateExprConnName = "conn_toeRotateExpr_" + sideName
	toeRotateExprConn = sfmUtils.CreateConnection( toeRotateExprConnName, toeRotateExpr, "result", animSet )
	toeRotateExprConn.AddOutput( toeRotateConstraint, "rotations", 0 );

	# Create a rotation constraint to drive the heel rotation and connect its input to the 
	# heel rotation expression and connect its output to the heel dag's orientation 
	heelRotateConstraintName = "rotationConstraint_heel_" + sideName
	heelRotateConstraint = sfmUtils.CreateRotationConstraint( heelRotateConstraintName, rotationAxis, heelDag, animSet )
	
	heelRotateExprConnName = "conn_heelRotateExpr_" + sideName
	heelRotateExprConn = sfmUtils.CreateConnection( heelRotateExprConnName, heelRotateExpr, "result", animSet )
	heelRotateExprConn.AddOutput( heelRotateConstraint, "rotations", 0 )
	
	if ( helperControlGroup != None ):
		sfmUtils.AddDagControlsToGroup( helperControlGroup, reverseHeelDag, ikHandleDag, heelDag )	   
	
	if ( footControlGroup != None ):
		footControlGroup.AddControl( footRollControl )
		
	return ikHandleDag

#==================================================================================================
# Compute the direction from boneA to boneB - used to find knee direction based on foot and toe
#==================================================================================================
def ComputeVectorBetweenBones( boneA, boneB, scaleFactor ):
	
	vPosA = vs.Vector( 0, 0, 0 )
	boneA.GetAbsPosition( vPosA )
	
	vPosB = vs.Vector( 0, 0, 0 )
	boneB.GetAbsPosition( vPosB )
	
	vDir = vs.Vector( 0, 0, 0 )
	vs.mathlib.VectorSubtract( vPosB, vPosA, vDir )
	vDir.NormalizeInPlace()
	
	vScaledDir = vs.Vector( 0, 0, 0 )
	vs.mathlib.VectorScale( vDir, scaleFactor, vScaledDir )	
	
	return vScaledDir
	
#==================================================================================================
# Make slaveBones look at boneViewTarget (unused)
#==================================================================================================	
def setUpAimConstraints(boneViewTarget, *slaveBones):
	if boneViewTarget is not None: 
		for bone in slaveBones:
			if bone is not None:
				sfm.PushSelection()				# Not sure what push and pop does in this context, can't test with script editor, but it crashes without this, so I assume it clears the selection.
				
				sfm.SelectDag( boneViewTarget )
				sfm.SelectDag( bone )

				sfm.AimConstraint( mo=False )	# The constraint is applied based on selection order, just like in SFM.

				sfm.PopSelection()

							
def createGroup(parentGroup, groupName, groupColor=Color1, selectable=True):
	### Checking if the group exists already, to avoid duplicate groups when removing and/or re-applying the rig ###
	retGroup = None												# Object to be returned later.
	if parentGroup.children:									# If the parent group has Any children
		for g in parentGroup.children:							# For each child
			if str(g.name) is groupName:						# If the child's name is the same as the given group's name
				retGroup = g									# Work with that child rather than creating a new group
				break
	
	if retGroup is None:										# If we didn't find an existing one, 
		retGroup = parentGroup.CreateControlGroup( groupName )	# create one.
	
	retGroup.SetGroupColor( groupColor, False )
	retGroup.SetSelectable( selectable )
	controlGroups.append(retGroup)
	return retGroup
				
#==================================================================================================
# Create a control group and move every bone and flex into it that matches the Regular Expression.
#==================================================================================================				
def regexGroup(groupName, parentGroup, groupColor, regex, selectable=True, debug=False):
	rei = re.compile(regex, re.I)								#Compile the regular expression with I for ignorecase
	
	retGroup = createGroup(parentGroup, groupName, groupColor, selectable)												# The control group that will be returned
	
	### Adding bones to our group ###
	for b in allBones:											# For each bone in the model
		if re.search(rei, str(b.name)):							# If our regex matches with the bone name
			sfmUtils.AddDagControlsToGroup( retGroup, b )		# Add the bone to the group we are working on. (Note: the bone control doesn't get a new reference, the existing one is "moved")
	
	### Adding flexes to our group ###
	for g in controlGroups:										# For each control group in the animationSet
		deleteStuff = []										# Stores the names of flexes that we replace(copy then delete original) 
		if groupName not in str(g.name):						# If the next group we are iterating through is NOT the group we are working on (without this we infinite loop)
			for dmEle in g.controls:							# For each control in the control group
				if type(dmEle) is vs.datamodel.CDmElement:		# If it's a flex (it still finds constraints I think, but it seems to not cause any issues so I ain't fixing what's not broken!)
					if debug: print("searching "+str(dmEle.name))
					if re.search(rei, str(dmEle.name)):		# If the regex matches the control name
						retGroup.controls.append(dmEle)		# Create a new reference to the control in our group's control
						if debug: print("FOUND!!!")
						deleteStuff.append(str(dmEle.name))	# Since we just created a new reference, we will later delete the original.
							
			for i, dmEle in reversed(list(enumerate(g.controls))):	# Iterating through the old group's controls, backwards, storing the (actual) index in "i" and the object in "dmEle"
				if deleteStuff:										# If there is anything to delete
					for d in deleteStuff:							# For each control we need to delete
						if(d == str(dmEle.name)):					# If the control was marked for deletion
							del(g.controls[i])						# Delete the reference from the old group

	
	retGroup.SetGroupColor( groupColor, False )
	retGroup.SetSelectable( selectable )
	return retGroup

#==================================================================================================
# Create left/right groups using regexGroup()
#==================================================================================================		
def stereoRegexGroup(groupName, regex, parentGL, parentGR, selectable=False):
	reL = "((?=.*("+regex+")))(?=.*(^L( |_)| L|\.L|left|_L)(?!ong|arge))"			# Adding parts that filter left and right sides to the passed in regex
	reR = "((?=.*("+regex+")))(?=.*(^R( |_)| R|\.R|right|_R)(?!oot|ing|ound|ip))"	# Excludes "hair.root", "finger_ring.L", etc
	
	GroupL = regexGroup( "Left %s" %groupName, parentGL, LeftColor, reL, selectable )
	GroupR = regexGroup( "Right %s" %groupName, parentGR, RightColor, reR, selectable )
	
	return [GroupL, GroupR]

#==================================================================================================
# Find the first child of a bone that matches the regex, even recursively
#==================================================================================================	
def FindChildBySubStr(parent, regex, recursive=False, required=False):
	rei = re.compile(regex, re.I)							# Compile the regex with I for ignorecase
	if parent is None:
		raise MetsRigError("This should never happen. Forgot to throw error earlier, when the parent of this bone was not found. TODO.")
	try:
		for b in parent.children:								# For each child
			if re.search(rei, str(b.name)):						# If the regex matches the child's name
				return b										# Return the child
			if recursive:										# If recursive is enabled and we didn't return yet
				search = FindChildBySubStr(b, regex, True)		# We have to go deeper
				if search is not None:							# If we got anything (We don't want to return None before checking everything!)
					return search								# Return it
	except AttributeError:	#I just want to throw more helpful errors.
		raise MetsRigError("Parent bone %s has no children, it was probably an incorrect match." %str(parent.name))
	### If nothing was returned ###
	if required:
		raise MetsRigError("Couldn't match any child of %s with regular expression: %s (recursive: %s)" %(str(parent.name), regex, recursive))
	return None

#==================================================================================================
# Find left/right children of left/right bones by regex - used for finding limb bones.
#==================================================================================================	
def findStereoChildByRegEx(parentL, parentR, regex, recursive=False, required=False):	#TODO use this to find rig bones.
	reL = "((?=.*("+regex+")))(?=.*( L ?|\.L|left|_L)(?!ong|arge))"
	reR = "((?=.*("+regex+")))(?=.*( R ?|\.R|right|_R)(?!oot|ing|ound|ip))"
	
	BoneL = FindChildBySubStr(parentL, reL, recursive, required)
	BoneR = FindChildBySubStr(parentR, reR, recursive, required)
	
	ret = [BoneL, BoneR]
	return ret
	
#==================================================================================================
# Building the IK rig #TODO - we could probably just have this outside of a function.
#==================================================================================================
def BuildRig():
	
	### Check if a rig is already applied by seeing if there is a "rig_root" element ###
	if sfmUtils.FindFirstDag( [ "rig_root" ], False ):
		raise MetsRigError("Rig already applied")
	
	# Start the biped rig to which all of the controls and constraints will be added
	# This rig object can be found under session.activeClip.subClipTrackGroup.Film.shot.scene.children
	rig = sfm.BeginRig( "rig_biped_" + animSet.GetName() + str(random.randint(0, 10000)));
	if ( rig == None ):
		return
	
	# Change the operation mode to passthrough so changes chan be made temporarily
	sfm.SetOperationMode( "Pass" )
	
	# Move everything into the reference pose
	sfm.SelectAll()
	sfm.SetReferencePose()
	
	
	### Quick and dirty eyeposing setup for MMD models ###
	#TODO create a rig handle if we can find eyes but can't find a viewTarget, Without crashing SFM.
	''' # This just kinda doesn't work very well.
	boneEyeL		= sfmUtils.FindFirstDag( [ "Eye.L", "Eyeball.L", "Eye_L", "Eyeball_L" ], False )
	boneEyeR		= sfmUtils.FindFirstDag( [ "Eye.R", "Eyeball.R", "Eye_R", "Eyeball_R" ], False )
	boneViewTarget	= sfmUtils.FindFirstDag( [ "Eye_viewTarget" ], False )	#TODO regex eyes
	setUpAimConstraints( boneViewTarget, boneEyeL, boneEyeR )
	'''
	#==================================================================================================
	# Finding the Spine bones!
	#==================================================================================================
	### Finding the Pelvis bone ###
	bonePelvis = FindChildBySubStr(rootBone, "Pelvis|^(?!.*(l|r)).*Hip", True)					# Attempting to find a Pelvis/Hip under the root bone
	if(bonePelvis == None):													# If there isn't any, the root bone is the pelvis
		bonePelvis = rootBone												# rootBone is never None, so no need to check that.
	
	boneSpines = [bonePelvis]												# Will store every spine bone, including necks and heads. Will use later to set up rig controllers.
	lastSpine = ""															# This will be used so that we know where to parent the Clavicle rig handles. (actual last spine, no necks or heads)
	
	spineReg = "^(?!.*(adjust).*).*(spine|torso|waist|chest|ribcage|COM|lowerback).*$"				# The regular expression that will hopefully only match spine bones that we need.
	neckReg = "^(?!.*(adjust|ribbon).*).*neck.*$"
	headReg = "^(?!.*(brow|lid|tong|jaw|band|\.R|\.L).*).*(head|s(k|c)ull).*$"
	
	### Finding the first Spine bone ###
	boneSpine = FindChildBySubStr(boneSpines[-1], spineReg)					# Attempt to find the first spine bone under the Pelvis
	lastSpine = boneSpine													# Set the lastSpine, in case this is the only spine bone we will find.
	if(lastSpine == None):													# If we didn't find a spine under the Pelvis
		boneSpine = FindChildBySubStr(rootBone, spineReg, True)					# Then look for one under the rootBone
		if boneSpine == None:												# If we still have nothing
			raise MetsRigError("Couldn't find any Spine bones.")				# Well, shit.
	
	lastSpine = boneSpine													# We always set lastSpine when we find a spine. (actual, no neck or head)
	boneSpines.append(boneSpine)											# And we always add it to boneSpines. (including neck and head)
	
	### Finding the rest of the Spine bones ###	
	while(True):															# TODO this could probably be done with some kind of super fancy recursion.
		boneSpine = FindChildBySubStr(boneSpines[-1], spineReg)				# Searching for spine under the last spine
		if(boneSpine != None):												# If we found something
			boneSpines.append(boneSpine)									# Add it and update lastSpine
			lastSpine = boneSpine
		else:																# If we did not find something
			boneSpine = FindChildBySubStr(boneSpines[-2], neckReg, True)	# Time to look for Necks, two spine bones behind, recursively...
			
			if(boneSpine != None and 												# If we found a neck AND
				not any(str(b.name) == str(boneSpine.name) for b in boneSpines)):	# This neck's name is Not equal to Any of the names in boneSpines
				boneSpines.append(boneSpine)								# Add it to boneSpines, but don't update lastSpine
			else:															# If we ran out of necks
				boneSpine = FindChildBySubStr(boneSpines[-1], headReg)		# Find heads!
				if(boneSpine != None):
					boneSpines.append(boneSpine)
					break;													#TODO Can't have multiple head bones because XNA models with bones under the Head like "head eyebrow left" that get matched.
				else:break
	
	
	#==============================================================================================
	# Find the bones in the model which will be used by the script
	#==============================================================================================
	boneRoot	  = sfmUtils.FindFirstDag( [ "RootTransform" ], True )
									   #V that .* is probably useless.
	excl = "^(?!.*(roll|twist|adjust|FK|ctr|ribbon|jiggle).*).*"	# If these are in the name of a bone, they probably aren't main limb bones.
	
	boneUpperLegs 	= findStereoChildByRegEx(	boneSpines[0],		boneSpines[0],		excl + "(hip|thigh|tight|upperleg|backleg)", True, True )
	boneLowerLegs 	= findStereoChildByRegEx(	boneUpperLegs[0],	boneUpperLegs[1],	excl + "(calf|knee|shin|lowerleg|backleg)", False, True )
	boneFeet 		= findStereoChildByRegEx(	boneLowerLegs[0],	boneLowerLegs[1],	excl + "(foot|toe|ankle)", True, True )
	boneToes 		= findStereoChildByRegEx(	boneFeet[0],		boneFeet[1],		excl + "(toe|paw)", True,  True )
	boneCollars 	= findStereoChildByRegEx(	boneSpines[1],		boneSpines[1],		excl + "(collar|clav|scapula|shoulder)", True, True )
	boneUpperArms 	= findStereoChildByRegEx(	boneCollars[0],		boneCollars[1],		excl + "(bicep|upperarm|shoulder|frontleg)", False, True )
	boneLowerArms 	= findStereoChildByRegEx(	boneUpperArms[0],	boneUpperArms[1],	excl + "(lowerarm|forearm|elbow|frontleg)", True, True )
	boneHands 		= findStereoChildByRegEx(	boneLowerArms[0],	boneLowerArms[1],	excl + "(hand|wrist|paw)", False, True )
	
	#==============================================================================================
	# Create the rig handles and constrain them to the bones we just found
	#==============================================================================================
	rigRoot	= sfmUtils.CreateConstrainedHandle(		"rig_root",		boneRoot,		bCreateControls=False )
	rigPelvis	= sfmUtils.CreateConstrainedHandle(	"rig_pelvis",	bonePelvis,		bCreateControls=False )
	
	rigFootR   = sfmUtils.CreateConstrainedHandle(	"rig_foot_R",	boneFeet[1],   	bCreateControls=False )
	rigToeR	= sfmUtils.CreateConstrainedHandle(		"rig_toe_R",	boneToes[1],	bCreateControls=False )
	rigCollarR = sfmUtils.CreateConstrainedHandle(	"rig_collar_R",	boneCollars[1],	bCreateControls=False )
	rigHandR   = sfmUtils.CreateConstrainedHandle(	"rig_hand_R",   boneHands[1],	bCreateControls=False )
	rigFootL   = sfmUtils.CreateConstrainedHandle(	"rig_foot_L",	boneFeet[0],	bCreateControls=False )
	rigToeL	= sfmUtils.CreateConstrainedHandle(		"rig_toe_L",	boneToes[0],	bCreateControls=False )
	rigCollarL = sfmUtils.CreateConstrainedHandle(	"rig_collar_L",	boneCollars[0],	bCreateControls=False )
	rigHandL   = sfmUtils.CreateConstrainedHandle(	"rig_hand_L",	boneHands[0],	bCreateControls=False )
	
	# Use the direction from the heel to the toe to compute the knee offsets, 
	# this makes the knee offset indpendent of the inital orientation of the model.
	vKneeOffsetR = ComputeVectorBetweenBones( boneFeet[1], boneToes[1], 10 )
	vKneeOffsetL = ComputeVectorBetweenBones( boneFeet[0], boneToes[0], 10 )
	
	rigKneeR   = sfmUtils.CreateOffsetHandle( "rig_knee_R",  boneLowerLegs[1], vKneeOffsetR,  bCreateControls=False )   
	rigKneeL   = sfmUtils.CreateOffsetHandle( "rig_knee_L",  boneLowerLegs[0], vKneeOffsetL,  bCreateControls=False )
	rigElbowR  = sfmUtils.CreateOffsetHandle( "rig_elbow_R", boneLowerArms[1], -vKneeOffsetR,  bCreateControls=False )
	rigElbowL  = sfmUtils.CreateOffsetHandle( "rig_elbow_L", boneLowerArms[0], -vKneeOffsetL,  bCreateControls=False )
	
	# Create a helper handle which will remain constrained to the each foot position that can be used for parenting.
	rigFootHelperR = sfmUtils.CreateConstrainedHandle( "rig_footHelper_R", boneFeet[1], bCreateControls=False )
	rigFootHelperL = sfmUtils.CreateConstrainedHandle( "rig_footHelper_L", boneFeet[0], bCreateControls=False )
	
	# Create a list of all of the rig dags
	allRigHandles = [ rigRoot,
					  rigCollarR, rigElbowR, rigHandR, rigKneeR, rigFootR, rigToeR,
					  rigCollarL, rigElbowL, rigHandL, rigKneeL, rigFootL, rigToeL ];
	
	### Creating rig handles for our Spine bones ###
	rigSpines = [rigPelvis]								# Nice little list to store them
	
	for b in boneSpines[1:]:							# For each spine bone after the first one (the Pelvis/Root)
		splitName = str(b.name).split("(")				# The original names look something like: "bone 2 (bip_spine0)". I want to get bip_spine0 from that.
		rigName = "rig_" + splitName[1][:-1]			# So we cut everything before "(" and leave the final character, which is always ")".
		rigSpine = sfmUtils.CreateConstrainedHandle( rigName,  b,  bCreateControls=False )
		rigSpines.append(rigSpine)
	
	for r in rigSpines:
		allRigHandles.append(r)							# Without this we crash, that is all I need to know.
	
	#==============================================================================================
	# Generate the world space logs for the rig handles and remove the constraints			# What?
	#==============================================================================================
	sfm.ClearSelection()
	sfmUtils.SelectDagList( allRigHandles )
	sfm.GenerateSamples()
	sfm.RemoveConstraints()								# I doubt this does what it sounds like it does.
	
	#==============================================================================================
	# Building the rig handle hierarchy
	#==============================================================================================
	sfmUtils.ParentMaintainWorld( rigSpines[0],		rigRoot )
	
	for i in range(1, len(rigSpines)):									# For each spine except the first
		sfmUtils.ParentMaintainWorld( rigSpines[i],	rigSpines[i-1] )	# Parent the spine bone to the one before it.
	
	sfmUtils.ParentMaintainWorld( rigFootHelperR,   rigRoot )
	sfmUtils.ParentMaintainWorld( rigFootHelperL,   rigRoot )
	sfmUtils.ParentMaintainWorld( rigFootR,			rigRoot )
	sfmUtils.ParentMaintainWorld( rigFootL,		 	rigRoot )
	sfmUtils.ParentMaintainWorld( rigKneeR,		 	rigFootR )
	sfmUtils.ParentMaintainWorld( rigKneeL,		 	rigFootL )
	sfmUtils.ParentMaintainWorld( rigToeR,		  	rigFootHelperR )
	sfmUtils.ParentMaintainWorld( rigToeL,		  	rigFootHelperL )
	
	sfmUtils.ParentMaintainWorld( rigCollarR,	   	lastSpine )			# And this is why we needed lastSpine!
	sfmUtils.ParentMaintainWorld( rigElbowR,		rigCollarR )
	sfmUtils.ParentMaintainWorld( rigHandR,			rigRoot )
	sfmUtils.ParentMaintainWorld( rigCollarL,	   	lastSpine )
	sfmUtils.ParentMaintainWorld( rigElbowL,		rigCollarL )
	sfmUtils.ParentMaintainWorld( rigHandL,			rigRoot )
	
	# Create the hips control, this allows a pelvis rotation that does not effect the spine,
	# it is only used for rotation so a position control is not created. Additionally add the
	# new control to the selection so the that set default call operates on it too.
	rigHips = sfmUtils.CreateHandleAt( "rig_hips", rigPelvis, False, True )
	sfmUtils.Parent( rigHips, rigPelvis, vs.REPARENT_LOGS_OVERWRITE )
	sfm.SelectDag( rigHips )

	# Set the defaults of the rig transforms to the current locations. Defaults are stored in local
	# space, so while the parent operation tries to preserve default values it is cleaner to just
	# set them once the final hierarchy is constructed.
	sfm.SetDefault()
	
	#==============================================================================================
	# Creating rig control groups
	#==============================================================================================
	rigBodyGroup = createGroup(rootGroup, "RigBody" )
	rigArmsGroup = createGroup(rootGroup, "RigArms" )
	rigLegsGroup = createGroup(rootGroup, "RigLegs" )
	
	rigBodyGroup.SetGroupColor( Color1, False )
	rigArmsGroup.SetGroupColor( Color1, False )
	rigLegsGroup.SetGroupColor( Color1, False )
	
	ArmsLRGroup = stereoRegexGroup( "Arm", "Hitler did nothing wrong", 			rigArmsGroup, rigArmsGroup, True )
	LegsLRGroup = stereoRegexGroup( "Leg", "Jet fuel can't melt dank memes", 	rigLegsGroup, rigLegsGroup, True ) 
	
	sfmUtils.AddDagControlsToGroup( ArmsLRGroup[1], rigHandR, rigElbowR, rigCollarR )
	sfmUtils.AddDagControlsToGroup( ArmsLRGroup[0], rigHandL, rigElbowL, rigCollarL )
	
	sfmUtils.AddDagControlsToGroup( LegsLRGroup[1], rigKneeR, rigFootR, rigToeR )
	sfmUtils.AddDagControlsToGroup( LegsLRGroup[0], rigKneeL, rigFootL, rigToeL )

	rigHelpersGroup = createGroup(rootGroup, "RigHelpers")
	
	#==============================================================================================
	# Create the reverse foot controls for both the left and right foot
	#==============================================================================================
	footIKTargetR = rigFootR
	footIkTargetL = rigFootL
	
	if ( boneToes ) :
		footRollIkTargetR = CreateReverseFoot( "rig_footRoll", "R", rigHelpersGroup, LegsLRGroup[1] )
		footRollIkTargetL = CreateReverseFoot( "rig_footRoll", "L", rigHelpersGroup, LegsLRGroup[0] )
		if ( footRollIkTargetR != None ) :
			footIKTargetR = footRollIkTargetR
		if ( footRollIkTargetL != None ) :
			footIkTargetL = footRollIkTargetL
	
	#==============================================================================================
	# Create constraints to drive the bone transforms using the rig handles
	#==============================================================================================
	
	# The following bones are simply constrained directly to a rig handle
	sfmUtils.CreatePointOrientConstraint( rigRoot,	  	boneRoot 		)
	sfmUtils.CreatePointOrientConstraint( rigHips,	  	bonePelvis 		)
	sfmUtils.CreatePointOrientConstraint( rigCollarR,   boneCollars[1]	)
	sfmUtils.CreatePointOrientConstraint( rigCollarL,   boneCollars[0]	)
	sfmUtils.CreatePointOrientConstraint( rigToeR,	  	boneToes[1]		)
	sfmUtils.CreatePointOrientConstraint( rigToeL,	  	boneToes[0]		)
	for k in range(1, len(rigSpines)):
		sfmUtils.CreatePointOrientConstraint( rigSpines[k], boneSpines[k] )
	
	# Create ik constraints for the arms and legs that will control the rotation of the hip / knee and 
	# upper arm / elbow joints based on the position of the foot and hand respectively.
	sfmUtils.BuildArmLeg( rigKneeR,		footIKTargetR,	boneUpperLegs[1],  boneFeet[1], 	True )
	sfmUtils.BuildArmLeg( rigKneeL,		footIkTargetL,	boneUpperLegs[0],  boneFeet[0],		True )
	sfmUtils.BuildArmLeg( rigElbowR,	rigHandR,		boneUpperArms[1],  boneHands[1],	True )
	sfmUtils.BuildArmLeg( rigElbowL,	rigHandL,		boneUpperArms[0],  boneHands[0],	True )
	
	#==============================================================================================
	# Create handles for the important attachment points 
	#==============================================================================================	
	attachmentGroup = rootGroup.CreateControlGroup( "Attachments" )
	attachmentGroup.SetGroupColor( Color1, False )
	attachmentGroup.SetVisible( False )
	
	sfmUtils.CreateAttachmentHandleInGroup( "pvt_heel_R",		attachmentGroup )
	sfmUtils.CreateAttachmentHandleInGroup( "pvt_toe_R",		attachmentGroup )
	sfmUtils.CreateAttachmentHandleInGroup( "pvt_outerFoot_R",	attachmentGroup )
	sfmUtils.CreateAttachmentHandleInGroup( "pvt_innerFoot_R",	attachmentGroup )
	
	sfmUtils.CreateAttachmentHandleInGroup( "pvt_heel_L",		attachmentGroup )
	sfmUtils.CreateAttachmentHandleInGroup( "pvt_toe_L",		attachmentGroup )
	sfmUtils.CreateAttachmentHandleInGroup( "pvt_outerFoot_L",	attachmentGroup )
	sfmUtils.CreateAttachmentHandleInGroup( "pvt_innerFoot_L",	attachmentGroup )
	
	#==============================================================================================
	# Bone organization!
	#==============================================================================================
	### Organizing rigBody and rigHelpersGroup, the old way ###
	sfmUtils.AddDagControlsToGroup( rigBodyGroup, rigRoot, rigHips, rigPelvis )
	for r in rigSpines:
		sfmUtils.AddDagControlsToGroup(rigBodyGroup, r)

	sfmUtils.AddDagControlsToGroup( rigHelpersGroup, rigFootHelperR, rigFootHelperL )
	
	### Deform bones that are now constrained and more or less useless ###
	BodyGroup = regexGroup( "Body", rootGroup, Color1, "genesis|root|head|neck|spine|pelvis|hip|COM")
	LegsGroup = regexGroup( "Legs", rootGroup, Color1, "leg|thigh|calf|upperleg|knee|foot(?!roll)|shin" )
	ArmsGroup = regexGroup( "Arms", rootGroup, Color1, "clav|collar|shoulder|upperarm|forearm|lowerarm|elbow|hand" )

	BodyGroup.AddChild( rigHelpersGroup )
	
	# Since these groups exist and contain shit under rootGroup by default, if I create them under BodyGroup, I'll be left with duplicate groups. (I only check for an existing group in the direct children of the parent group, when creating them, so that doesn't help)
	BodyGroup.AddChild( LegsGroup )			
	BodyGroup.AddChild( ArmsGroup )
	
	### Everything else! ###
	SpineAdjustGroup = regexGroup ( "Spine", rigBodyGroup, Color2, "^(?=.*(adjust|twist)).*(spine|belly|back|chest)", False )
	
	ArmTwistLRGroups = stereoRegexGroup( "Arm Adjust", "(?=.*(twist|adjust|FK|ctr))(?=.*(fore|arm|elbow|shoulder|shldr|clav|collar|wrist))|carpal|ulna|bicep|wrist", ArmsLRGroup[0], ArmsLRGroup[1], selectable=False )
	LegTwistLRGroups = stereoRegexGroup( "Leg Adjust", "(?=.*(twist|adjust|FK|ctr))(?=.*(leg|thitiggh|knee|calf|ankle))|tarsal|heel|achil", LegsLRGroup[0], LegsLRGroup[1], selectable=False )
	
	ToesLRGroup = stereoRegexGroup( "Toes", "toe|(?=.*(toe))(?=.*(big|index|middle|ring|pinky|small|big))", LegsLRGroup[0],LegsLRGroup[1] )
	
	FingerLRGroups = stereoRegexGroup( "Fingers",  "(finger|index|thumb|ring|pinky)|(?=.*(middle))(?=.*(finger|bip))|middle.$", ArmsLRGroup[0], ArmsLRGroup[1] ) #I can't assume everything that has "middle" in it is a finger, but everything that has both "middle" and "finger" in it should get matched.
	
	GenitalsGroup = regexGroup( "Genitals", rootGroup, Color1, "nipple|protrusion|pregnant|vag|butt|ass|genitals|breast|boob" ,False)
	BreastsLRGroup = stereoRegexGroup ( "Breast", "breast|pec|nipple", GenitalsGroup, GenitalsGroup, True )
	VaginaGroup = regexGroup( "Vagina", GenitalsGroup, GenitalColor, "^(?!.*throat.*).*(vag|(?<!naso)labia|pussy|bulge|ladypart).*$" ) #well, this is a mess. catches all bulges except throat bulges, and all labia except nasolabia.
	PenisGroup = regexGroup( "Penis", GenitalsGroup, GenitalColor, "(?<!o)pen|ball|sack|scrotum" )
	AnusGroup = regexGroup( "Anus", GenitalsGroup, GenitalColor, "anus|anal" )
	
	WingsGroup = regexGroup( "Wings", rootGroup, Color1, "wing" )
	WingsLRGroup = stereoRegexGroup( "Wing", "wing", WingsGroup, WingsGroup )
	
	TailGroup = regexGroup( "Tail", rootGroup, Color1, "tail" )
	
	HairGroup = regexGroup( "Hair", rootGroup, Color1, "hair", False )
	HairBackGroup = regexGroup( "Back", HairGroup, Color3, "(?=.*(hair))(?=.*(tail|back))" )
	HairFrontGroup = regexGroup( "Front", HairGroup, Color3, "(?=.*(hair))(?=.*(fringe|front|bang))" )
	HairLRGroups = stereoRegexGroup( "Hair", "hair|kanzashi", HairGroup, HairGroup ,True)
	
	FaceGroup = regexGroup( "Face", rootGroup, Color1, "face|teeth|throat|blush|laryngeal|melt", False )
	EyesGroup = regexGroup( "Eyes", FaceGroup, Color2, "eye|blink|closelid" ) #This matches eyebrows, eyelids and whatnot, so just make sure this stays Before those groups get defined.
	EyebrowsGroup = regexGroup( "Eyebrows", EyesGroup, Color3, "brow|eybrw|frown|sneer" )
	LowerEyelidsGroup = regexGroup( "Lower Eyelids", EyesGroup, Color3, "(?=.*(lid|eyld))(?=.*(low|lwr|bottom))" )
	UpperEyelidsGroup = regexGroup( "Upper Eyelids", EyesGroup, Color3, "(?=.*(lid|eyld))(?=.*(upper|upp?r|top))" )
	
	
	ForeHeadGroup = regexGroup( "Forehead", FaceGroup, Color2, "forehead|temple|scalp" )
	NoseGroup = regexGroup( "Nose", FaceGroup, Color2, "nose|nostril" )
	CheeksGroup = regexGroup( "Cheek", FaceGroup, Color2, "cheek|squint")
	JawGroup = regexGroup( "Mouth", FaceGroup, Color2, "jaw|chin|nasola|grin|mouth(?!.*corner)" )	#It is awkwardly important that this stays below the Vagina group definition.
	TongueGroup = regexGroup( "Tongue", JawGroup, Color3, "tongu?e|mlem")
	
	LipsGroup = regexGroup( "Lips", JawGroup, Color3, "platy|dimple|kiss|lip|smile|pucker|mouth.*(?=corner)" )
	
	EarsGroup = regexGroup( "Ears", FaceGroup, Color2, "(?<!for)ear" )	#don't fucking catch forearms.
	
	ClothesGroup = regexGroup( "Clothes", rootGroup, Color1, "shawl|panties|string|^(?!.*hair.*).*(canteen|rocket|pauldron|helm|backpiece|pad|armplate|armor|shield|brooch|band|quiver|belt|(^(?!.*(lip|lid)).*top)|(!<?el)bow|pants|shirt|tie|hanging|strap|scythe|skull_|flames|bra|coat|panty|glove|bikini|swimsuit|weapon|sword|shade|glass|spectacle|gun|headband|cloth|scarf|mask|flower|hairpiece|bunny|gear|pouch|mag|pistol|zip|backpad|chestcompress|visor|wibbly|timeywimey|jacket|pack|bag|droid|hood|bullet|bracelet|necklace|chain|flappy|radio|dress|stiletto).*$" , False)
	
	ClothesFlexGroup = regexGroup ( "Clothes", rootGroup, Color1, "fit(armpits|nipples|waist|default|feet|arm|leg|tit|breast|butt|chest|torso|upper|lower|top|thigh)|hide|^(?!.*lip.*).*shrink.*$|internal", False )
	ClothesLRGroups = stereoRegexGroup( "Clothes", "fringe", ClothesGroup, ClothesGroup )
	ClothesFrontGroup = regexGroup( "Front Clothes", ClothesGroup, Color2,"(?=.*(cloth))(?=.*(front))")
	ClothesBackGroup = regexGroup( "Back Clothes", ClothesGroup, Color2, "(?=.*(cloth))(?=.*(back))")
	
	RibbonsGroup = regexGroup( "Ribbons", ClothesGroup, Color2, "ribbon" )
	SkirtGroup = regexGroup( "Skirt", ClothesGroup, Color2, "skirt" )
	MercySkirtGroup = regexGroup ( "Devil Skirt", SkirtGroup, Color2, "skirt_d" )
	
	FuckedGroup = regexGroup( "Garbage", rootGroup, RightColor, "blender_implicit")

	#==============================================================================================
	# Finishing up
	#==============================================================================================
	
	# Set the control group visiblity, this is done through the rig so it can track which
	# groups it hid, so they can be set back to being visible when the rig is detached.
	### interesting, the above comment implies the rig object is related to what happens when the rig gets detached. I thought all it did was bake and remove all constraints.
	HideControlGroups( rig, rootGroup, "Body", "Arms", "Legs", "Unknown", "Other", "Root" )	  
		
	### Re-order the groups ###
	rootGroup.MoveChildToBottom( rigBodyGroup )
	rootGroup.MoveChildToBottom( rigLegsGroup )	
	rootGroup.MoveChildToBottom( rigArmsGroup )	  
	
	### Deleting empty groups ### #TODO - delete near empty groups when?
	rootGroup.DestroyEmptyChildren()
	
	
	print("RIG DONE")	#TODO could print some extra info or some shit.
	# End the rig definition
	sfm.EndRig()
	return
	
#==================================================================================================
# Script entry
#==================================================================================================

# Construct the rig for the selected animation set
BuildRig();