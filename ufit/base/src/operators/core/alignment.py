import os
import bpy
from mathutils import Vector
from ..utils import annotations, general, user_interface


#########################################
# Import Connector
#########################################
def prep_import_connector(context):
    # change orthographic
    user_interface.change_orthographic('BOTTOM')

    # activate grease pensil
    user_interface.activate_new_grease_pencil(context, name='Selections', layer_name='Connector_Loc')

    # deactivate snapping
    bpy.context.scene.tool_settings.use_snap = False


def import_connector(context, path_consts, connector_type, foot_type, amputation_side):
    objs = [obj for obj in bpy.data.objects if obj.name.startswith("uFit")]
    ufit_circum_objects = [obj for obj in bpy.data.objects if obj.name.startswith("Circum_")]
    objs.extend(ufit_circum_objects)

    # switch origin to center of mass
    ufit_obj = bpy.data.objects['uFit']
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='MEDIAN')

    # move the object to origin of world
    anchor_point = Vector((ufit_obj.location.x, ufit_obj.location.y, 0))

    # set new anchor point for all ufit objects and circums
    default_z_loc = 0.4
    if context.scene.ufit_device_type == 'transfemoral':
        default_z_loc = 0.6

    for obj in objs:
        obj.hide_set(False)
        general.activate_object(context, obj, mode='OBJECT')
        general.set_object_origin(anchor_point)
        general.move_object(obj, -anchor_point)  # bring to the center
        general.move_object(obj, Vector((0, 0, default_z_loc)))  # move up
        if obj.name != 'uFit':
            obj.hide_set(True)

    # go to object mode
    general.activate_object(context, ufit_obj, mode='OBJECT')
    user_interface.set_shading_solid_mode()

    # set connector file params
    connectors_dir = os.path.join(os.path.dirname(__file__), f"../../../..{path_consts['paths']['connectors_path']}")
    conn_file_path = f'{connectors_dir}/{connector_type}'
    conn_inner_path = 'Object'
    object_connector = 'Connector'

    # load the connector
    bpy.ops.wm.append(
        filepath=os.path.join(conn_file_path, conn_inner_path, object_connector),
        directory=os.path.join(conn_file_path, conn_inner_path),
        filename=object_connector
    )

    # set foot file params
    feet_dir = os.path.join(os.path.dirname(__file__), f"../../../..{path_consts['paths']['feet_path']}")
    foot_file_path = f'{feet_dir}/{foot_type}'
    foot_inner_path = 'Object'
    object_foot = 'Foot'

    # load the connector
    bpy.ops.wm.append(
        filepath=os.path.join(foot_file_path, foot_inner_path, object_foot),
        directory=os.path.join(foot_file_path, foot_inner_path),
        filename=object_foot
    )

    # set foot obj
    foot_obj = bpy.data.objects[object_foot]
    if amputation_side == 'left':
        # mirror the foot in the direction of x-axis
        foot_obj.scale.x = -1

    # set connector obj
    conn_obj = bpy.data.objects[object_connector]

    # move connector obj
    bottom_vert = annotations.get_all_points('Selections', 'Connector_Loc')[-1]  # get last
    distance = bottom_vert.z + (default_z_loc - 0.02)
    general.move_object(conn_obj, Vector((0, 0, distance)))

    # shrinkwrap modifier on the connector object
    shrinkwrap_mod = conn_obj.modifiers.new(name="Shrinkwrap", type="SHRINKWRAP")
    shrinkwrap_mod.wrap_method = 'PROJECT'
    shrinkwrap_mod.wrap_mode = 'OUTSIDE_SURFACE'
    shrinkwrap_mod.subsurf_levels = 0
    shrinkwrap_mod.vertex_group = "shrinkwrap_group"
    shrinkwrap_mod.use_project_z = True
    shrinkwrap_mod.target = ufit_obj
    shrinkwrap_mod.auxiliary_target = ufit_obj
    shrinkwrap_mod.vertex_group = "shrinkwrap_group"

    # cleanup annotations
    user_interface.cleanup_grease_pencil(context)
    
    
