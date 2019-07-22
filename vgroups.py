#  Eric Joyce, Stevens Institute of Technology, 2019

#  Find all triangles with surface normal perpendicular to gravity, within some degree of tolerance.
#  Vertical groups are grown from these triangles across adjacent and likewise aligned triangles
#  to form vertical groups.
#  We write these vertical groups to new OBJ files (subject to user-defined parameters).

#  python vgroups.py matterport_scan/5daf295b660043cead6640a9bc15c32a.obj -v -ll -theta 25

import sys
import re
import os
import numpy as np
from face import *													#  Our custom OBJ unpacker

#   argv[0] = vgroups.py
#   argv[1] = mesh file
#  {argv[2..n] = flags}

def main():
	if len(sys.argv) < 2:  ##########################################  Step 1: check arguments and files
		usage()
		return
	if not os.path.exists(sys.argv[1]):								#  Must have a 3D file
		print('Unable to find mesh file "' + sys.argv[1] + '"')
		return

	params = parseRunParameters()									#  Get command-line options
	if params['helpme']:											#  Did user ask for help?
		usage()														#  Display options
		return

	meshfn = sys.argv[1]											#  Save required arguments
	meshpath = '/'.join(meshfn.split('/')[:-1])

	params['mesh'] = meshfn											#  Add these to the parameter dictionary

	#################################################################  Step 2: Load the OBJ mesh model
	if params['verbose']:
		print('Loading OBJ file...')								#  http://www.andrewnoske.com/wiki/OBJ_file_format

																	#  Build a model we can query
	obj = Mesh(meshfn, meshpath, [], params['epsilon'], params['verbose'])
	obj.reconcile = True											#  (This is true by default anyway, but it's helpful
																	#   to point out here as different from 'find.py'.)
	obj.texmaporigin = params['origin']								#  Tell Mesh object where its texture map origin should be

	obj.load()
	if params['verbose']:
		print('  done')
		print('Connecting OBJ neighbors...')
	obj.computeFaceNeighbors()
	if params['verbose']:
		print('  done')

	#################################################################  Step 3: find vertical triangles
	if params['verbose']:
		print('Searching for vertical triangles among '+str(len(obj.faces))+'...')
		print('  (Tolerant within '+str(round(np.arccos(params['cos']) * 180 / np.pi))+' degrees)')
	verts = []														#  List of indices/keys for triangles passing verticality test

	gravity = np.array(params['gravity'])							#  Gravity as a unit vector
	gravity /= np.linalg.norm(gravity)

	for i in range(0, len(obj.faces)):
		n = obj.faces[i].norm
		cosTheta = n.dot(gravity)
		if np.abs(cosTheta) <= 1.0 - params['cos']:					#  Vertical enough!
			verts.append(i)

	vertLarge = [ (x, obj.faces[x].area) for x in verts ]			#  Build list of (face key, area) tuples
	vertLarge = sorted(vertLarge, reverse=True, key=lambda x: x[1])	#  Sort tuples descending by area

	#################################################################  Step 4: grow regions from triangles
	if params['verbose']:
		print('  done');
		print('Identified ' + str(len(vertLarge)) + ' vertical triangles.')

	lookup = {}														#  The list 'vertLarge' is sorted, and this may still be
	for faceArea in vertLarge:										#  helpful by rendering groups from most-likely to least-likely
		lookup[faceArea[0]] = [faceArea[1]]							#  to be large. This means the list of tuples should be
																	#  maintained even as we remove tuples from it as they're
																	#  added to groups. This lookup assists the remove() below.
	visited = {}													#  Track visited faces
	sections = []													#  List of lists of face-keys forming vertical groups
	while len(vertLarge) > 0:										#  Until we run out of vertical triangles...
		original = obj.faces[vertLarge[0][0]].norm					#  Save the normal of the central face
		sections.append( [] )										#  Begin a new growth
		queue = []
		queue.append( vertLarge[0] )								#  Seed growth with largest unvisited triangle tuple
		while len(queue) > 0:										#  Until the queue is empty...
			if params['verbose']:
				sys.stdout.write('  Growing region ' + str(len(sections))+': '+\
				                    str(len(sections[-1]))+':'+str(len(queue))+':'+str(len(vertLarge)) + ' ' * 24 + '\r')
				sys.stdout.flush()
			n = queue[0]											#  Pop an element
			queue = queue[1:]										#  Shorten the queue
			if n[0] not in visited:									#  If this face has not already been visited

				nNorm = obj.faces[n[0]].norm
				cosThetaGravity = nNorm.dot(gravity)				#  Valid addition should be perpendicular to gravity
				cosTheta = original.dot(nNorm)						#  AND parallel or diametrically opposed to original
																	#  If the candidate is vertical enough (perpendicular to gravity)
																	#  and parallel/opposed enough (to its neighbor)
				if np.abs(cosThetaGravity) <= 1.0 - params['cos'] and np.abs(cosTheta) >= params['cos']:
					sections[-1].append(n[0])						#  Add this face to the current growth
					visited[n[0]] = True							#  This belongs to something now:
					if n[0] in lookup:								#  if it's one of our verticals,
						vertLarge.remove(n)							#  remove it from the list of tuples
																	#  Consider its neighbors
					for neighbor in obj.faces[n[0]].neighbors:		#  'neighbor' is a face lookup key (zero-indexed int)
						if neighbor in lookup:						#  Lookup neighbor's area and add tuple to queue.
							queue.append( (neighbor, lookup[neighbor]) )
						else:										#  Otherwise, this triangle did not pass the verticality test
							queue.append( (neighbor, None) )		#  but is within our margin of forgiveness.
		print('')

	if params['verbose']:
		print('\nGrouped into ' + str(len(sections)) + ' vertical regions.')

	#################################################################  Step 5: compute areas of all regions and throw
	areas = {}														#  away all things out of user-specified range.

	for i in range(0, len(sections)):								#  Lookup: key = section number, value = region area
		areas[i] = 0
		for j in sections[i]:
			areas[i] += obj.faces[j].area
																	#  sectArea is array of tuples, (area, index in sections)
																	#  DESCENDING by area
	sectArea = sorted( [(v, k) for k, v in areas.items()], reverse=True )
	numbers = [x[1] for x in sectArea]								#  Preserve the group numbers so that we don't loose our
																	#  convenient mapping with the log file if we discard groups.
	fstr = ''														#  Write a log file of ALL groups:
	for i in range(0, len(sectArea)):								#  Group-number    Area    [Comma-separated-list-of-faces]
		fstr += str(i) + '\t' + str(sectArea[i][0]) + '\t[' + ', '.join( [ str(x) for x in sections[numbers[i]] ]) + ']\n'
	fh = open('vgroups.log', 'w')
	fh.write(fstr)
	fh.close()

	if params['topn'] is not None:									#  Keep only the top n
		sections = [sections[x[1]] for x in sectArea[:params['topn']]]
		numbers  =          [x[1] for x in sectArea[:params['topn']]]
	elif params['topp'] is not None:								#  Keep only the top percentage
		sections = [sections[x[1]] for x in sectArea[:int(round(params['topp'] * len(sectArea)))]]
		numbers  =          [x[1] for x in sectArea[:int(round(params['topp'] * len(sectArea)))]]
	elif params['agt'] is not None or params['alt'] is not None:	#  Area lower and upper bounds
		if params['agt'] is not None and params['alt'] is None:
			sections = [sections[x[1]] for x in sectArea if x[0] > params['agt']]
			numbers  =          [x[1] for x in sectArea if x[0] > params['agt']]
		elif params['alt'] is not None and params['agt'] is None:
			sections = [sections[x[1]] for x in sectArea if x[0] < params['alt']]
			numbers  =          [x[1] for x in sectArea if x[0] < params['alt']]
		elif params['alt'] is not None and params['agt'] is not None:
			sections = [sections[x[1]] for x in sectArea if x[0] < params['alt'] and x[0] > params['agt']]
			numbers  =          [x[1] for x in sectArea if x[0] < params['alt'] and x[0] > params['agt']]

	#################################################################  Step 6: Make a new OBJ file for each section.
	vertices = []													#  First, build a master reference of all
	tVertices = []													#  original 3D and 2D vertices
	fh = open(params['mesh'], 'r')
	lines = fh.readlines()
	for line in lines:
		arr = line.strip().split()
		if len(arr) > 0:
			if arr[0] == 'v':
				vertices.append( (float(arr[1]), float(arr[2]), float(arr[3])) )
			elif arr[0] == 'vt':
				tVertices.append( (float(arr[1]), float(arr[2])) )
	fh.close()

	for i in range(0, len(sections)):								#  For each vertical group...
		vctr = 1
		vtctr = 1
		vLookup = {}
		vtLookup = {}

		for f in sections[i]:										#  Build lookups of vertices used by faces in this group:
			for v in obj.faces[f].t3Dindices:						#  Key is the new index, value is the old index
				vLookup[vctr] = v
				vctr += 1
			for v in obj.faces[f].t2Dindices:
				vtLookup[vtctr] = v
				vtctr += 1
																	#  New OBJ file name
		newFilename = meshpath + '/vertical_group_' + str(numbers[i]) + '.obj'
		if params['verbose']:
			print('Writing "' + newFilename + '"')

		fh = open(newFilename, 'w')									#  Create the new file
		mtllibarr = params['mesh'].split('.')[0]
		fh.write('mtllib ' + mtllibarr.split('/')[-1] + '.mtl' + '\n\n')
		for v in range(1, vctr):									#  Write all vertices used for this face
			fh.write('v ' + str(vertices[vLookup[v] - 1][0]))
			fh.write(' '  + str(vertices[vLookup[v] - 1][1]))
			fh.write(' '  + str(vertices[vLookup[v] - 1][2]) + '\n')
		fh.write('\n')												#  Skip a line
		for v in range(1, vtctr):									#  Write texture vertices used for this face
			fh.write('vt ' + str(tVertices[vtLookup[v] - 1][0]))
			fh.write(' '   + str(tVertices[vtLookup[v] - 1][1]) + '\n')

		vLookup = {v: k for k, v in vLookup.iteritems()}			#  Reverse lookups: original vertex index
		vtLookup = {v: k for k, v in vtLookup.iteritems()}			#  gets us the new one

		currentTexmap = None
		v = 1
		vt = 1
		for f in sections[i]:										#  For every face in the group...
			if obj.faces[f].texmap != currentTexmap:
				fh.write('\nusemtl ' + obj.faces[f].texmap + '\n')
				currentTexmap = obj.faces[f].texmap
			fh.write('f ' + str(vLookup[obj.faces[f].t3Dindices[0]]) + '/' + str(vtLookup[obj.faces[f].t2Dindices[0]]))
			fh.write(' '  + str(vLookup[obj.faces[f].t3Dindices[1]]) + '/' + str(vtLookup[obj.faces[f].t2Dindices[1]]))
			fh.write(' '  + str(vLookup[obj.faces[f].t3Dindices[2]]) + '/' + str(vtLookup[obj.faces[f].t2Dindices[2]]) + '\n')
		fh.close()

	return

