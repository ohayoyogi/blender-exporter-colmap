bl_info = {
    "name": "Scene exporter for colmap",
    "description": "Generates a dataset for colmap by exporting blender camera poses and rendering scene.",
    "author": "Ohayoyogi",
    "version": (0,1,0),
    "blender": (3,6,0),
    "location": "File/Export",
    "warning": "",
    "wiki_url": "https://github.com/ohayoyogi/blender-exporter-colmap",
    "tracker_url": "https://github.com/ohayoyogi/blender-exporter-colmap/issues",
    "category": "Import-Export"
}

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper
from . ext.read_write_model import write_model, Camera, Image

import mathutils
from pathlib import Path
import numpy as np

class BlenderExporterForColmap(bpy.types.Operator, ExportHelper):
   
    filename_ext = "."
    
    directory: StringProperty()
    
    filter_folder = True

    def export_dataset(self, context, dirpath: Path, format: str):
        scene = context.scene
        scene_cameras = [ i for i in scene.objects if i.type == "CAMERA"]

        output_format = format if format in ['.txt', '.bin'] else '.txt'

        scale = scene.render.resolution_percentage / 100.0

        output_dir = dirpath
        images_dir = output_dir / 'images'

        output_dir.mkdir(parents=True, exist_ok=True)

        cameras = {}
        images = {}
        for idx, cam in enumerate(sorted(scene_cameras, key=lambda x: x.name_full + ".jpg")):
            camera_id = idx+1
            filename = f'{cam.name_full}.jpg'
            width = scene.render.resolution_x
            height = scene.render.resolution_y
            focal_length = cam.data.lens
            sensor_width = cam.data.sensor_width
            sensor_height = cam.data.sensor_height
            fx = focal_length * width / sensor_width
            fy = focal_length * height / sensor_height
            # fx, fy, cx, cy, k1, k2, p1, p2
            params = [fx, fy, width/2, height/2, 0, 0, 0, 0]
            cameras[camera_id] = Camera(
                id=camera_id,
                model='OPENCV',
                width=width,
                height=height,
                params=params
            )

            image_id = camera_id
            rotation_mode_bk = cam.rotation_mode

            cam.rotation_mode = "QUATERNION"
            cam_rot_orig = mathutils.Quaternion(cam.rotation_quaternion)
            cam_rot = mathutils.Quaternion((
                cam_rot_orig.x,
                cam_rot_orig.w,
                cam_rot_orig.z,
                -cam_rot_orig.y))
            qw = cam_rot.w
            qx = cam_rot.x
            qy = cam_rot.y
            qz = cam_rot.z
            cam.rotation_mode = rotation_mode_bk

            T = mathutils.Vector(cam.location)
            T1 = -(cam_rot.to_matrix() @ T)

            tx = T1[0]
            ty = T1[1]
            tz = T1[2]
            images[image_id] = Image(
                id=image_id,
                qvec=np.array([qw, qx, qy, qz]),
                tvec=np.array([tx, ty, tz]),
                camera_id=camera_id,
                name=filename,
                xys=[],
                point3D_ids=[]
            )

            # Render scene
            bpy.context.scene.camera = cam
            bpy.ops.render.render()
            bpy.data.images['Render Result'].save_render(
                str(images_dir / filename))
            yield 100.0 * idx / (len(scene_cameras) + 1)

        write_model(cameras, images, {}, str(output_dir), output_format)
        yield 100.0

    def execute_(self, context, format):
        dirpath = Path(self.directory)
        if not dirpath.is_dir():
            return { "WARNING", "Illegal directory was passed: " + self.directory }

        context.window_manager.progress_begin(0, 100)
        for progress in self.export_dataset(context, dirpath, format):
            context.window_manager.progress_update(progress)
        context.window_manager.progress_end()

        return {"FINISHED"}

class BlenderExporterForColmapBinary(BlenderExporterForColmap):
    bl_idname = "object.colmap_dataset_generator_binary"
    bl_label = "Export as colmap dataset with binary format"
    bl_options = {"PRESET"}

    def execute(self, context):
        return super().execute_(context, '.bin')

class BlenderExporterForColmapText(BlenderExporterForColmap):
    bl_idname = "object.colmap_dataset_generator_text"
    bl_label = "Export as colmap dataset with text format"
    bl_options = {"PRESET"}

    def execute(self, context):
        return super().execute_(context, '.txt')

def _blender_export_operator_function(topbar_file_import, context):
    topbar_file_import.layout.operator(
        BlenderExporterForColmapText.bl_idname, text="Colmap dataset (.txt)"
    )
    topbar_file_import.layout.operator(
        BlenderExporterForColmapBinary.bl_idname, text="Colmap dataset (.bin)"
    )

def register():
    bpy.utils.register_class(BlenderExporterForColmapBinary)
    bpy.utils.register_class(BlenderExporterForColmapText)
    bpy.types.TOPBAR_MT_file_export.append(_blender_export_operator_function)

def unregister():
    bpy.utils.unregister_class(BlenderExporterForColmapBinary)
    bpy.utils.unregister_class(BlenderExporterForColmapText)

if __name__ == "__main__":
    register()