#################################
# Alignment
#################################
def prep_alignment(context):
    conn_obj = bpy.data.objects['Connector']
    foot_obj = bpy.data.objects['Foot']

    foot_obj.hide_select = False  # make selectable
    foot_obj.select_set(True)  # also select foot for focus (UFit obj already selected)
    user_interface.focus_on_selected()  # focus on both selected objects
    foot_obj.select_set(False)  # deselect foot after focus
    foot_obj.hide_select = True  # do not make selectable

    # change the view
    user_interface.change_orthographic('FRONT')
    user_interface.change_view_orbit(10, 'ORBITDOWN')

    # make sure to show the connector
    context.scene.ufit_show_connector = True

    # show the z-axis
    context.space_data.overlay.show_axis_z = True
    context.space_data.overlay.show_cursor = False

    # activate the rotation tool
    context.scene.ufit_alignment_tool = 'builtin.rotate'


def save_alignment(context):
    ufit_obj = bpy.data.objects['uFit']
    ufit_measure_obj = bpy.data.objects['uFit_Measure']
    ufit_original_obj = bpy.data.objects['uFit_Original']
    conn_obj = bpy.data.objects['Connector']

    # save the connector locaiton
    context.scene.ufit_connector_loc = conn_obj.location

    # apply transformations
    transform_objs = [obj for obj in bpy.data.objects if obj.name.startswith("Circum_")]
    transform_objs.extend([ufit_measure_obj, ufit_original_obj])
    for obj in transform_objs:
        obj.location = ufit_obj.location
        obj.rotation_euler = ufit_obj.rotation_euler
        general.apply_transform(obj, use_location=True, use_rotation=True, use_scale=True)

    for obj in [ufit_obj, conn_obj]:
        general.apply_transform(obj, use_location=True, use_rotation=True, use_scale=True)


#########################################
# Transition Connector
#########################################
def scale_connector_scale_groups(context):
    conn_obj = bpy.data.objects['Connector']

    # make sure the connector object is not hidden and activated
    conn_obj.hide_set(False)

    # select scale_group_inner and scale smaller
    general.select_vertices_from_vertex_groups(context, conn_obj, vg_names=["scale_group_inner"])
    bpy.ops.transform.resize(value=(0.95, 0.95, 0.95))

    # select scale_group_outer and scale bigger
    general.select_vertices_from_vertex_groups(context, conn_obj, vg_names=["scale_group_outer"])
    bpy.ops.transform.resize(value=(2, 2, 2))


def create_inner_outer_ufit(context):
    ufit_obj = bpy.data.objects['uFit']

    # delete the faces from the edge ring
    general.select_vertices_from_vertex_groups(context, ufit_obj, ['cutout_edge_0'])
    bpy.ops.mesh.delete(type='FACE')

    # select a random vertex and take the linked_pick
    bpy.ops.mesh.select_linked_pick(deselect=False,
                                    delimit=set(),
                                    object_index=ufit_obj.pass_index,
                                    index=50)

    # create uFit_1 based on selection
    ufit_1 = general.create_obj_from_selection(context, 'uFit_1')

    # create uFit_2 as inverted selection
    bpy.ops.mesh.select_all(action='INVERT')
    ufit_2 = general.create_obj_from_selection(context, 'uFit_2')

    # calculate the surface area, the smallest surface area is the inside
    total_area_ufit_1 = sum(f.area for f in ufit_1.data.polygons)
    total_area_ufit_2 = sum(f.area for f in ufit_2.data.polygons)

    # assign the correct names
    if total_area_ufit_1 > total_area_ufit_2:
        ufit_outer = ufit_1
        ufit_inner = ufit_2
    else:
        ufit_outer = ufit_2
        ufit_inner = ufit_1

    ufit_inner.name = 'uFit_Inner'
    ufit_outer.name = 'uFit_Outer'

    # flip the normals from ufit_outer for the boolean modifier to work as we want (no clue why)
    general.activate_object(context, ufit_outer, mode='EDIT')
    bpy.ops.mesh.flip_normals()

    # add faces again to edge ring
    general.select_vertices_from_vertex_groups(context, ufit_obj, ['cutout_edge_0'])
    bpy.ops.mesh.bridge_edge_loops()

    return ufit_inner, ufit_outer


