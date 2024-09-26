import os
import bpy
import math
import bpy.utils.previews
from ..operators.utils import general, user_interface, color_attributes, nodes
from ..operators.core import checkpoints
from ..operators.core.sculpt import color_attr_select


# We can store multiple preview collections here,
preview_collections = {}


#################################
# Callbacks
#################################
def full_screen(self, context):
    user_interface.set_full_screen(self.ufit_full_screen)
    # bpy.ops.wm.window_fullscreen_toggle()


def quad_view(self, context):
    user_interface.set_quad_view(self.ufit_quad_view)


def orthographic_view(self, context):
    user_interface.set_ortho_view(self.ufit_orthographic_view)


# function that dynamically sets the ufit_checkpoints enum
def checkpoint_items(self, context):
    enum_items = []
    for checkpoint in context.scene.ufit_checkpoint_collection:
        name = str(checkpoint.name)
        item = (name, name, name)
        enum_items.append(item)

    # reverse the list so that the last item appears first
    enum_items.reverse()

    return enum_items


def show_prescale_update(self, context):
    obj = bpy.data.objects['uFit_Prescale']
    if self.ufit_show_prescale:
        obj.hide_set(False)
    else:
        obj.hide_set(True)


def show_original_update(self, context):
    # ufit_original = bpy.data.objects['uFit_Original']
    ufit_original = bpy.data.objects['uFit_Measure']  # temporary workaround to avoid same color
    if self.ufit_show_original:
        ufit_original.hide_set(False)
    else:
        ufit_original.hide_set(True)


def update_colors_enable(self, context):
    if self.ufit_enable_colors:
        user_interface.set_shading_material_preview_mode()
    else:
        user_interface.set_shading_solid_mode(light='STUDIO', color_type='MATERIAL')


def update_vertex_color_all(self, context):
    ufit_obj = bpy.data.objects['uFit']
    if self.ufit_vertex_color_all:
        color_attributes.reset_color_attribute(ufit_obj, color_attr_select, color=(0.0325735, 0.78, 0.0565021, 1))
    else:
        color_attributes.reset_color_attribute(ufit_obj, color_attr_select, color=(1, 1, 1, 1))


def sculpt_mode_update(self, context):
    if self.ufit_sculpt_mode == 'guided':
        bpy.ops.object.mode_set(mode='VERTEX_PAINT')
        context.scene.tool_settings.unified_paint_settings.size = 30
    else:
        bpy.ops.object.mode_set(mode='SCULPT')
        context.scene.ufit_sculpt_brush = self.ufit_sculpt_brush  # trigger the sculpt_brush_update_function
        checkpoints.fill_history_with_null_operations()  # fill the history with null operations so that the user cannot switch back to vertex paint mode using crtl-z


def sculpt_brush_update(self, context):
    if self.ufit_sculpt_brush == 'push_brush':
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
        bpy.data.brushes["SculptDraw"].direction = 'SUBTRACT'
    elif self.ufit_sculpt_brush == 'pull_brush':
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
        bpy.data.brushes["SculptDraw"].direction = 'ADD'
    elif self.ufit_sculpt_brush == 'smooth_brush':
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Smooth")
        bpy.data.brushes["Smooth"].direction = 'SMOOTH'
    elif self.ufit_sculpt_brush == 'flatten_brush':
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Flatten")
        bpy.data.brushes["Flatten/Contrast"].direction = 'FLATTEN'


