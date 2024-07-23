import colorsys
import math

import bpy
import bmesh


# Gamma correction and inverse gamma correction may be reversed
def inverse_gamma(c: float):
    """Gamma uncorrection."""

    c = min(max(0, c), 1)
    c = c / 12.92 if c < 0.04045 else math.pow((c + 0.055) / 1.055, 2.4)

    return c


def gamma_correct(c: float):
    """Gamma correction."""

    c = max(0.0, c * 12.92) if c < 0.0031308 else 1.055 * math.pow(c, 1.0 / 2.4) - 0.055
    c = max(min(int(c * 255 + 0.5), 255), 0)

    return c / 255


def inverse_gamma_color(rgb):
    """Gamma uncorrection."""

    # return r, g, b
    return inverse_gamma(rgb[0]), inverse_gamma(rgb[1]), inverse_gamma(rgb[2])


def gamma_correct_color(rgb):
    """Gamma correction."""

    # return r / 255, g / 255, b / 255
    return gamma_correct(rgb[0]), gamma_correct(rgb[1]), gamma_correct(rgb[2])


def set_restricted_color(color: tuple, new_color: tuple, channels: str):
    """Set color according to restrictions."""

    if bpy.context.mode != "EDIT_MESH":
        new_color = inverse_gamma_color(new_color)

    if "R" in channels:
        color[0] = new_color[0]

    if "G" in channels:
        color[1] = new_color[1]

    if "B" in channels:
        color[2] = new_color[2]

    if "A" == channels:
        hsv_color = colorsys.rgb_to_hsv(*new_color)
        for i in range(3):
            color[i] = hsv_color[2]


def round_color(color, precision=5):
    return tuple(round(x, precision) for x in color)


ignore_color_change = False

"""
{
    col_idx: [
        col_rgb, {
        "obj": {
            vert_idx: [
                corner_list_idx,
                ...
            ]
        }
    }]
}
"""
color_corner_lookup = {}
lookup_to_obj_col_idx_mapping = {}
obj_to_lookup_col_idx_mapping = []
"""
{
    ("obj", vert_idx): col_idx
}
"""
corner_color_lookup = {}


def get_face_corner_idx(corner):
    for i in range(len(corner.vert.link_loops)):
        if corner.vert.link_loops[i].index == corner.index:
            return i


def sort_update_object_colors(colors, active_color_index):
    global ignore_color_change

    if active_color_index is None:
        return

    ignore_color_change = True

    to_remove_count = len(bpy.context.scene.vrtxa_object_colors) - len(colors)
    if to_remove_count > len(colors):
        bpy.context.scene.vrtxa_object_colors.clear()

    while len(bpy.context.scene.vrtxa_object_colors) > len(colors):
        bpy.context.scene.vrtxa_object_colors.remove(len(bpy.context.scene.vrtxa_object_colors) - 1)

    while len(bpy.context.scene.vrtxa_object_colors) < len(colors):
        new_color = bpy.context.scene.vrtxa_object_colors.add()
        new_color.index = len(bpy.context.scene.vrtxa_object_colors) - 1

    bpy.context.scene.vrtxa_active_color_index = lookup_to_obj_col_idx_mapping[active_color_index]
    for i, color_comp in enumerate(colors):
        color = color_comp[0]
        bpy.context.scene.vrtxa_object_colors[i].color = color

    ignore_color_change = False


