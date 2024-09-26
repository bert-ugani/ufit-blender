import bpy
from ..utils import annotations, general, user_interface, color_attributes


#########################################
# Move to center
#########################################
def prep_move_scan(context):
    # set ufit object
    ufit_obj = bpy.data.objects['uFit']

    # disable auto_smooth
    ufit_obj.data.use_auto_smooth = False

    # switch to annotation tool
    user_interface.activate_new_grease_pencil(context, name='Selections', layer_name='Knee')


def move_scan(context):
    # set ufit object
    ufit_obj = bpy.data.objects['uFit']

    # switch to edit mode
    general.activate_object(context, ufit_obj, mode='EDIT')

    # select single vertex based on annotations
    annotations.select_single_vert(ufit_obj, 'Selections', 'Knee')

    # move the scan to the center
    knee_vert = general.get_single_vert_co(context)
    general.set_object_origin(knee_vert)
    general.move_object(ufit_obj, -knee_vert)

    # apply location
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

    # cleanup annotations
    user_interface.cleanup_grease_pencil(context)


###############################
# Clean Up
###############################
def prep_clean_up(context):
    ufit_obj = bpy.data.objects['uFit']

    # go to edit mode
    general.activate_object(context, ufit_obj, mode='EDIT')

    # turn on xray
    user_interface.set_xray(turn_on=True, alpha=1)

    # activate tools
    user_interface.set_active_tool('builtin.select_circle')


def clean_up(context):
    selected_verts = general.get_selected_vertices_ix(context)
    if not len(selected_verts) > 100:  # there shoul
        raise Exception(f"Please select enough vertices. You only selected {len(selected_verts)} vertices, which is not possible in this step")

    # delete non-selected vertices
    bpy.ops.mesh.select_all(action='INVERT')
    bpy.ops.mesh.delete(type='VERT')

    # toggle edit mode
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()

    # select all
    bpy.ops.mesh.select_all(action='SELECT')

    # remove edges with no length and faces with no area
    bpy.ops.mesh.dissolve_degenerate(threshold=0.0001)  # make sure to use the same distance as remove_doubles

    # merge by distance to only keep relevant vertices
    bpy.ops.mesh.remove_doubles(threshold=0.0001)

    # some extra clean up
    bpy.ops.mesh.delete_loose()

    # Reselect all and fill holes
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.fill_holes(sides=50)


###############################
# Verify Clean Up
###############################
def prep_verify_clean_up(context):
    ufit_obj = bpy.data.objects['uFit']
    general.activate_object(context, ufit_obj, mode='EDIT')

    # turn off xray
    user_interface.set_xray(turn_on=False, alpha=1)

    bpy.ops.mesh.separate(type='LOOSE')
    x = []
    for i in bpy.context.selectable_objects:
        x.append(len(i.data.vertices))
    x.sort(reverse=True)
    x = x[:1]

    for i in bpy.context.selectable_objects:
        if len(i.data.vertices) != x[0]:
            bpy.data.objects.remove(i, do_unlink=True)

    bpy.context.selectable_objects[0].name = "uFit"
    bpy.context.view_layer.objects.active = bpy.context.selectable_objects[0]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_non_manifold()


def highlight_next_non_manifold(context):
    ufit_obj = bpy.data.objects['uFit']

    # get the vertex groups of the non-manifold areas
    nm_vertex_groups = [vg for vg in ufit_obj.vertex_groups if vg.name.startswith('nm_')]

    if nm_vertex_groups:
        active_vg = ufit_obj.vertex_groups[ufit_obj.vertex_groups.active_index].name

        if active_vg.startswith('nm_') and active_vg != context.scene.ufit_non_manifold_highlighted:
            # the active
            context.scene.ufit_non_manifold_highlighted = active_vg
        else:
            # get the name of the next active non-manifold area
            for i, nm_vg in enumerate(nm_vertex_groups):
                if nm_vg.name == context.scene.ufit_non_manifold_highlighted:
                    next_index = i + 1
                    if next_index > len(nm_vertex_groups) - 1:
                        next_index = 0
                    context.scene.ufit_non_manifold_highlighted = nm_vertex_groups[next_index].name
                    break

        # highlight vertices from non-manifold area (vertex group)
        general.select_vertices_from_vertex_groups(context, ufit_obj,
                                                   vg_names=[context.scene.ufit_non_manifold_highlighted])

        # focus on the selected area
        user_interface.focus_on_selected()