def cutout_style_update(self, context):
    ufit_obj = bpy.data.objects['uFit']
    cut_obj = bpy.data.objects['uFit_Cutout']

    if self.ufit_cutout_style == 'free':
        # activate uFit
        general.activate_object(context, ufit_obj, mode='OBJECT')

        # hide the cutout object
        cut_obj.hide_set(True)

        # set annotation tool
        bpy.ops.wm.tool_set_by_id(name='builtin.annotate')

        # activate snapping
        bpy.context.scene.tool_settings.use_snap = True

    elif self.ufit_cutout_style == 'straight':
        # make uFit unselectable
        ufit_obj.select_set(False)
        ufit_obj.hide_select = True

        # unhide cutter object
        cut_obj.hide_set(False)
        cut_obj.select_set(True)
        cut_obj.hide_select = False

        # activate the cutter object
        general.activate_object(context, cut_obj, mode='OBJECT')

        # set the ufit plane operation to move
        context.scene.ufit_plane_operation = 'move'

        # deactivate snapping
        bpy.context.scene.tool_settings.use_snap = False


def plane_operation_update(self, context):
    if bpy.context.scene.ufit_plane_operation == 'move':
        bpy.ops.wm.tool_set_by_id(name="builtin.move")

    elif bpy.context.scene.ufit_plane_operation == 'rotate':
        bpy.ops.wm.tool_set_by_id(name="builtin.rotate")

    elif bpy.context.scene.ufit_plane_operation == 'scale':
        bpy.ops.wm.tool_set_by_id(name="builtin.scale")


def mean_tilt_update(self, context):
    tilt = int(self.ufit_mean_tilt)

    # select all of the curve
    bpy.ops.curve.select_all(action='SELECT')

    # set the tilt
    bpy.ops.curve.tilt_clear()  # first clear the tilt
    bpy.ops.transform.tilt(value=math.radians(tilt),
                           mirror=False,
                           use_proportional_edit=False,
                           proportional_edit_falloff='SMOOTH',
                           proportional_size=1,
                           use_proportional_connected=False,
                           use_proportional_projected=False)

    # deselect all of the curve
    bpy.ops.curve.select_all(action='DESELECT')


def cutout_selection_update(self, context):
    ufit_part1 = bpy.data.objects['uFit_part1']
    ufit_part2 = bpy.data.objects['uFit_part2']

    if self.cutout_selection == 'ufit_part1':
        # activate uFit
        general.activate_object(context, ufit_part1, mode='OBJECT')
    else:
        general.activate_object(context, ufit_part2, mode='OBJECT')


def draw_type_update(self, context):
    ufit_obj = bpy.data.objects['uFit']
    general.activate_object(context, ufit_obj, mode='OBJECT')

    general.remove_all_modifiers(ufit_obj)

    if self.ufit_draw_type == 'free':
        color_attributes.activate_color_attribute(ufit_obj, 'draw_selection')
        nodes.set_voronoi_geometry_nodes_one(ufit_obj, tree_name="Voronoi Nodes Empty",
                                             color_attr_name='draw_selection')
        general.activate_object(context, ufit_obj, mode='VERTEX_PAINT')
        context.scene.ufit_voronoi_size = 'empty'

    elif self.ufit_draw_type == 'solid':
        # add a solididfy modifier on uFit
        solidify_mod = ufit_obj.modifiers.new(name="Solidify", type="SOLIDIFY")
        solidify_mod.offset = 1
        solidify_mod.use_even_offset = False  # DO NOT USE EVEN OFFSET
        solidify_mod.thickness = context.scene.ufit_solidify_thickness / 1000  # one mm of thickness

    elif self.ufit_draw_type == 'voronoi':
        context.scene.ufit_voronoi_type = 'voronoi_one'


def voronoi_type_update(self, context):
    ufit_obj = bpy.data.objects['uFit']
    general.activate_object(context, ufit_obj, mode='OBJECT')

    general.remove_all_modifiers(ufit_obj)

    if self.ufit_voronoi_type == 'voronoi_one':
        color_attributes.activate_color_attribute(ufit_obj, 'voronoi_one_selection')
        nodes.set_voronoi_geometry_nodes_one(ufit_obj, tree_name="Voronoi Nodes One",
                                             color_attr_name='voronoi_one_selection')
        general.activate_object(context, ufit_obj, mode='VERTEX_PAINT')
        context.scene.ufit_voronoi_size = 'medium'
    elif self.ufit_voronoi_type == 'voronoi_two':
        color_attributes.activate_color_attribute(ufit_obj, 'voronoi_two_selection')
        decimate_mod = ufit_obj.modifiers.new(name="Decimate", type="DECIMATE")
        decimate_mod.ratio = 0.01

        nodes.set_voronoi_geometry_nodes_two(ufit_obj, tree_name="Voronoi Nodes Two",
                                             color_attr_name='voronoi_two_selection')
        general.activate_object(context, ufit_obj, mode='OBJECT')