#  Parse the command line and set variables accordingly
def parseRunParameters():
	cosThetaTolerance = None										#  Specify how forgiving we want to be using cosine
	gravity = None													#  Specify gravity vector
	verbose = None
	topN = None
	topPercent = None
	areaGreaterThan = None
	areaLessThan = None
	epsilon = None
	origin = 'ul'													#  Default assumption: origin is upper-left
																	#  of every texture map
	helpme = False

	argtarget = None												#  Current argument to be set
																	#  Permissible setting flags
	flags = ['-theta', '-cos', '-g', '-v', \
	         '-topn', '-topp', '-agt', '-alt', '-epsilon', \
	         '-ul', '-ll', '-lr', '-ur', \
	         '-?', '-help', '--help']
	for i in range(2, len(sys.argv)):
		if sys.argv[i] in flags:
			argtarget = sys.argv[i]
			if argtarget == '-v':
				verbose = True
			elif argtarget == '-ll':
				origin = 'll'
			elif argtarget == '-ul':
				origin = 'ul'
			elif argtarget == '-ur':
				origin = 'ur'
			elif argtarget == '-lr':
				origin = 'lr'
			elif argtarget == '-?' or argtarget == '-help' or argtarget == '--help':
				helpme = True
		else:
			argval = sys.argv[i]

			if argtarget is not None:
				if argtarget == '-theta':							#  Following argument sets forgiveness using theta (degrees)
					cosThetaTolerance = np.cos(float(argval) * np.pi / 180.0)
				elif argtarget == '-cos':							#  Following argument sets forgiveness using cosine theta
					cosThetaTolerance = float(argval)
				elif argtarget == '-g':								#  Following THREE arguments set gravity vector
					 if gravity is None:
					 	gravity = []								#  Create the list
					 gravity.append(float(argval))					#  Add the first
				elif argtarget == '-topn':							#  Following argument sets the top N largest vertical groups
					topN = int(argval)
				elif argtarget == '-topp':							#  Following argument sets the largest portion of groups
					topPercent = float(argval)
				elif argtarget == '-agt':							#  Following argument sets the lower bound for group area
					areaGreaterThan = float(argval)
				elif argtarget == '-alt':							#  Following argument sets the upper bound for group area
					areaLessThan = float(argval)
				elif argtarget == '-epsilon':						#  Following argument sets epsilon
					epsilon = float(argval)
																	#  Use default values where necessary.
	if cosThetaTolerance is None:									#  Default COS-THETA (5 degrees)
		cosThetaTolerance = np.cos(5.0 * np.pi / 180.0)
	if gravity is None or len(gravity) != 3:						#  Default gravity
		gravity = [0.0, 0.0, 1.0]
	if verbose is None:												#  Default to no verbosity
		verbose = False
	if epsilon is None:												#  Default to no epsilon unless exact duplicate
		epsilon = 0.0

	params = {}
	params['cos'] = cosThetaTolerance
	params['gravity'] = gravity
	params['verbose'] = verbose
	params['topn'] = topN
	params['topp'] = topPercent
	params['agt'] = areaGreaterThan
	params['alt'] = areaLessThan
	params['epsilon'] = epsilon
	params['origin'] = origin
	params['helpme'] = helpme

	return params