def prep_transition_connector(context):
    conn_obj = bpy.data.objects['Connector']
    ufit_obj = bpy.data.objects['uFit']

    ufit_inner, ufit_outer = create_inner_outer_ufit(context)

    # change to the correct mode
    user_interface.change_orthographic('FRONT')
    user_interface.set_shading_solid_mode()

    # remove the shrinkwrap modifier on the conn_obj
    shrinkwrap_mod = conn_obj.modifiers["Shrinkwrap"]
    conn_obj.modifiers.remove(shrinkwrap_mod)

    # create new shrinkwrap modifier from conn_obj to the ufit_inner object
    shrinkwrap_mod = conn_obj.modifiers.new(name="Shrinkwrap_Inner", type="SHRINKWRAP")
    shrinkwrap_mod.wrap_method = 'NEAREST_SURFACEPOINT'
    shrinkwrap_mod.wrap_mode = 'ON_SURFACE'
    shrinkwrap_mod.vertex_group = "scale_group_inner"
    shrinkwrap_mod.target = ufit_inner

    # create new shrinkwrap modifier from conn_obj to the ufit_outer object
    shrinkwrap_mod = conn_obj.modifiers.new(name="Shrinkwrap_Outer", type="SHRINKWRAP")
    shrinkwrap_mod.wrap_method = 'NEAREST_SURFACEPOINT'
    shrinkwrap_mod.wrap_mode = 'ON_SURFACE'
    shrinkwrap_mod.vertex_group = "scale_group_outer"
    shrinkwrap_mod.target = ufit_outer

    # switch to object mode
    general.activate_object(context, ufit_obj, mode='OBJECT')

    # add a plane (automatically the active object
    z_loc = context.scene.ufit_connector_loc[2] + 0.07
    bpy.ops.mesh.primitive_plane_add(size=0.2, enter_editmode=False, align='WORLD',
                                     location=(0, 0, z_loc), scale=(1, 1, 1))

    # name the new object
    cut_obj = bpy.context.active_object
    cut_obj.name = "Cutter"

    # lock to y direction movement
    cut_obj.lock_location[0] = True
    cut_obj.lock_location[1] = True

    # set the move tool
    bpy.ops.wm.tool_set_by_id(name="builtin.move")

    # add boolean modifier to the uFit obj to make the cut
    boolean_mod = ufit_obj.modifiers.new(name="Boolean", type="BOOLEAN")
    boolean_mod.operation = 'DIFFERENCE'
    boolean_mod.solver = 'EXACT'
    boolean_mod.object = cut_obj

    # add boolean modifier to the uFit_Inner obj to make the cut
    boolean_mod = ufit_inner.modifiers.new(name="Boolean", type="BOOLEAN")
    boolean_mod.operation = 'DIFFERENCE'
    boolean_mod.solver = 'EXACT'
    boolean_mod.object = cut_obj

    # add boolean modifier to the uFit_Outer obj to make the cut
    boolean_mod = ufit_outer.modifiers.new(name="Boolean", type="BOOLEAN")
    boolean_mod.operation = 'DIFFERENCE'
    boolean_mod.solver = 'EXACT'
    boolean_mod.object = cut_obj

    # scale the connector inner and outer shell
    # scale_connector_scale_groups(context, conn_obj)

    # activate the cutter object
    general.activate_object(context, cut_obj, mode='OBJECT')

    # make the ufit object unselectable
    ufit_obj.hide_select = True

    # turn of the xray
    context.scene.ufit_x_ray = False