def update_lookups(new_color, changes):
    global color_corner_lookup, corner_color_lookup

    if new_color not in [x[0] for x in color_corner_lookup.values()]:
        new_color_idx = max(color_corner_lookup.keys()) + 1 if len(color_corner_lookup) > 0 else 0
        color_corner_lookup.setdefault(
            new_color_idx, [new_color, {}]
        )
    else:
        new_color_idx = [x for x in color_corner_lookup.items() if x[1][0] == new_color][0][0]

    # Add new entry to color corner lookup
    for change in changes:
        obj_name = change[0]
        vert_idx = change[1]
        corner_list_idx = change[2]

        color_corner_lookup[new_color_idx][1].setdefault(
            obj_name, {}
        ).setdefault(
            vert_idx, []
        ).append(
            corner_list_idx
        )

    removed_col_idxs = []

    # Remove old and empty entries
    for change in changes:
        obj_name = change[0]
        vert_idx = change[1]
        corner_list_idx = change[2]

        col_idx = corner_color_lookup[(obj_name, corner_list_idx)]
        color_corner_lookup[col_idx][1][obj_name][vert_idx].remove(corner_list_idx)

        if len(color_corner_lookup[col_idx][1][obj_name][vert_idx]) == 0:
            del color_corner_lookup[col_idx][1][obj_name][vert_idx]
        
        if len(color_corner_lookup[col_idx][1][obj_name]) == 0:
            del color_corner_lookup[col_idx][1][obj_name]

        if len(color_corner_lookup[col_idx][1]) == 0:
            removed_col_idxs.append(col_idx)
            del color_corner_lookup[col_idx]

    # Update corner color lookup
    for change in changes:
        obj_name = change[0]
        corner_list_idx = change[2]

        corner_color_lookup[(obj_name, corner_list_idx)] = new_color_idx

    return new_color_idx


class VRTXA_OT_SetColor(bpy.types.Operator):
    bl_idname = "vertx_artist.set_color"
    bl_label = "Set Color"
    bl_description = "Apply color to active selection"
    bl_options = {"REGISTER", "UNDO"}

    color: bpy.props.FloatVectorProperty(
        name='color',
        description='Color to apply to selection',
        size=3,
        subtype='COLOR_GAMMA',
        min=0.0,
        max=1.0
    )
    use_static: bpy.props.BoolProperty(
        name='use_static',
        description='Apply static color instead of operator color',
        default=False,
        options={'HIDDEN'}
    )

    @classmethod
    def poll(cls, context):
        in_edit_mode = context.mode == 'EDIT_MESH'
        in_paint_mode = context.mode == 'PAINT_VERTEX'
        paint_select = bpy.context.object.data.use_paint_mask or bpy.context.object.data.use_paint_mask_vertex

        return in_edit_mode or (in_paint_mode and paint_select)

    def execute(self, context):
        global color_corner_lookup, corner_color_lookup
        global lookup_to_obj_col_idx_mapping, obj_to_lookup_col_idx_mapping

        obj = bpy.context.object
        color_attribute = obj.data.color_attributes.active_color

        if obj is None or color_attribute is None :
            self.report({'WARNING'}, message="Can't set color")
            return {"FINISHED"}

        if self.use_static:
            color = bpy.context.scene.vrtxa_static_color
        else:
            color = self.color

        channels = obj.vrtxa_layers[obj.data.color_attributes.active_color_index].channels

        changes = []
        new_color_idx = None
        new_color = None

        # VERTEX PAINT MODE
        if bpy.context.mode == "PAINT_VERTEX":
            try:
                vert_mode = obj.data.use_paint_mask_vertex
                poly_mode = obj.data.use_paint_mask
            except AttributeError:
                return {"FINISHED"}

            if vert_mode:
                selected_vert_idx = []

                for vertex in obj.data.vertices:
                    if vertex.select:
                        selected_vert_idx.append(vertex.index)

                for i, l in enumerate(obj.data.loops):
                    if l.vertex_index not in selected_vert_idx:
                        continue

                    set_restricted_color(
                        color_attribute.data[i].color,
                        color,
                        channels
                    )

                    changes.append((obj.name, l.vertex_index, i))

            # polygons
            if poly_mode:
                for polygon in obj.data.polygons:
                    if polygon.select:
                        for i in polygon.loop_indices:
                            set_restricted_color(
                                color_attribute.data[i].color,
                                color,
                                channels
                            )

                            changes.append((obj.name, obj.data.loops[i].vertex_index, i))
            
            new_color = round_color(gamma_correct_color(tuple(color_attribute.data[changes[-1][2]].color)[:-1]))

        # EDIT MODE
        if bpy.context.mode == "EDIT_MESH":
            objs = bpy.context.selected_objects
            if not objs:
                objs = [obj]

            # Ignore non-mesh objects
            objs = [x for x in objs if x.type == "MESH"]

            for obj in objs:
                mode = list(bpy.context.tool_settings.mesh_select_mode)
                bm = bmesh.from_edit_mesh(obj.data)
                active_layer = bm.loops.layers.color.get(color_attribute.name)

                # edge or vertex selection
                if mode[0] or mode[1]:
                    for vert in bm.verts:
                        if vert.select:
                            for corner_idx, corner in enumerate(vert.link_loops):
                                set_restricted_color(
                                    corner[active_layer],
                                    color,
                                    channels
                                )

                                changes.append((obj.name, vert.index, corner.index))

                # faces
                if mode[2]:
                    for face in bm.faces:
                        if face.select:
                            for corner in face.loops:
                                set_restricted_color(
                                    corner[active_layer],
                                    color,
                                    channels
                                )

                                changes.append((obj.name, corner.vert.index, corner.index))

                if new_color is None:
                    # new_color = tuple(bm.verts[changes[-1][1]].link_loops[changes[-1][2]][active_layer])[:-1]
                    if mode[0] or mode[1]:
                        for vert in bm.verts:
                            if vert.select:
                                new_color = round_color(tuple(vert.link_loops[0][active_layer])[:-1])
                                break

                    if mode[2]:
                        for face in bm.faces:
                            if face.select:
                                new_color = round_color(tuple(face.loops[0][active_layer])[:-1])
                                break

                bmesh.update_edit_mesh(obj.data)

        new_color_idx = update_lookups(new_color, changes)

        """
        colors = {
            (r, g, b): idx
        }
        """
        colors = [(x[1][0], x[0]) for x in color_corner_lookup.items()]
        colors = sorted(colors, key=lambda x: colorsys.rgb_to_hsv(*x[0]))
        lookup_to_obj_col_idx_mapping = {x[1]: i for i, x in enumerate(colors)}
        obj_to_lookup_col_idx_mapping = [x[1] for x in colors]
        active_color_index = new_color_idx

        sort_update_object_colors(colors, active_color_index)

        return {"FINISHED"}


