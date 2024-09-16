import os
import shutil
import zipfile
from datetime import datetime
import bpy
import bmesh
from mathutils import Vector
from .checkpoints import (
    recalc_ufit_paths,
    set_active_step,
    clear_checkpoints,
    get_workflow_step,
)
from ..utils import general, nodes, user_interface


#################################
# Start new / Start from existing
#################################
def start_modeling(context):
    # reset progress
    context.scene.ufit_progress = 0

    # set view_3d area full window
    # bpy.ops.wm.window_new()
    context.scene.ufit_full_screen = True


def start_from_existing(context, file_path_obj, path_consts, ui_consts, debug_step=None):
    modeling_folder = os.path.dirname(file_path_obj)
    checkpoints_dir = os.path.join(modeling_folder, "checkpoints")
    file_path = os.path.join(checkpoints_dir, 'uFit_settings.txt')
    add_on_version = user_interface.get_addon_version('uFit')

    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                if "uFit Version" in line:
                    ufit_version = line.split(":")[1].strip()
                    break
    else:
        raise Exception(f"The uFit_settings.txt file does not exist")

    if add_on_version.split('.')[0].strip() != ufit_version.split('.')[0].strip():
        raise Exception(f"The 3D model was created with uFit version {ufit_version} "
                        f"and that is not compatible with uFit version {add_on_version}."
                        f"Go to our website for more information")

    if os.path.isdir(checkpoints_dir):
        if context.scene.ufit_device_type not in modeling_folder:
            raise Exception(f"The chosen device type does not match the folder name")

        checkpoints_files = os.listdir(checkpoints_dir)
        checkpoints_files.reverse()
        latest_checkpoint = None
        active_step = None

        workflow = list(ui_consts['workflow'].keys())
        workflow.reverse()
        for step in workflow:
            for file in checkpoints_files:
                if file.startswith('ST_'):
                    wf_step = get_workflow_step(step, path_consts)
                    if wf_step \
                            and wf_step in file \
                            and 'blend1' not in file \
                            and (not debug_step or step == debug_step):
                        latest_checkpoint = os.path.join(checkpoints_dir, file)
                        active_step = step
                        break

            # also break out of big for loop
            if latest_checkpoint and active_step:
                break

        if latest_checkpoint:
            bpy.ops.wm.open_mainfile(filepath=latest_checkpoint)
            recalc_ufit_paths(context, modeling_folder, checkpoints_dir)
            set_active_step(context, active_step, path_consts, ui_consts)

            return None

    raise Exception(f"No checkpoint folder found. Please use 'Create New' for this scan.")


#################################
# Import Scan
#################################
def init_modeling_folders(context, filepath):

    file_name = os.path.basename(filepath)
    file_folder = os.path.dirname(filepath)

    # make sure you are not inside a modeling folder that already has checkpoints
    if not os.path.isdir(f'{file_folder}/checkpoints'):

        # define and create modeling folder
        ts = datetime.now().strftime("%y%m%d_%H%M%S")
        modeling_folder = f'{file_folder}/{context.scene.ufit_device_type}_{ts}'
        os.makedirs(modeling_folder)

        # scan file name and checkpoint folders
        context.scene.ufit_scan_filename = f'{file_name.split(".")[0]}'
        context.scene.ufit_folder_modeling = modeling_folder
        context.scene.ufit_folder_checkpoints = f'{modeling_folder}/checkpoints'

        # copy zip file to modeling folder
        # shutil.copy2(filepath, f'{modeling_folder}/{file_name}')
        obj_filepath = None

        if filepath.endswith(".obj"):

            png_file = next((os.path.join(file_folder, file) for file in os.listdir(file_folder) if file
                            .endswith(".png")), None)
            mtl_file = next((os.path.join(file_folder, file) for file in os.listdir(file_folder) if file
                            .endswith(".mtl")), None)
            if png_file and mtl_file:
                shutil.copy2(filepath, f'{modeling_folder}')
                shutil.copy2(png_file, f'{modeling_folder}')
                shutil.copy2(mtl_file, f'{modeling_folder}')
                obj_filepath = f'{modeling_folder}/{file_name}'  # not sure about the path
                context.scene.ufit_scan_filename = file_name.split(".")[0]
            else:
                raise Exception(f" MTL /PNG files are missing")
        elif filepath.endswith(".stl"):

            shutil.copy2(filepath, f'{modeling_folder}')
            obj_filepath = f'{modeling_folder}/{file_name}'
            context.scene.ufit_scan_filename = file_name.split(".")[0]

        elif filepath.endswith(".zip"):
           # extract the zip file
            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                zip_ref.extractall(modeling_folder)

            # store checkpoints folder and scan_filename
            for file in os.listdir(modeling_folder):
                if file.endswith(".obj") or file.endswith(".stl"):
                    obj_filepath = f'{modeling_folder}/{file}'
                    context.scene.ufit_scan_filename = file.split(".")[0]
                    break

        if not obj_filepath:
            raise Exception('Could not find an .obj or .stl file in scan folder')

        clear_checkpoints(context)
        return obj_filepath

    else:
        raise Exception(f"Found checkpoints folder. You can't use 'Create New' in this location.")


def import_3d_file(context, filepath):
    # delete everything from the scene
    general.delete_scene(context)
    # load the new object

    if filepath.endswith(".obj"):
        bpy.ops.import_scene.obj(filepath=filepath)
    elif filepath.endswith(".stl"):
        bpy.ops.import_mesh.stl(filepath=filepath)
    # rename the object
    obj_scan = bpy.context.selected_objects[0]
    obj_scan.name = 'uFit'

    # check if the object has a texture
    if not nodes.has_texture(obj_scan):
        context.scene.ufit_colored_scan = False

    # remove any rotation, location and scaling changes
    obj_scan.rotation_euler = (0, 0, 0)
    obj_scan.location = (0, 0, 0)
    obj_scan.scale = (1, 1, 1)

    # Perform scaling by user
    scale = context.scene.ufit_scan_scale_size
    obj_scan.scale = (scale, scale, scale)

    # activate object
    context.view_layer.objects.active = obj_scan

    # apply scaling
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    # Print the total surface area
    total_area = sum(f.area for f in bpy.context.active_object.data.polygons)
    print("Total Surface Area:", total_area)
    if total_area > 10:
        raise Exception(f"Surface area exceeds the limit. Please select a smaller model")








