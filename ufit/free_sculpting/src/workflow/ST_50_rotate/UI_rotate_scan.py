from .....base.src.ui.base.UI_rotate import UIRotate
from ...free_sculpting_constants import fs_ui_consts


class UIRotateFS(UIRotate):
    bl_idname = "VIEW3D_PT_fs_rotate_scan"
    bl_label = fs_ui_consts['workflow']['rotate']['ui_name']

    def draw(self, context):
        self.draw_base(context,
                       ot_save_rotation="fs_operators.save_rotation",
                       ot_mirror="fs_operators.mirror",
                       ot_rotate_part_of_model="fs_operators.rotate_part_of_model")

    @classmethod
    def poll(cls, context):
        return (context.scene.ufit_active_step == 'rotate'
                and context.scene.ufit_device_type == 'free_sculpting')
