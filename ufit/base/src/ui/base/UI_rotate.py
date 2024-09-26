import bpy
from .....base.src.ui.utils.general import UFitPanel
from .....base.src.ui.utils.general import get_standard_navbox


class UIRotate(UFitPanel, bpy.types.Panel):
    def draw_base(self, context, ot_save_rotation, ot_mirror=None, ot_rotate_part_of_model=None):
        layout = self.layout

        if ot_mirror:
            row0 = layout.row()
            row0.operator(ot_mirror)


        
        if ot_rotate_part_of_model:
            box0 = layout.box()
            box0_row1 = box0.row()
            box0_row1.prop(context.scene, "ufit_rotate_part_of_model", text="Enable Scan Adjustment")
            box0_row2 = box0.row()
            box0_row2.label(text="Uncheck the box to confirm.")


        get_standard_navbox(self.layout, "ufit_operators.prev_step", ot_save_rotation)