def fill_non_manifold(context):
    ufit_obj = bpy.data.objects['uFit']
    if len(ufit_obj.vertex_groups) != 0:
        bpy.ops.mesh.edge_face_add()
        bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
        bpy.ops.mesh.subdivide(number_cuts=5)
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_remove()


def delete_non_manifold(context):
    bpy.ops.mesh.select_linked(delimit=set())
    bpy.ops.mesh.delete(type='VERT')
    bpy.ops.object.vertex_group_remove()


def lift_ufit_non_manifold_top(context):
    ufit_obj = bpy.data.objects['uFit']
    non_manifold_areas = general.create_non_manifold_vertex_groups(context, ufit_obj, max_verts=None)

    # get the non-manifold area with the biggest amount of vertices (big gap at top of socket)
    max_nma = None
    max_verts = 0
    for nma, verts in non_manifold_areas.items():
        if len(verts) > max_verts:
            max_verts = len(verts)
            max_nma = nma

    if max_nma:
        # highlight vertices from non-manifold area (vertex group)
        general.select_vertices_from_vertex_groups(context, ufit_obj, vg_names=[max_nma])

        # deactivate snapping to move verts up
        bpy.context.scene.tool_settings.use_snap = False

        # move the verts x cm up
        context.scene.transform_orientation_slots[0].type = 'GLOBAL'
        bpy.ops.transform.translate(value=(0, 0, 0.05))


def verify_clean_up(context):
    ufit_obj = bpy.data.objects['uFit']

    # smooth all vertices
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.vertices_smooth(factor=0.5, repeat=7)

    # make sure to have more than 30000 vertices
    # general.subdivide_until_vertex_count(ufit_obj, 30000)

    # remesh the uFit object so you have quads
    if context.scene.ufit_device_type in ('transfemoral'):
        lift_ufit_non_manifold_top(context)
    color_attributes.remesh_with_texture_to_color_attr(context, ufit_obj, 'scan_colors')


###############################
# Rotate
###############################
def prep_rotate(context):
    # cursor to world center and snap cursor as rotaion point
    bpy.ops.view3d.snap_cursor_to_center()

    # activate rotation tool
    user_interface.set_active_tool('builtin.rotate')


def mirror(context):
    ufit_obj = bpy.data.objects['uFit']

    # mirror using x-axis direction
    bpy.ops.transform.mirror(
        orient_type='GLOBAL',
        orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
        orient_matrix_type='GLOBAL',
        constraint_axis=(True, False, False)
    )

    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # mirroring flips the normals
    general.activate_object(context, ufit_obj, 'EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.flip_normals()

    general.activate_object(context, ufit_obj, 'OBJECT')


def save_rotation(context):
    ufit_obj = bpy.data.objects['uFit']

    # make sure the ufit object is selected
    general.apply_transform(ufit_obj, use_location=True, use_rotation=True, use_scale=True)


def rotate_part_of_model(context):
    pass

#################################
# Circumferences
#################################
def prep_circumferences(context):
    pass


def add_circumference(context, i, z=0.0):
    measure_obj = bpy.data.objects['uFit']
    if 'uFit_Measure' in bpy.data.objects:
        measure_obj = bpy.data.objects['uFit_Measure']

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.mesh.primitive_circle_add(radius=0.2, enter_editmode=False, align='WORLD', location=(0, 0, z),
                                      scale=(1, 1, 1))

    # Fill the circle with a face
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.edge_face_add()

    # name the circumference object
    circum_obj = bpy.context.active_object
    circum_obj.name = f"Circum_{i}"

    # lock to y direction movement
    circum_obj.lock_location[0] = True
    circum_obj.lock_location[1] = True

    # add a boolean modifier to find the intersection with the ufit object
    general.activate_object(context, circum_obj, mode='OBJECT')
    boolean_mod = circum_obj.modifiers.new(name="Boolean", type="BOOLEAN")
    boolean_mod.operation = 'INTERSECT'
    boolean_mod.solver = 'FAST'
    boolean_mod.object = measure_obj

    # Set the origin to the median point of the object
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')

    # set the move tool
    bpy.ops.wm.tool_set_by_id(name="builtin.move")


# you cannot immediately apply after adding circumference because the user first moves it to the correct position
def apply_circumference(context):
    z_coord = None
    circumference = None

    # ONLY APPLIES ONE AT THE TIME (for-loop breaks!)
    for obj in bpy.data.objects:
        if "Circum_" in obj.name and obj.modifiers:
            # bug in blender - you have to use an override to apply the modifier
            override = {"object": obj, "active_object": obj}
            bpy.ops.object.modifier_apply(override, modifier="Boolean")

            # get the z coord
            z_coord = obj.location.z

            # get the circumference
            general.activate_object(context, obj, mode='EDIT')
            circumference = general.get_mesh_circumference(obj)
            general.activate_object(context, obj, mode='OBJECT')

            # move the origin of the object back to the median point (origin is dislocated after boolean operator)
            # completely changes the location of the object. Perform this after storing the z-ix
            bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='MEDIAN')

            # scale so that the object is visible
            obj.scale = (1.01, 1.01, 1.0)

            # apply transformations (resets origin of object to center of world!)
            general.apply_transform(obj, use_location=True, use_rotation=True, use_scale=True)

            break

    return z_coord, circumference