def correct_thickness_connector(context, conn_obj):
    # # subdivide outer shell
    # general.activate_object(context, conn_obj, mode='OBJECT')
    # general.select_vertices_from_vertex_groups(context, conn_obj, vg_names=['outer_shell_group'])
    # bpy.ops.mesh.subdivide(number_cuts=5)

    # create inner shell object for shrinkwrap
    general.select_vertices_from_vertex_groups(context, conn_obj, vg_names=['inner_shell_group'])
    inner_shell_obj = general.create_obj_from_selection(context, 'Inner_Shell', copy_vg=True)

    # # extrude the bottom of the inner shell object along it's curve
    general.select_vertices_from_vertex_groups(context, inner_shell_obj, vg_names=['inner_shell_bottom'])
    general.move_selected_verts_along_local_axis(inner_shell_obj, 0.02, axis=(False, True, False))

    # relax the inner_shell_bottom
    bpy.ops.mesh.looptools_relax(input='selected', interpolation='linear', iterations='25', regular=True)

    # # make the inner_shell_bottom vertices a perfect circle
    # bpy.ops.mesh.looptools_circle(custom_radius=False, fit='best', flatten=True, influence=100, lock_x=False,
    #                               lock_y=False, lock_z=False, radius=1, angle=0, regular=True)
    #
    # # subdivide inner shell object
    # # general.select_vertices_from_vertex_groups(context, inner_shell_obj, vg_names=['inner_shell_group'])
    # # bpy.ops.mesh.subdivide(number_cuts=5)

    # add shrinkwrap modifier to connector
    shrinkwrap_mod = conn_obj.modifiers.new(name="Shrinkwrap", type="SHRINKWRAP")
    shrinkwrap_mod.wrap_method = 'NEAREST_SURFACEPOINT'  # 'NEAREST_VERTEX'
    shrinkwrap_mod.wrap_mode = 'ON_SURFACE'
    shrinkwrap_mod.target = inner_shell_obj
    shrinkwrap_mod.offset = 0.0005  # negligible
    shrinkwrap_mod.vertex_group = 'outer_shell_group'

    # apply shrinkwrap
    general.activate_object(context, conn_obj, mode='OBJECT')
    override = {"object": conn_obj, "active_object": conn_obj}
    bpy.ops.object.modifier_apply(override, modifier="Shrinkwrap")

    # move outer shell in the xy direction
    thickness = context.scene.ufit_print_thickness / 1000 - 0.0005
    general.select_vertices_from_vertex_groups(context, conn_obj, vg_names=['outer_shell_group'])
    general.scale_selected_verts_distance_xy(conn_obj, thickness)

    # get all vertices below x mm and pull/push to connector height down
    general.activate_object(context, conn_obj, mode='OBJECT')
    connector_height = context.scene.ufit_connector_loc[2]

    for v in general.get_vertices_below_z(conn_obj, z=(connector_height + 0.005)):
        v.co.z = connector_height

    # delete the inner shell object
    general.delete_obj_by_name_contains('Inner_Shell')


