# Borders
`borders.py` is a helper script that takes a 3D mesh (OBJ), along with all its texture maps, and creates new copies of the texture maps with the mesh's triangles drawn on. This is helpful for visualizing which corner of its texture maps the mesh considers to be the origin. You will need to know this in order to produce vertical groups of mesh faces that have correctly-mapped skins.

## Dependencies and Set-Up

### NumPy
http://www.numpy.org/
Needed for vector and matrix math
### OpenCV
https://opencv.org/
The `borders.py` script really only uses OpenCV to load and measure texture maps. You could replace this with any other image library, but more intricate vision-related tasks will put OpenCV to full use. More thorough notes on installing OpenCV are found in the "Dependencies and Set-Up" section under "OBJ-Parse."
### face.py
The classes in this file assist the `vgroups.py` script. It should be in the same directory.

## Inputs

### Example Script Call
The only required argument is a 3D-mesh OBJ file, as seen here: `python borders.py mesh.obj`
Script performance can be modified by passing flags and arguments after the OBJ file. Please see these described below in "Parameters."

## Outputs

The script will create one new image file for every texture map in your OBJ mesh. These files will have the same name, plus `borders.` plus a two-character origin identifier, and finally the graphics extension of the original. These two-character identifiers are `ll` for "lower-left," `ul` for "upper-left," `ur` for "upper-right", and `lr` for "lower-right," indicating that the mesh considers (0, 0) to be in that corner. For example, if you called `python borders.py mesh.obj`, and the texture maps for `mesh.obj` are named `mesh_000.jpg`, `mesh_001.jpg`, `mesh_002.jpg`, etc. On assumption that the origin is in the lower-left, the resulting files would be `mesh_000.borders.ll.jpg`, `mesh_001.borders.ll.jpg`, `mesh_002.borders.ll.jpg`, etc.

## Parameters

### `-ll` Assume that the Origin is the Lower-Left
For example, `python borders.py mesh.obj -ll`

### `-ul` Assume that the Origin is the Upper-Left
For example, `python borders.py mesh.obj -ul`

### `-ur` Assume that the Origin is the Upper-Right
For example, `python borders.py mesh.obj -ur`

### `-lr` Assume that the Origin is the Lower-Right
For example, `python borders.py mesh.obj -lr`

### `-?`, `-help`, `--help` Help!
Display some notes on how to use this script.

# OBJ-Parse
OBJ-mesh file parsing code. The script `vgroups.py` parses an OBJ file, resolves triangle soup, and groups mesh faces into vertical groups.

## Dependencies and Set-Up

### NumPy
http://www.numpy.org/
Needed for vector math
### OpenCV
https://opencv.org/
In this case, we really only use OpenCV to load and measure texture maps. If you had to, you could swap this out for another image package. It made sense to use OpenCV here since it applies to other, related tasks.