def hide_circumferences(context):
    for obj in bpy.data.objects:
        if "Circum_" in obj.name:
            obj.hide_set(True)


def calc_circumferences(context, z_coord, circumference, distance=0.02):
    i = 0
    new_z_coord = z_coord
    new_circum = circumference
    while new_circum > 0.025:
        context.scene.ufit_circum_z_ixs[i] = new_z_coord
        context.scene.ufit_circumferences[i] = new_circum
        i += 1

        new_z_coord -= distance
        add_circumference(context, i, new_z_coord)
        new_z_coord, new_circum = apply_circumference(context)

    general.delete_obj_by_name_contains(f'Circum_{i}')  # delete the last added circum because it is too small

    # hide the circumferences
    hide_circumferences(context)


def add_other_circumferences(context):
    # apply the first circumference
    z_coord, circumference = apply_circumference(context)

    # calculate the other circumferences
    dist = float(context.scene.ufit_circums_distance)
    calc_circumferences(context, z_coord, circumference, distance=dist)

    # set the initial circumferences
    context.scene.ufit_init_circumferences = context.scene.ufit_circumferences

    # increase substep
    context.scene.ufit_substep += 1


# function called in other steps to remeasure circumferences when ufit object changed
def remeasure_circumferences(context):
    general.delete_obj_by_name_contains('Circum_')  # remove circum objects
    for i, z in enumerate(context.scene.ufit_circum_z_ixs):
        if context.scene.ufit_circumferences[i] > 0:  # only recalculate if it was calculated before
            add_circumference(context, i, z)  # remeasure circumferences
            new_z_coord, new_circum = apply_circumference(context)
            context.scene.ufit_circumferences[i] = new_circum

    # hide the circumferences
    hide_circumferences(context)


def highlight_circumferences():
    # keep looping until the context is filled after opening a new file
    if bpy.context.window is None:
        bpy.app.timers.register(highlight_circumferences, first_interval=0.1)

    # get the ufit or ufit_original object
    ufit_obj = bpy.data.objects['uFit']
    active_obj = ufit_obj
    if 'uFit_Measure' in bpy.data.objects:
        ufit_obj.hide_set(True)
        active_obj = bpy.data.objects['uFit_Measure']
        active_obj.hide_set(False)
        active_obj.hide_select = False

    # Object mode, show colors and orbit up the viewpoint to avoid frontal view
    general.activate_object(bpy.context, active_obj, mode='OBJECT')
    user_interface.change_orthographic('FRONT')
    light = 'FLAT'
    if not bpy.context.scene.ufit_colored_scan:
        light = 'STUDIO'
    user_interface.set_shading_solid_mode(light=light, color_type='VERTEX')
    user_interface.set_active_tool('builtin.select_box')

    # un-hide and select all Circum objects
    for obj in bpy.data.objects:
        if "Circum_" in obj.name:
            obj.hide_set(False)
            obj.hide_select = False
            obj.select_set(True)
        elif not obj == active_obj:
            obj.hide_set(True)  # hide all objects except the active object and the circumferences

    # deselect the UFit object
    active_obj.select_set(False)

    # set the property that indicates the circums are highlighted
    bpy.context.scene.ufit_circums_highlighted = True