class VRTXA_OT_ApplyAlphaGradient(bpy.types.Operator):
    bl_idname = "vertx_artist.apply_alpha_gradient"
    bl_label = "Apply Alpha Gradient"
    bl_description = "Apply alpha gradient to correct channel"
    bl_options = {"REGISTER", "UNDO"}
    neg_axis: bpy.props.FloatProperty(name='neg_axis', default=0.0, min=0.0, max=1.0)
    pos_axis: bpy.props.FloatProperty(name='pos_axis', default=1.0, min=0.0, max=1.0)

    def calculate_alpha(self, min_z, max_z, z):
        """Calculate alpha value for vertex."""

        div = max_z - min_z if max_z - min_z != 0 else 1
        alpha = (z - min_z) / div * (self.pos_axis - self.neg_axis) + self.neg_axis
        return alpha

    @classmethod
    def poll(cls, context):
        active_obj = bpy.context.object
        objects = bpy.context.selected_objects
        return active_obj is not None and active_obj.type == "MESH" or objects

    def execute(self, context):
        active_obj = bpy.context.object
        objects = bpy.context.selected_objects
        if not objects:
            objects = [active_obj]

        for obj in objects:
            if obj.type != "MESH":
                continue

            if obj.data.color_attributes.active_color is None:
                bpy.context.view_layer.objects.active = obj
                bpy.ops.geometry.color_attribute_add(name='Attribute', domain='CORNER', data_type='BYTE_COLOR')

        bpy.context.view_layer.objects.active = active_obj

        if bpy.context.mode == "OBJECT":
            obj_verts_coords = [obj.matrix_world @ v.co for obj in objects for v in obj.data.vertices]
        elif bpy.context.mode == "EDIT_MESH":
            obj_verts_coords = []
            for obj in objects:
                if obj.type != "MESH":
                    continue

                bm = bmesh.from_edit_mesh(obj.data)
                obj_verts_coords.extend([obj.matrix_world @ v.co for v in bm.verts if v.select])

        if len(obj_verts_coords) == 0:
            return {"FINISHED"}

        min_z = min(obj_verts_coords, key=lambda x: x[2])[2]
        max_z = max(obj_verts_coords, key=lambda x: x[2])[2]

        if bpy.context.mode == "EDIT_MESH":
            rolling_i = 0
            for i, obj in enumerate(objects):
                if obj.type != "MESH":
                    continue

                bm = bmesh.from_edit_mesh(obj.data)
                active_name = obj.data.color_attributes.active_color.name
                channels = obj.vrtxa_layers[active_name].channels
                color_attribute = bm.loops.layers.color.get(active_name)

                for vert in bm.verts:
                    if not vert.select:
                        continue

                    alpha = self.calculate_alpha(min_z, max_z, obj_verts_coords[rolling_i][2])
                    rolling_i += 1

                    for corner in vert.link_loops:
                        if channels == 'A':
                            corner[color_attribute][0] = alpha
                            corner[color_attribute][1] = alpha
                            corner[color_attribute][2] = alpha
                        else:
                            corner[color_attribute][3] = alpha

                bmesh.update_edit_mesh(obj.data)

        # Object mode
        else:
            rolling_i = 0
            for obj in objects:
                if obj.type != "MESH":
                    continue

                channels = obj.vrtxa_layers[obj.data.color_attributes.active_color.name].channels

                vert_corners = [[] for _ in range(len(obj.data.vertices))]
                for corner in obj.data.loops:
                    vert_corners[corner.vertex_index].append(corner.index)

                for i in range(len(obj.data.vertices)):
                    alpha = self.calculate_alpha(min_z, max_z, obj_verts_coords[rolling_i + i][2])

                    for corner in vert_corners[i]:
                        if channels == 'A':
                            obj.data.color_attributes.active_color.data[corner].color[0] = alpha
                            obj.data.color_attributes.active_color.data[corner].color[1] = alpha
                            obj.data.color_attributes.active_color.data[corner].color[2] = alpha
                        else:
                            obj.data.color_attributes.active_color.data[corner].color[3] = alpha

                rolling_i += len(obj.data.vertices)

        # POSSIBLE OPTIMIZATION WITH LOOKUPS
        bpy.ops.vertx_artist.refresh('INVOKE_DEFAULT')

        return {"FINISHED"}