def draw_thickness_update(self, context):
    node_tree = bpy.data.node_groups['Voronoi Nodes Empty']
    node_tree.nodes['ufit_extrude_node'].inputs[3].default_value = self.ufit_free_draw_thickness/1000


def solidify_thickness_update(self, context):
    ufit_obj = bpy.data.objects['uFit']

    solidify_mod = ufit_obj.modifiers["Solidify"]
    solidify_mod.thickness = self.ufit_solidify_thickness / 1000


def voronoi_one_thickness_update(self, context):
    node_tree = bpy.data.node_groups['Voronoi Nodes One']
    node_tree.nodes['ufit_extrude_node'].inputs[3].default_value = self.ufit_voronoi_one_thickness / 1000


def voronoi_two_thickness_update(self, context):
    node_tree = bpy.data.node_groups['Voronoi Nodes Two']
    node_tree.nodes['ufit_extrude_node'].inputs[3].default_value = self.ufit_voronoi_two_thickness / 1000


def voronoi_size_update(self, context):
    node_tree = None
    if context.scene.ufit_draw_type == 'free':
        node_tree = bpy.data.node_groups['Voronoi Nodes Empty']
    elif context.scene.ufit_draw_type == 'voronoi' and context.scene.ufit_voronoi_type == 'voronoi_one':
        node_tree = bpy.data.node_groups['Voronoi Nodes One']

    if node_tree:
        compare_node = node_tree.nodes['ufit_compare_node']

        if self.ufit_voronoi_size == 'very_small':
            compare_node.inputs[1].default_value = 0.3
        elif self.ufit_voronoi_size == 'small':
            compare_node.inputs[1].default_value = 0.25
        elif self.ufit_voronoi_size == 'medium':
            compare_node.inputs[1].default_value = 0.2
        elif self.ufit_voronoi_size == 'big':
            compare_node.inputs[1].default_value = 0.15
        elif self.ufit_voronoi_size == 'very_big':
            compare_node.inputs[1].default_value = 0.1
        elif self.ufit_voronoi_size == 'empty':
            compare_node.inputs[1].default_value = 0


def flare_tool_update(self, context):
    # (re)select vertices from cutout edge
    # when the user switches tool, it can be used as a reset to reselect the edge
    ufit_obj = bpy.data.objects['uFit']
    vgs = general.get_all_cutout_edges(context)
    general.select_vertices_from_vertex_groups(context, ufit_obj, vg_names=vgs)

    user_interface.set_active_tool(self.ufit_flare_tool)


def get_flare_height(self):
    return bpy.context.tool_settings.proportional_size*100


def set_flare_height(self, value):
    bpy.context.tool_settings.proportional_size = value/100
    self["flare_height"] = value


def xray_update(self, context):
    user_interface.set_xray(context.scene.ufit_x_ray)


def show_connector_update(self, context):
    conn_obj = bpy.data.objects['Connector']
    conn_obj.hide_set(not context.scene.ufit_show_connector)


def alignment_tool_update(self, context):
    user_interface.set_active_tool(self.ufit_alignment_tool)


def alignment_object_update(self, context):
    # unhide connector
    if self.ufit_alignment_object == 'Connector':
        context.scene.ufit_show_connector = True
        context.scene.ufit_alignment_tool = 'builtin.move'

    # activate object
    obj = bpy.data.objects[self.ufit_alignment_object]
    general.activate_object(context, obj, 'OBJECT')