That said, the Python installation of OpenCV will suffice for this script, as seen here: https://docs.opencv.org/4.1.0/d2/de6/tutorial_py_setup_in_ubuntu.html. Other vision-realated repositories will need to compile C++ code using the OpenCV libraries, which is a more involved installation. The following worked for us, installing OpenCV 3.1.0 on Ubuntu 16.04:
```
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install build-essential cmake pkg-config
sudo apt-get install git libgtk-3-dev
sudo apt-get install libjpeg8-dev libtiff5-dev libjasper-dev libpng12-dev libdc1394-22-dev libeigen3-dev libtheora-dev libvorbis-dev
sudo apt-get install libtbb2 libtbb-dev
sudo apt-get install libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
sudo apt-get install libxvidcore-dev libx264-dev sphinx-common yasm libfaac-dev libopencore-amrnb-dev libopencore-amrwb-dev libopenexr-dev libgstreamer-plugins-base1.0-dev libavutil-dev libavfilter-dev libavresample-dev
sudo apt-get install libatlas-base-dev gfortran
```
The foregone commands install all the requisite libraries. Now we install and build OpenCV:
```
sudo -s
cd /opt
wget -O opencv.zip https://github.com/Itseez/opencv/archive/3.1.0.zip
unzip opencv.zip
wget -O opencv_contrib.zip https://github.com/Itseez/opencv_contrib/archive/3.1.0.zip
unzip opencv_contrib.zip
mv /opt/opencv-3.1.0/ /opt/opencv/
mv /opt/opencv_contrib-3.1.0/ /opt/opencv_contrib/
cd opencv
mkdir release
cd release
cmake -D WITH_IPP=ON -D INSTALL_CREATE_DISTRIB=ON -D CMAKE_BUILD_TYPE=RELEASE -D CMAKE_INSTALL_PREFIX=/usr/local -D OPENCV_EXTRA_MODULES_PATH=/opt/opencv_contrib/modules /opt/opencv/
make
make install
ldconfig
exit
cd ~
```
If all went well, we should be able to query the version of the OpenCV installation:
```
pkg-config --modversion opencv
```
We should also be able to compile C++ code that uses OpenCV utilities. (Suppose we've written some such program, `helloworld.cpp`.)
```
g++ helloworld.cpp -o helloworld `pkg-config --cflags --libs opencv`
```
### Scikit Learn
https://scikit-learn.org/stable/
The KDTree data-type is the weapon of choice for finding multi-dimensional nearest neighbors. We will have to find nearest vertices to expand vertial groups across "triangle soup."
### face.py
The classes in this file assist the `vgroups.py` script. It should be in the same directory.

## Inputs

### Example Script Call
The only required argument is a 3D-mesh OBJ file to be parsed, as seen here: `python vgroups.py mesh.obj`
Script performance can be modified by passing flags and arguments after the OBJ file. Please see these described below in "Parameters."

## Outputs

### New OBJ Files
Once vertical groups have been identified, they are written to new OBJ files. Regardless of how else script performance was changed by command-line parameters, these output files are written from the largest to the smallest groups. The idea is that the larger groups are more likely to be useful, and that since parsing can be a time-consuming process, you may want to quit script execution early and neglect smaller groups. New OBJ files are named sequentially, "vertical_group_X.obj", where X is an integer greater-than or equal-to zero.

Note that these new OBJ files still depend on the same texture maps used by the original, entire mesh.

### Log File
The script also creates a log file which tells you which faces in the mesh belong to which vertical groups. This log is sorted descending by group area. Note that regardless of which conditions are placed on the OBJ output, the naming convention adheres to this log file. This would be why, say, new OBJ files might start with "vertical_group_24.obj" rather than with "vertical_group_0.obj". In other words, if you have told the script to only create new OBJ files of some subset of all vertical groups, the vertical groups which were discovered but not turned into new files will still be listed in the log.

## Parameters

### `-theta` Set an Acceptable Angle of Error (in Degrees)
The script `vgroups.py` reads the given OBJ file and finds mesh triangles with surface normals perpendicular to gravity. It then grows these regions outward along neighboring triangles with similar surface normals. Since scans are imperfect and sometimes noisy, this argument allows you to specify a degree of forgiveness between normal vectors. For example, if we pass `-theta 15` then two faces which are supposed to be part of the same vertical surface can differ by as many as 15 degrees and still be considered part of the same (mostly) flat surface.
e.g. `python vgroups.py mesh.obj -theta 15`
### `-cos` Set an Acceptable Angle of Error (as a Ratio)
Controls the same variable as above, but receives a ratio in [0.0, 1.0] rather than a number of degrees.
e.g. `python vgroups.py mesh.obj -cos 0.01`
### `-g` Set Gravity
By default, the gravity vector is [0.0, 0.0, 1.0], but you can change this by passing the `-g` flag and three arguments to describe another vector. The script will normalize your input for you.
e.g. `python vgroups.py mesh.obj -g 0 1 0`
Don't be mislead by thinking of this parameter as "gravity" in the sense of up or down. Really, all we want to define is the up-down axis. Mesh faces with surface normals perpendicular to up or down are vertically aligned faces, so `-g 0 0 -1` has the same effect as `-g 0 0 1`. Different systems consider different axes to be the up-down axis; sometimes it's Y, sometimes it's Z. You could deliberately change what the script considers up-down to find other groups. `-g 1 0 0` would find horizontally aligned groups like ceilings and floors.
### `-v` Enable Verbosity
Parsing and expanding vertical groups can be time-consuming. It's often helpful for the program to show signs of life. No argument follows `-v`.
### `-topn` Top N Groups
Once the OBJ file is parsed, adjacent triangles within an acceptable angle of error form groups. This parameter tells the script to discard all but the N largest groups. Calling the script like so, `python vgroups.py mesh.obj -topn 10`, asks for the largest ten.
### `-topp` Top Portion [0.0, 1.0] of Groups
As above, this parameter discards smaller groups. This parameter differs only in that it allows you to specify a real number in [0.0, 1.0]. To save only the largest quarter of groups:
e.g. `python vgroups.py mesh.obj -topp 0.25`
### `-agt` Groups with Areas Greater Than
Another group-culling parameter. The script computes triangle areas as it reads and parses the OBJ file. The `-agt` argument sets a lower bound for groups we will keep. If you would like to keep only those groups with areas greater than 1.5, you would call the script like so:
e.g. `python vgroups.py mesh.obj -agt 1.5`
Note that this can be combined with the "area less than" argument described below.
### `-alt` Groups with Areas Less Than
Another group-culling parameter. This one tells the script to keep all groups with areas with areas less than the given positive real number, effectively setting an upper bound. For example, if we would like to keep only groups with areas less than 1.0, we would call the script like so:
e.g. `python vgroups.py mesh.obj -alt 1.0`
This argument can be combined with the lower bound-setting argument, `-agt`, described above. These would be the arguments to use if, say, you were searching for vertical groups likely to contain an object of known size. Culling away groups too large and too small would save some searching work.
### `-epsilon` Set Minimum Distnace of Identical Vertices
"Triangle soup" is the name for meshes containing redundant vertices. Identifying redundant vertices had to be addressed so that we could expend vertical groups across triangles that were sptially aligned, though not connected by common vertices. This leads to the notion of "close enough to be considered the same," a value you can set by passing the `-epsilon` flag and a (small) non-negative real number. By default, `epsilon` is zero.
e.g. `python vgroups.py mesh.obj -epsilon 0.0001`
### `-ll`, `-ul`, `-ur`, `-lr` Set the Texture Map Origin
Different mesh-packing tools pack texture maps differently. These flags tell the script which corner of the texture maps to assume is (0, 0): respectively the "Lower-Left," "Upper-Left," "Upper-Right," and "Lower-Right." Use the `borders.py` script to have a look at where triangles fall on your textrue maps.
### `-?`, `-help`, `--help` Help!
Display some notes on how to use this script.

## Recommended Settings

Settings really depend on the mesh you intend to parse. Consider that `theta` is really the driving force of this script: setting it higher will absorb more mesh faces into fewer groups; setting it lower will produce more groups with fewer mesh faces. When trying to find a subset mesh of an object we as humans would consider "flat," try to gauge how "flat" a literal-minded program would find it. For instance we ran several tests searching for a control panel which, yes, was a flat surface, though the panel actually had raised buttons and a beveled central face. Finding the entire "flat" panel, then, complete with protrusions required making `theta` higher than we had expected.

## Citation

If this code was helpful for your research, please consider citing this repository.

```
@misc{obj-parse_2019,
  title={OBJ-Parse},
  author={Eric C. Joyce},
  year={2019},
  publisher={Github},
  journal={GitHub repository},
  howpublished={\url{https://github.com/EricCJoyce/OBJ-Parse}}
}
```