class VRTXA_GROUP_ObjectColor(bpy.types.PropertyGroup):

    def object_color_update(self, context):
        """Update color of everything with same color."""

        if not ignore_color_change:
            color_idx = obj_to_lookup_col_idx_mapping[self.index]
            new_color = self.color

            obj = bpy.context.object
            objs = bpy.context.selected_objects
            if not objs:
                if obj is None:
                    return
                objs = [obj]

            # Ignore non-mesh objects
            objs = [x for x in objs if x.type == "MESH"]
            obj_name_map = {x.name: x for x in objs}

            for obj_name in color_corner_lookup[color_idx][1]:
                obj = obj_name_map[obj_name]        
                color_attribute = obj.data.color_attributes.active_color
                if color_attribute is None:
                    continue

                bm = bmesh.from_edit_mesh(obj.data)
                active_layer = bm.loops.layers.color.get(color_attribute.name)

                for vert_idx in color_corner_lookup[color_idx][1][obj.name]:
                    for corner_list_idx in color_corner_lookup[color_idx][1][obj.name][vert_idx]:
                        set_restricted_color(
                            bm.verts[vert_idx].link_loops[corner_list_idx][active_layer],
                            new_color,
                            bpy.context.view_layer.objects.active.vrtxa_layers[bpy.context.object.data.color_attributes.active_color_index].channels
                        )
                        color_corner_lookup[color_idx][0] = bm.verts[vert_idx].link_loops[corner_list_idx][active_layer][:-1]

                bmesh.update_edit_mesh(obj.data)

    color: bpy.props.FloatVectorProperty(
        name='color', description='Object color to dynamically change',
        size=3, default=(0.0, 0.0, 0.0),
        subtype='COLOR_GAMMA',
        min=0.0, max=1.0,
        update=object_color_update
    )
    index: bpy.props.IntProperty(
        name='index',
        default=0
    )