def smooth_borders_update(self, context):
    ufit_obj = bpy.data.objects['uFit']
    ufit_obj.modifiers['Corrective Smooth'].show_viewport = self.ufit_smooth_borders


def show_inner_part_update(self, context):
    # only hide the uFit object so that the inner part becomes visible
    ufit_obj = bpy.data.objects['uFit']
    ufit_obj.hide_set(context.scene.ufit_show_inner_part)

    # also hide ufit_original
    context.scene.ufit_show_original = False

    # ufit_inner_obj = bpy.data.objects['uFit_Inner']
    # ufit_inner_obj.hide_set(not context.scene.ufit_show_inner_part)


# # function is directly called from operator as callback
# def rotation_update(self, context):
#     objs = [obj for obj in bpy.data.objects if obj.name.startswith("uFit")]
#     ufit_circum_objects = [obj for obj in bpy.data.objects if obj.name.startswith("Circum_")]
#
#     objs.extend(ufit_circum_objects)
#
#     for obj in objs:
#         obj.rotation_euler.x = math.radians(context.scene.ufit_x_rotation)
#         obj.rotation_euler.y = math.radians(context.scene.ufit_y_rotation)
#         obj.rotation_euler.z = math.radians(context.scene.ufit_z_rotation)
#
#
# def move_update(self, context):
#     objs = [obj for obj in bpy.data.objects if obj.name.startswith("uFit")]
#     ufit_circum_objects = [obj for obj in bpy.data.objects if obj.name.startswith("Circum_")]
#
#     objs.extend(ufit_circum_objects)
#
#     default_z_loc = bpy.context.scene.bl_rna.properties['ufit_z_move'].default
#     for obj in objs:
#         obj.location.x = context.scene.ufit_x_move / 100
#         obj.location.y = -context.scene.ufit_y_move / 100
#         obj.location.z = context.scene.ufit_z_move / 100


# def connector_move_update(self, context):
#     conn_obj = bpy.data.objects['Connector']
#     conn_obj.location.z = context.scene.ufit_connector_move / 100


def enum_previews_for_assistance(self, context):
    if context.scene.ufit_assistance_previews_dir:
        # Get the preview collection, create new if not exists.
        pcoll = preview_collections.get('assistance')
        if not pcoll:
            pcoll = bpy.utils.previews.new()
            pcoll.my_previews_dir = ""
            pcoll.my_previews = ()
            preview_collections['assistance'] = pcoll

        enum_previews = user_interface.enum_previews_from_directory_items(context, pcoll,
                                                                          context.scene.ufit_assistance_previews_dir)

        return enum_previews

    return []


def rotate_part_of_model(self, context):
    ufit_obj = bpy.data.objects['uFit']

    # Select object mode
    general.activate_object(context, ufit_obj, mode='OBJECT')

    if not self.ufit_rotate_part_of_model:
        # Restore quad view
        user_interface.set_quad_view(True)

        # Permanently apply changes to the uFit object
        bpy.ops.object.modifier_apply({"object": ufit_obj}, modifier='Lattice')

        # Remove lattice
        lattice_obj = bpy.data.objects["Lattice"]
        general.activate_object(context, lattice_obj, mode='OBJECT')
        bpy.ops.object.delete()

        # Remove lattice modifier
        general.remove_all_modifiers(ufit_obj)

        # Activate the uFit object
        general.activate_object(context, ufit_obj, mode='OBJECT')

    else:
        # Remove quad view
        user_interface.set_quad_view(False)

        # Add lattice modifier to the uFit object, only small changes allowed (strength=0.2)
        lattice_obj = general.add_lattice_modifier(context, ufit_obj, strength=0.2)

        # Activate built-in rotation tool
        general.activate_object(context, lattice_obj, mode='EDIT')
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        user_interface.set_active_tool('builtin.rotate')
