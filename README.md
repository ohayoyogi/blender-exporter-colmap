# blender-exporter-colmap

Blender plugin which generates a dataset for colmap by exporting blender camera poses and rendering scene.

## output format

This script generate these files on a selected folder.

|Name|Description|
|:--|:--|
|📂images|Contains rendered images. Each image is rendered with  parameters (intrinsic and pose) of camera in the scene.|
|📄cameras.txt|Contains intrinsic paramters of each camera.|
|📄images.txt|Contains camera poses of each camera.|
|📄points3D.txt|Empty file|

For details, please refer to [COLMAP documentation](https://colmap.github.io/format.html).