class VRTXA_OT_ShowhideObjectColors(bpy.types.Operator):
    bl_idname = "vertx_artist.showhide_object_colors"
    bl_label = "Show/Hide Object Colors"
    bl_description = "Show or Hide Object colors"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bpy.context.scene.vrtxa_show_object_colors = not bpy.context.scene.vrtxa_show_object_colors
        if bpy.context.scene.vrtxa_show_object_colors and bpy.context.mode == 'EDIT_MESH':
            bpy.ops.vertx_artist.refresh('INVOKE_DEFAULT')

        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class VRTXA_OT_Checkpoint(bpy.types.Operator):
    bl_idname = "vertx_artist.checkpoint"
    bl_label = "Checkpoint"
    bl_description = "Create a checkpoint with an undo step"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        return {"FINISHED"}


class VRTXA_OT_Refresh(bpy.types.Operator):
    bl_idname = "vertx_artist.refresh"
    bl_label = "Refresh"
    bl_description = "Force refresh object colors"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        global color_corner_lookup, corner_color_lookup
        global ignore_color_change
        global lookup_to_obj_col_idx_mapping, obj_to_lookup_col_idx_mapping

        color_corner_lookup = {}
        corner_color_lookup = {}

        obj = bpy.context.object
        objs = bpy.context.selected_objects
        if not objs:
            if obj is None:
                return {"FINISHED"}
            objs = [obj]

        """
        colors = {
            (r, g, b): [idx, count]
        }
        """
        colors = {}

        # Ignore non-mesh objects
        objs = [x for x in objs if x.type == "MESH"]
        for obj in objs:
            color_attribute = obj.data.color_attributes.active_color
            if color_attribute is None:
                continue

            bm = bmesh.from_edit_mesh(obj.data)
            active_layer = bm.loops.layers.color.get(color_attribute.name)

            def get_color(c):
                color = round_color(tuple(corner[active_layer])[:-1])
                colors.setdefault(color, [len(colors), 0])[1] += c

                color_corner_lookup.setdefault(
                    colors[color][0], [color, {}]
                )[1].setdefault(
                    obj.name, {}
                ).setdefault(
                    vert.index, []
                ).append(
                    corner.index
                )
                corner_color_lookup[(obj.name, corner.index)] = colors[color][0]

            # vert or edge mode
            if bpy.context.tool_settings.mesh_select_mode[0] or bpy.context.tool_settings.mesh_select_mode[1]:
                for vert in bm.verts:
                    for corner_idx, corner in enumerate(vert.link_loops):
                        get_color(int(vert.select))
            # faces
            if bpy.context.tool_settings.mesh_select_mode[2]:
                for face in bm.faces:
                    for corner in face.loops:
                        vert = corner.vert
                        get_color(int(face.select))

        colors = sorted(colors.items(), key=lambda x: colorsys.rgb_to_hsv(*x[0]))
        lookup_to_obj_col_idx_mapping = {x[1][0]: i for i, x in enumerate(colors)}
        obj_to_lookup_col_idx_mapping = [x[1][0] for x in colors]
        active_color_index = max(range(len(colors)), key=lambda x: colors[x][1][1]) if len(colors) > 0 else None

        sort_update_object_colors(colors, obj_to_lookup_col_idx_mapping[active_color_index])

        return {"FINISHED"}


