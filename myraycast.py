import bpy
from mathutils import Vector, Matrix
import numpy as np
import math


def insideObject(point):
    # Define the starting point and direction of the ray
    direction1 = Vector((0, 0, 1))
    direction2 = Vector((0, 0, -1))
    # Shoot the ray and get the result
    hit1, location1, normal1, face_index1, object1, matrix1 = bpy.context.scene.ray_cast(point, direction1)
    hit2, location2, normal2, face_index2, object2, matrix2 = bpy.context.scene.ray_cast(point, direction2)
    # Check if the ray hit an object
    if object1 and object2 and object1.name == object2.name:
        return (object1, object2)
    else:
        # print("Ray did not hit any objects.")
        return None

po = Vector((0,0,1))
print(insideObject(po))
# exit()
angle = -41.273
xAxis = Vector((1,0,0))
yAxis = Vector((0,1,0))
zAxis = Vector((0,0,1))
corner = Vector()

rotMat = Matrix.Rotation(math.radians(angle), 3, 'Z')
xAxis.rotate(rotMat)
yAxis.rotate(rotMat)
zAxis.rotate(rotMat)

#represent part of the world with a 3D array
#each position in array is a number meaning what object/mesh is at that location

#set the dimensions of the array and the part of the world represented
sceneDims = np.array((16,17,4))
sceneOrigin = np.array((-12.74,0.04,-0.11))

#traversing a meter in the x, y, or z direction of the point cloud, you will pass 25 points
pointsPerMeter = 5

#x, y, z
arrDims = sceneDims * pointsPerMeter
stepSizes = sceneDims/(arrDims - 1)
arr = np.zeros(arrDims)

numInside = 0

print("STARTING")
for xSteps in range(arrDims[0]):
    for ySteps in range(arrDims[1]):
        for zSteps in range(arrDims[2]):
            stpAmts = (stepSizes * (xSteps,ySteps,zSteps))
            # print(type(stpAmts), type(stpAmts[0]))
            mappedPos = sceneOrigin + (xAxis * stpAmts[0] + yAxis * stpAmts[1] + zAxis * stpAmts[2])
            # print(mappedPos)
            insideOf = insideObject(mappedPos)
            arr[xSteps][ySteps][zSteps] = 1 if insideOf else 0
            if insideOf != None:
                numInside += 1
print(numInside, arrDims[0] * arrDims[1] * arrDims[2])

with open('/home/mary/Code/spatial-reasoning/custom_clevr/image_generation/test.npy', 'wb') as f:
    np.save(f, arr)