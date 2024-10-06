bl_info = {
    "name": "Scene exporter for colmap",
    "description": "Generates a dataset for colmap by exporting blender camera poses and rendering scene.",
    "author": "Ohayoyogi",
    "version": (0,0,1),
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

import mathutils
from pathlib import Path


class BlenderExporterForColmap(bpy.types.Operator, ExportHelper):
    bl_idname = "object.colmap_dataset_generator"
    bl_label = "Export as colmap dataset"
    bl_options = {"PRESET"}
    
    filename_ext = "."
    
    directory: StringProperty()
    
    filter_folder = True

    def export_dataset(self, context, dirpath: Path):
        scene = context.scene
        cameras = [ i for i in scene.objects if i.type == "CAMERA"]

        scale = scene.render.resolution_percentage / 100.0

        output_dir = dirpath
        cameras_file = output_dir / 'cameras.txt'
        images_file = output_dir / 'images.txt'
        images_dir = output_dir / 'images'
        points_file = output_dir / 'points3D.txt'

        output_dir.mkdir(parents=True, exist_ok=True)

        with open(cameras_file, 'w') as f_cam, open(images_file, 'w') as f_img, open(points_file, 'w') as f_points:
            f_cam.write(f'# Camera list generated by blender-exporter-colmap\n')
            f_img.write(f'# Image list generated by blender-exporter-colmap\n')
            f_points.write(f'# 3D point list generated by blender-exporter-colmap\n')
                
            for idx, cam in enumerate(sorted(cameras, key=lambda x: x.name_full + ".jpg")):
                filename = cam.name_full
                width = scene.render.resolution_x
                height = scene.render.resolution_y
                focal_length = cam.data.lens
                sensor_width = cam.data.sensor_width
                sensor_height = cam.data.sensor_height
                fx = focal_length * width / sensor_width
                fy = focal_length * height / sensor_height
                # fx, fy, cx, cy, k1, k2, p1, p2
                params = [fx, fy, width/2 , height/2, 0, 0, 0, 0]
                f_cam.write(f'{idx+1} OPENCV {width} {height} {" ".join(map(str,params))}\n')
                
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
                
                # IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME
                f_img.write(f'{idx+1} {qw} {qx} {qy} {qz} {tx} {ty} {tz} {idx+1} {filename}.jpg\n')
                f_img.write(f'\n')

                bpy.context.scene.camera = cam
                bpy.ops.render.render()
                bpy.data.images['Render Result'].save_render(str(images_dir / f'{filename}.jpg'))
                yield 100.0 * idx / len(cameras)
        
        yield 100.0

    def execute(self, context):
        dirpath = Path(self.directory)
        if not dirpath.is_dir():
            return { "WARNING", "Illegal directory was passed: " + self.directory }

        context.window_manager.progress_begin(0, 100)
        for progress in self.export_dataset(context, dirpath):
            context.window_manager.progress_update(progress)
        context.window_manager.progress_end()

        return {"FINISHED"}

def _blender_export_operator_function(topbar_file_import, context):
    topbar_file_import.layout.operator(
        BlenderExporterForColmap.bl_idname, text="Colmap dataset"
    )

def register():
    bpy.utils.register_class(BlenderExporterForColmap)
    bpy.types.TOPBAR_MT_file_export.append(_blender_export_operator_function)

def unregister():
    bpy.utils.unregister_class(BlenderExporterForColmap)

if __name__ == "__main__":
    register()