class VRTXA_OT_SelectByColor(bpy.types.Operator):
    bl_idname = "vertx_artist.select_by_color"
    bl_label = "Select By Color"
    bl_description = "Select only the vertices/polygons with the specified color, depending on the selection tolerance"
    bl_options = {"REGISTER", "UNDO"}
    selection_tolerance: bpy.props.FloatProperty(
        name='selection_tolerance',
        default=0.0, precision=2,
        min=0.0, max=1.0
    )
    select_color: bpy.props.FloatVectorProperty(
        name='select_color',
        options={'HIDDEN'},
        size=3, default=(0.0, 0.0, 0.0),
        subtype='COLOR_GAMMA',
        min=0.0, max=1.0
    )
    select_color_idx: bpy.props.IntProperty(name='select_color_idx', options={'HIDDEN'})
    ignore_hue: bpy.props.BoolProperty(name='ignore_hue', default=False)
    ignore_saturation: bpy.props.BoolProperty(name='ignore_saturation', default=False)
    ignore_value: bpy.props.BoolProperty(name='ignore_value', default=False)

    def execute(self, context):
        ignore_hsv = (self.ignore_hue, self.ignore_saturation, self.ignore_value)

        obj = bpy.context.object
        objs = bpy.context.selected_objects
        if not objs:
            if obj is None:
                return
            objs = [obj]

        # Ignore non-mesh objects
        objs = [x for x in objs if x.type == "MESH"]
        obj_name_map = {x.name: x for x in objs}

        if self.select_color_idx == -1:
            # find index from self.select_color
            for i, color in enumerate(bpy.context.scene.vrtxa_object_colors):
                if color.color == self.select_color:
                    self.select_color_idx = i
                    break

        if self.select_color_idx == -1:
            return {"FINISHED"}

        self.select_color_idx = obj_to_lookup_col_idx_mapping[self.select_color_idx]

        # Deselect all
        if bpy.context.mode == "EDIT_MESH":
            for obj in objs:
                bm = bmesh.from_edit_mesh(obj.data)
                for vert in bm.verts:
                    vert.select = False
                for face in bm.faces:
                    face.select = False
                for edge in bm.edges:
                    edge.select = False

                bm.select_flush_mode()
                bmesh.update_edit_mesh(obj.data)

        def compare_ignore_color(ignore, hsv1, hsv2):
            return (
                (ignore[0] or hsv1[0] == hsv2[0]) and
                (ignore[1] or hsv1[1] == hsv2[1]) and
                (ignore[2] or hsv1[2] == hsv2[2])
            )

        # vert mode or edge mode
        if bpy.context.tool_settings.mesh_select_mode[0] or bpy.context.tool_settings.mesh_select_mode[1]:
            for obj_name in color_corner_lookup[self.select_color_idx][1]:
                obj = obj_name_map[obj_name]
                bm = bmesh.from_edit_mesh(obj.data)

                bm.verts.ensure_lookup_table()
                for vert_idx in color_corner_lookup[self.select_color_idx][1][obj_name]:
                    if len(color_corner_lookup[self.select_color_idx][1][obj_name][vert_idx]) / len(bm.verts[vert_idx].link_loops) >= (1 - self.selection_tolerance):
                        bm.verts[vert_idx].select = True

                # if ignore_hsv
                if any(ignore_hsv):
                    for col_idx, color in enumerate(bpy.context.scene.vrtxa_object_colors):
                        if col_idx == self.select_color_idx:
                            continue

                        select_color_hsv = colorsys.rgb_to_hsv(*self.select_color)
                        color_hsv = colorsys.rgb_to_hsv(*color.color)

                        if compare_ignore_color(ignore_hsv, select_color_hsv, color_hsv):
                            for vert_idx in color_corner_lookup[col_idx][1][obj_name]:
                                bm.verts[vert_idx].select = True

                # edge mode
                if bpy.context.tool_settings.mesh_select_mode[1]:
                    for edge in bm.edges:
                        if edge.verts[0].select and edge.verts[1].select:
                            edge.select = True

                bmesh.update_edit_mesh(obj.data)

        # face mode
        if bpy.context.tool_settings.mesh_select_mode[2]:
            for obj_name in color_corner_lookup[self.select_color_idx][1]:
                obj = obj_name_map[obj_name]
                bm = bmesh.from_edit_mesh(obj.data)

                bm.faces.ensure_lookup_table()
                for face in bm.faces:
                    loops_in_face = [x for x in face.loops if x.vert.index in color_corner_lookup[self.select_color_idx][1][obj_name]]
                    if len(loops_in_face) / len(face.loops) >= (1 - self.selection_tolerance):
                        face.select = True

                # if ignore_hsv
                if any(ignore_hsv):
                    for col_idx, color in enumerate(bpy.context.scene.vrtxa_object_colors):
                        if col_idx == self.select_color_idx:
                            continue

                        select_color_hsv = colorsys.rgb_to_hsv(*self.select_color)
                        color_hsv = colorsys.rgb_to_hsv(*color.color)

                        if compare_ignore_color(ignore_hsv, select_color_hsv, color_hsv):
                            for face in bm.faces:
                                face.select = True

                bmesh.update_edit_mesh(obj.data)

        bpy.context.scene.vrtxa_active_color_index = lookup_to_obj_col_idx_mapping[self.select_color_idx]

        return {"FINISHED"}