def usage():
	print('Usage:  python vgroups.py mesh-filename <options, each preceded by a flag>')
	print(' e.g.:  python vgroups.py mesh.obj -theta 15 -v')
	print('Flags:  -theta   following argument is the acceptable angle of error, in degrees.')
	print('                 In other words, this sets the number of degrees by which two vectors')
	print('                 can differ and still be thought of as the same.')
	print('        -cos     following argument is the acceptable angle of error, as a ratio.')
	print('                 (See above)')
	print('        -g       following three arguments are the x, y, and z components of the')
	print('                 gravity vector.')
	print('        -v       enable verbosity')
	print('        -topn    following argument is the number of largest vertical groups to output.')
	print('        -topp    following argument is the portion of largest vertical groups to output.')
	print('        -agt     following argument is the area of vertical groups, greater than which we output.')
	print('        -alt     following argument is the area of vertical groups, less than which we output.')
	print('        -epsilon following argument is the distance within which two vertices are considered the same.')
	print('        -ul      tells the script to assume texture map origins are upper-left.')
	print('                 (This is the default assumption.)')
	print('        -ll      tells the script to assume texture map origins are lower-left.')
	print('        -lr      tells the script to assume texture map origins are lower-right.')
	print('        -ur      tells the script to assume texture map origins are upper-right.')
	return

if __name__ == '__main__':
	main()