def create_ufit_inside(context, ufit_obj, conn_obj):
    # duplicate the inner shell group
    general.select_vertices_from_vertex_groups(context, conn_obj, vg_names=['inner_shell_group'])
    ufit_inside = general.create_obj_from_selection(context, 'uFit_Inside', copy_vg=True)

    # select all vertices and create faces
    general.select_vertices_from_vertex_groups(context, ufit_inside, vg_names=['inner_shell_group'])
    bpy.ops.mesh.edge_face_add()

    # toggle edit mode
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()

    # duplicate ufit_inside so we have it twice
    ufit_inside_2 = general.duplicate_obj(ufit_inside, 'uFit_Inside_2', context.collection, data=True, actions=False)

    # boolean modifier - intersect to capture everything inside uFit_Inside_2 of the normal uFit Object
    boolean_mod = ufit_inside_2.modifiers.new(name="Boolean", type="BOOLEAN")
    boolean_mod.operation = 'INTERSECT'
    boolean_mod.solver = 'EXACT'
    boolean_mod.object = ufit_obj

    # apply boolean modifier
    general.activate_object(context, ufit_inside_2, mode='OBJECT')
    override = {"object": ufit_inside_2, "active_object": ufit_inside_2}
    bpy.ops.object.modifier_apply(override, modifier="Boolean")

    # on uFit_Inside delete the top face
    general.select_vertices_from_vertex_groups(context, ufit_inside, vg_names=['scale_group_inner'])
    bpy.ops.mesh.delete(type='FACE')

    # add a solididfy modifier on uFit_Inner
    boolean_mod = ufit_inside.modifiers.new(name="Solidify", type="SOLIDIFY")
    boolean_mod.thickness = -0.001  # one mm of thickness

    # apply the solidify modifier
    general.activate_object(context, ufit_inside, mode='OBJECT')
    override = {"object": ufit_inside, "active_object": ufit_inside}
    bpy.ops.object.modifier_apply(override, modifier="Solidify")

    # join the uFit_Inner and uFit_Inside_2
    selected_objects = [ufit_inside, ufit_inside_2]
    join_dict = {
        'object': ufit_inside,
        'active_object': ufit_inside,
        'selected_objects': selected_objects,
        'selected_editable_objects': selected_objects
    }
    bpy.ops.object.join(join_dict)

    # Remesh the uFit_Inner object
    voxel_remesh = ufit_inside.modifiers.new("Voxel Remesh", type='REMESH')
    voxel_remesh.mode = 'VOXEL'
    voxel_remesh.voxel_size = 0.0005  # Set the voxel size

    # set the origin to the center of the object and scale
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='MEDIAN')
    ufit_inside.scale = (0.99, 0.99, 0.99)

    # apply the remesh modifier
    general.activate_object(context, ufit_inside, mode='OBJECT')
    override = {"object": ufit_inside, "active_object": ufit_inside}
    bpy.ops.object.modifier_apply(override, modifier="Voxel Remesh")

    # decimate geometry to reduce vertices
    general.activate_object(context, ufit_inside, mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.decimate(ratio=0.05)

    # make ufit_inner part of the collection
    bpy.data.collections['Collection'].objects.link(ufit_inside)
    bpy.context.scene.collection.objects.unlink(ufit_inside)  # ['Collection'].objects.link(ufit_inside)


def fix_transition_inaccuracy(context, ufit_obj, conn_obj):
    for i in range(5):
        # select the inner and outer scale vertex groups on conn_obj and subdivide
        general.select_vertices_from_vertex_groups(context, conn_obj, vg_names=['scale_group_inner'])
        bpy.ops.mesh.subdivide(number_cuts=1, ngon=False, quadcorner='INNERVERT')
        general.select_vertices_from_vertex_groups(context, conn_obj, vg_names=['scale_group_outer'])
        bpy.ops.mesh.subdivide(number_cuts=1, ngon=False, quadcorner='INNERVERT')

        # add shrinkwrap modifier again to connector
        shrinkwrap_mod = conn_obj.modifiers.new(name="Shrinkwrap", type="SHRINKWRAP")
        shrinkwrap_mod.wrap_method = 'NEAREST_SURFACEPOINT'  # 'NEAREST_VERTEX'
        shrinkwrap_mod.wrap_mode = 'ON_SURFACE'
        shrinkwrap_mod.target = ufit_obj
        shrinkwrap_mod.vertex_group = 'shrinkwrap_group'

        # apply the shrinkwrap modifier
        general.activate_object(context, conn_obj, mode='OBJECT')
        override = {"object": conn_obj, "active_object": conn_obj}
        bpy.ops.object.modifier_apply(override, modifier="Shrinkwrap")

    # # triangulate to avoid bended faces
    # triangulate_mod = conn_obj.modifiers.new(name="Triangulate", type="TRIANGULATE")
    # triangulate_mod.quad_method = 'SHORTEST_DIAGONAL'
    # triangulate_mod.ngon_method = 'BEAUTY'
    # triangulate_mod.min_vertices = 4
    #
    # # apply the triangulate modifier
    # general.activate_object(context, conn_obj, mode='OBJECT')
    # override = {"object": conn_obj, "active_object": conn_obj}
    # bpy.ops.object.modifier_apply(override, modifier="Triangulate")

    # decimate connector to reduce vertices and avoid long calculation time for union
    # general.activate_object(context, conn_obj, mode='EDIT')
    # bpy.ops.mesh.select_all(action='SELECT')
    # bpy.ops.mesh.vert_connect_concave()

    # general.select_vertices_from_vertex_groups(context, conn_obj, vg_names=['shrinkwrap_group'])
    # bpy.ops.mesh.decimate(ratio=0.05)


def transition_connector(context):
    ufit_obj = bpy.data.objects['uFit']
    conn_obj = bpy.data.objects['Connector']

    # apply shrinkwrap modifier on connector
    general.activate_object(context, conn_obj, mode='OBJECT')
    override = {"object": conn_obj, "active_object": conn_obj}
    bpy.ops.object.modifier_apply(override, modifier="Shrinkwrap_Inner")
    bpy.ops.object.modifier_apply(override, modifier="Shrinkwrap_Outer")

    # fix potential transition inaccuracy of connector
    fix_transition_inaccuracy(context, ufit_obj, conn_obj)

    # make sure the ufit object is manifold
    general.activate_object(context, ufit_obj, mode='OBJECT')
    bpy.ops.mesh.print3d_clean_non_manifold()

    # temporary disable the Boolean modifier on uFit to create the inner part for full contact socket
    bpy.context.object.modifiers["Boolean"].show_viewport = False

    if context.scene.ufit_total_contact_socket:
        create_ufit_inside(context, ufit_obj, conn_obj)

    # make sure the thickness is horizontally consistent
    if context.scene.ufit_try_perfect_print:
        correct_thickness_connector(context, conn_obj)

    # apply the Boolean modifier of the uFit
    general.activate_object(context, ufit_obj, mode='OBJECT')
    bpy.context.object.modifiers["Boolean"].show_viewport = True  # reactivate
    override = {"object": ufit_obj, "active_object": ufit_obj}
    bpy.ops.object.modifier_apply(override, modifier="Boolean")

    selected_objects = [ufit_obj, conn_obj]
    join_dict = {
        'object': ufit_obj,
        'active_object': ufit_obj,
        'selected_objects': selected_objects,
        'selected_editable_objects': selected_objects
    }
    bpy.ops.object.join(join_dict)

    # # boolean modifier UNION to merge the uFit and Connector object
    # boolean_mod = ufit_obj.modifiers.new(name="Boolean", type="BOOLEAN")
    # boolean_mod.operation = 'UNION'
    # boolean_mod.solver = 'EXACT'
    # boolean_mod.object = conn_obj
    # # boolean_mod.use_hole_tolerant = True
    # # boolean_mod.use_self = True  # costs a crazy amount of performance
    #
    # # apply the merge
    # override = {"object": ufit_obj, "active_object": ufit_obj}
    # bpy.ops.object.modifier_apply(override, modifier="Boolean")

    # delete connector and cutter object
    general.delete_obj_by_name_contains(name='Connector')
    general.delete_obj_by_name_contains(name='Cutter')
    general.delete_obj_by_name_contains(name='uFit_Inner')
    general.delete_obj_by_name_contains(name='uFit_Outer')