def register():
    bpy.types.Scene.vrtxa_static_color = bpy.props.FloatVectorProperty(
        name='static_color',
        description='Color to apply to selection',
        size=3,
        subtype='COLOR_GAMMA',
        min=0.0, max=1.0
    )
    bpy.utils.register_class(VRTXA_OT_SetColor)
    bpy.utils.register_class(VRTXA_OT_ApplyAlphaGradient)

    bpy.utils.register_class(VRTXA_GROUP_ObjectColor)
    bpy.types.Scene.vrtxa_object_colors = bpy.props.CollectionProperty(
        name='object_colors',
        type=VRTXA_GROUP_ObjectColor
    )
    bpy.types.Scene.vrtxa_object_colors_index = bpy.props.IntProperty(
        name='object_colors_index',
        description='Object_color index',
        default=0,
        min=0
    )
    bpy.types.Scene.vrtxa_active_color_index = bpy.props.IntProperty(
        name='active_color_index',
        default=0
    )
    bpy.types.Scene.vrtxa_show_object_colors = bpy.props.BoolProperty(
        name='show_object_colors', description='',
        default=True
    )

    bpy.utils.register_class(VRTXA_OT_ShowhideObjectColors)
    bpy.utils.register_class(VRTXA_OT_Checkpoint)
    bpy.utils.register_class(VRTXA_OT_Refresh)
    bpy.utils.register_class(VRTXA_OT_SelectByColor)


def unregister():
    del bpy.types.Scene.vrtxa_static_color
    bpy.utils.unregister_class(VRTXA_OT_SetColor)
    bpy.utils.unregister_class(VRTXA_OT_ApplyAlphaGradient)

    bpy.utils.unregister_class(VRTXA_GROUP_ObjectColor)
    del bpy.types.Scene.vrtxa_object_colors
    del bpy.types.Scene.vrtxa_object_colors_index
    del bpy.types.Scene.vrtxa_show_object_colors

    bpy.utils.unregister_class(VRTXA_OT_ShowhideObjectColors)
    bpy.utils.unregister_class(VRTXA_OT_Checkpoint)
    bpy.utils.unregister_class(VRTXA_OT_Refresh)
    bpy.utils.unregister_class(VRTXA_OT_SelectByColor)
