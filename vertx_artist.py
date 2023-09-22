"""Vertex color script for blender."""

import os
import math
import re
import colorsys

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

    # r = rgb[0] * 255
    # g = rgb[1] * 255
    # b = rgb[2] * 255

    # r = min(max(0, r), 255) / 255
    # g = min(max(0, g), 255) / 255
    # b = min(max(0, b), 255) / 255

    # r = r / 12.92 if r < 0.04045 else math.pow((r + 0.055) / 1.055, 2.4)
    # g = g / 12.92 if g < 0.04045 else math.pow((g + 0.055) / 1.055, 2.4)
    # b = b / 12.92 if b < 0.04045 else math.pow((b + 0.055) / 1.055, 2.4)

    # return r, g, b
    return inverse_gamma(rgb[0]), inverse_gamma(rgb[1]), inverse_gamma(rgb[2])


def gamma_correct_color(rgb):
    """Gamma correction."""

    # r = rgb[0]
    # g = rgb[1]
    # b = rgb[2]

    # r = max(0.0, r * 12.92) if r < 0.0031308 else 1.055 * math.pow(r, 1.0 / 2.4) - 0.055
    # g = max(0.0, g * 12.92) if g < 0.0031308 else 1.055 * math.pow(g, 1.0 / 2.4) - 0.055
    # b = max(0.0, b * 12.92) if b < 0.0031308 else 1.055 * math.pow(b, 1.0 / 2.4) - 0.055

    # r = max(min(int(r * 255 + 0.5), 255), 0)
    # g = max(min(int(g * 255 + 0.5), 255), 0)
    # b = max(min(int(b * 255 + 0.5), 255), 0)

    # return r / 255, g / 255, b / 255
    return gamma_correct(rgb[0]), gamma_correct(rgb[1]), gamma_correct(rgb[2])


def print_props(inst, max_len=50):
    for i in dir(inst):
        if i.startswith("__"):
            continue

        prop = str(getattr(inst, i))
        prop = prop if len(prop) < 73 else prop[:70] + "..."
        name_len = len(str(i))
        print(i, (max_len - name_len) * " ", prop)


# possibly save color RGB, and then only update specific items
"""
{
    col_idx: {
        "obj": {
            vert_idx: [(
                corner_list_idx,
                corner_idx
            ), ...]
        }
    }
}
"""
color_corner_lookup = {}
"""
{
    ("obj", vert_idx, corner_idx): col_idx
}
"""
corner_color_lookup = {}


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


def set_color(color: tuple, channels: str):
    """Set color of active selection."""

    obj = bpy.context.object
    if obj is None:
        return None

    color_attribute = obj.data.color_attributes.active_color

    if color_attribute is None:
        return None

    # VERTEX PAINT MODE
    if bpy.context.mode == "PAINT_VERTEX":
        try:
            vert_mode = obj.data.use_paint_mask_vertex
            poly_mode = obj.data.use_paint_mask
        except AttributeError:
            return None

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

        return

    # EDIT MODE
    if bpy.context.mode == "EDIT_MESH":
        objs = bpy.context.selected_objects
        if not objs:
            objs = [obj]

        # new_color = None
        # changes = []

        # Ignore non-mesh objects
        objs = [x for x in objs if x.type == "MESH"]
        # obj_name_map = {x.name: x for x in objs}

        for obj in objs:
            mode = list(bpy.context.tool_settings.mesh_select_mode)
            bm = bmesh.from_edit_mesh(obj.data)
            active_layer = bm.loops.layers.color.get(color_attribute.name)

            # edge or vertex selection
            if mode[0] or mode[1]:
                for vert in bm.verts:
                    if vert.select:
                        for loop in vert.link_loops:
                            set_restricted_color(
                                loop[active_layer],
                                color,
                                channels
                            )

                            # changes.append((obj.name, vert.index, loop.index))

            # # faces
            if mode[2]:
                for face in bm.faces:
                    if face.select:
                        for loop in face.loops:
                            set_restricted_color(
                                loop[active_layer],
                                color,
                                channels
                            )

                            # changes.append((obj.name, loop.vert.index, loop.index))

            # if new_color is None:
            #     new_color = tuple(bm.verts[changes[-1][1]].link_loops[changes[-1][2]][active_layer])
            bmesh.update_edit_mesh(obj.data)

        # Update color corner lookup
        # for change in changes:
        #     corner_color_lookup[change] = color_attribute.index


def on_obj_color_change(obj_color, channels: str):
    """Update color of everything with same color."""

    color_idx = obj_color.index
    new_color = obj_color.color

    obj = bpy.context.object
    objs = bpy.context.selected_objects
    if not objs:
        if obj is None:
            return
        objs = [obj]

    # Ignore non-mesh objects
    objs = [x for x in objs if x.type == "MESH"]
    obj_name_map = {x.name: x for x in objs}

    for obj_name in color_corner_lookup[color_idx]:
        obj = obj_name_map[obj_name]        
        color_attribute = obj.data.color_attributes.active_color
        if color_attribute is None:
            continue

        bm = bmesh.from_edit_mesh(obj.data)
        active_layer = bm.loops.layers.color.get(color_attribute.name)

        for vert_idx in color_corner_lookup[color_idx][obj.name]:
            for corner_list_idx, corner_idx in color_corner_lookup[color_idx][obj.name][vert_idx]:
                set_restricted_color(
                    bm.verts[vert_idx].link_loops[corner_list_idx][active_layer],
                    new_color,
                    channels
                )

        bmesh.update_edit_mesh(obj.data)


def refresh_object_colors():
    """Return all colors of objects."""

    global color_corner_lookup, corner_color_lookup

    color_corner_lookup = {}
    corner_color_lookup = {}

    output_size = 2

    obj = bpy.context.object
    objs = bpy.context.selected_objects
    if not objs:
        if obj is None:
            return (None, ) * output_size
        objs = [obj]

    """
    colors = {
        (r, g, b): [idx, count],
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

        def get_color(corner_list_idx, c):
            color = tuple(corner[active_layer])[:-1]
            colors.setdefault(color, [len(colors), 0])[1] += c

            color_corner_lookup.setdefault(
                colors[color][0], {}
            ).setdefault(
                obj.name, {}
            ).setdefault(
                vert.index, []
            ).append(
                (corner_list_idx, corner.index)
            )
            # corner_color_lookup[(obj.name, vert.index, corner.index)] = colors[color][0]

        # vert or edge mode
        if bpy.context.tool_settings.mesh_select_mode[0] or bpy.context.tool_settings.mesh_select_mode[1]:
            for vert in bm.verts:
                for corner_idx, corner in enumerate(vert.link_loops):
                    get_color(corner_idx, int(vert.select))
        # faces
        if bpy.context.tool_settings.mesh_select_mode[2]:
            for face in bm.faces:
                def get_corner_idx():
                    corner_list_idx = 0
                    for i in range(len(corner.vert.link_loops)):
                        if corner.vert.link_loops[i].index == corner.index:
                            corner_list_idx = i
                            break
                    return corner_list_idx

                for corner in face.loops:
                    vert = corner.vert
                    get_color(get_corner_idx(), int(face.select))

    active_color_index = max(colors.values(), key=lambda x: x[1])[0] if len(colors) > 0 else None
    colors = [x for x in colors.keys()]

    return active_color_index, colors


def import_palette(path: str):
    """Import palette from file."""

    palette_name = os.path.basename(path).split(".")[0]
    palette_name = palette_name.replace("_", " ")
    file_extension = path.split(".")[-1]

    names = []
    colors = []

    if file_extension == "ccb":
        with open(path, "r", encoding="utf16") as f:
            contents = f.readlines()

        del contents[:25]

        for line in contents:
            line = line.strip().split(" ")

            r_raw = float(line[0])
            g_raw = float(line[1])
            b_raw = float(line[2])

            # colors.append(to_blender_color((r_raw, g_raw, b_raw)))
            colors.append((r_raw, g_raw, b_raw))
            names.append(line[4])

        return palette_name, names, colors

    if file_extension == "colors":
        with open(path, "r", encoding="us-ascii") as f:
            contents = f.read()

        colors_re = re.findall(r'(m_Color: {r: (.+), g: (.+), b: (.+), a: (.+)})', contents)
        names = re.findall(r'(- m_Name: (.*))', contents)

        for color in colors_re:
            r_raw = float(color[1])
            g_raw = float(color[2])
            b_raw = float(color[3])

            # colors.append(to_blender_color((r_raw, g_raw, b_raw)))
            colors.append((r_raw, g_raw, b_raw))

        names = [i[1] for i in names][9:]
        colors = colors[9:]

        return palette_name, names, colors

    if file_extension == "gpl":
        with open(path, "r", encoding="utf8") as f:
            contents = f.readlines()

        for line in contents:
            line = line.strip()

            if (
                line == "" or
                line.startswith("#") or
                line.startswith("GIMP Palette") or
                line.startswith("Name: ") or
                line.startswith("Columns: ")
            ):
                continue

            line = line.split()

            r_raw = float(line[0]) / 255
            g_raw = float(line[1]) / 255
            b_raw = float(line[2]) / 255
            name = " ".join(line[3:])

            # colors.append(to_blender_color((r_raw, g_raw, b_raw)))
            colors.append((r_raw, g_raw, b_raw))
            names.append(name)

        return palette_name, names, colors
    
    print("Unknown file extension: " + file_extension)
    return None, None, None


def export_palette(colors: list, path: str, ccb_header_path: str = None):
    """Export palette to file."""

    file_extension = path.split(".")[-1]

    if file_extension == "ccb":
        with open(ccb_header_path, "r", encoding="utf8") as f:
            contents = f.readlines()

        with open(path, "w", encoding="utf16") as out:
            out.writelines(contents)

            print(len(colors), file=out)

            for color in colors:
                # rgb = from_blender_color(tuple(color.color))
                rgb = tuple(color.color)
                print(
                    f"{rgb[0]:.6f}",
                    f"{rgb[1]:.6f}",
                    f"{rgb[2]:.6f}",
                    f"{1:.6f}",
                    color.name,
                    file=out
                )

        return

    if file_extension == "gpl":
        with open(path, "w", encoding="utf8") as out:
            print("GIMP Palette", file=out)
            print("Name:", os.path.basename(path).split(".")[0], file=out)
            print("Columns: 0", file=out)

            for color in colors:
                # rgb = from_blender_color(tuple(color.color))
                rgb = tuple(color.color)
                rgb_int = [int(x * 255) for x in rgb]
                print(
                    f"{rgb_int[0]}",
                    f"{rgb_int[1]}",
                    f"{rgb_int[2]}",
                    color.name,
                    file=out
                )

        return

    print("Unknown file extension: " + file_extension)
    return


def compare_hsv(rgb1: tuple, rgb2: tuple, hsv2: tuple, ignore_hsv: tuple):
    """Compare the two colors, ignoring HSV flags."""

    hsv1 = colorsys.rgb_to_hsv(*rgb1)
    if any(ignore_hsv):

        equals = (
            math.isclose(hsv1[0], hsv2[0], rel_tol=1e-4) or ignore_hsv[0],
            math.isclose(hsv1[1], hsv2[1], rel_tol=1e-4) or ignore_hsv[1],
            math.isclose(hsv1[2], hsv2[2], rel_tol=1e-4) or ignore_hsv[2]
        )
    else:
        equals = (
            math.isclose(rgb1[0], rgb2[0], rel_tol=1e-4),
            math.isclose(rgb1[1], rgb2[1], rel_tol=1e-4),
            math.isclose(rgb1[2], rgb2[2], rel_tol=1e-4)
        )

    return all(equals)


def select_by_color(tolerance: float, color: tuple, color_idx: int, ignore_hsv: tuple):
    """Select all vertices/polygons with color within tolerance."""

    obj = bpy.context.object
    objs = bpy.context.selected_objects
    if not objs:
        if obj is None:
            return
        objs = [obj]

    # Ignore non-mesh objects
    objs = [x for x in objs if x.type == "MESH"]
    obj_name_map = {x.name: x for x in objs}

    # Deselect all
    if bpy.context.mode == "EDIT_MESH":
        bm = bmesh.from_edit_mesh(obj.data)
        for vert in bm.verts:
            vert.select = False
        for face in bm.faces:
            face.select = False
        for edge in bm.edges:
            edge.select = False

        bm.select_flush_mode()

    # vert mode or edge mode
    if bpy.context.tool_settings.mesh_select_mode[0] or bpy.context.tool_settings.mesh_select_mode[1]:
        for obj_name in color_corner_lookup[color_idx]:
            obj = obj_name_map[obj_name]
            bm = bmesh.from_edit_mesh(obj.data)

            bm.verts.ensure_lookup_table()
            for vert_idx in color_corner_lookup[color_idx][obj_name]:
                if len(color_corner_lookup[color_idx][obj_name][vert_idx]) / len(bm.verts[vert_idx].link_loops) >= (1 - tolerance):
                    bm.verts[vert_idx].select = True

            # edge mode
            if bpy.context.tool_settings.mesh_select_mode[1]:
                for edge in bm.edges:
                    if edge.verts[0].select and edge.verts[1].select:
                        edge.select = True

            bmesh.update_edit_mesh(obj.data)

    # face mode
    if bpy.context.tool_settings.mesh_select_mode[2]:
        for obj_name in color_corner_lookup[color_idx]:
            obj = obj_name_map[obj_name]
            bm = bmesh.from_edit_mesh(obj.data)

            bm.faces.ensure_lookup_table()
            for face in bm.faces:
                loops_in_face = [x for x in face.loops if x.vert.index in color_corner_lookup[color_idx][obj_name]]
                if len(loops_in_face) / len(face.loops) >= (1 - tolerance):
                    face.select = True

            bmesh.update_edit_mesh(obj.data)


def combine_layers(
    channels: str,
    channels_list: list,
    channels_values: list,
    channels_gamma: list,
    layers: list
):
    """Assign color to active Color attribute from multiple channels."""

    obj = bpy.context.object
    if obj is None:
        return None

    color_attribute = obj.data.color_attributes.active_color

    if color_attribute is None:
        return None

    new_layer_name = color_attribute.name

    color_attributes = [None] * 4

    def combine_layers_bmesh():
        color_attribute = bm.loops.layers.color.get(new_layer_name)
        for channel in channels_list:
            for i in range(4):
                if channel == channels_list[i]:
                    color_attributes[i] = bm.loops.layers.color.get(channel)

        def color_map(corner, j: int):
            if color_attributes[j] is None:
                return channels_values[j]

            if j < 3:
                return corner[color_attributes[j]][j]

            if layers[channels_list[j]].channels == "A":
                obj_color = tuple(corner[color_attributes[j]])[:-1]
                obj_hsv_color = colorsys.rgb_to_hsv(*obj_color)
                return obj_hsv_color[2]

            if channels == "A":
                return corner[color_attributes[j]][3]

            return corner[color_attributes[j]][j]

        if channels == "A":
            for vert in bm.verts:
                for corner in vert.link_loops:
                    for j in range(3):
                        corner[color_attribute][j] = color_map(corner, 3)

            if channels_gamma[3] == "Gamma":
                for vert in bm.verts:
                    for corner in vert.link_loops:
                        for j in range(3):
                            corner[color_attribute][j] = gamma_correct(corner[color_attribute][j])

            if channels_gamma[3] == "Inverse":
                for vert in bm.verts:
                    for corner in vert.link_loops:
                        for j in range(3):
                            corner[color_attribute][j] = inverse_gamma(corner[color_attribute][j])

            return

        for vert in bm.verts:
            for corner in vert.link_loops:
                for j in range(4):
                    corner[color_attribute][j] = color_map(corner, j)

        for j in range(4):
            if channels_gamma[j] == "Gamma":
                for vert in bm.verts:
                    for corner in vert.link_loops:
                        corner[color_attribute][j] = gamma_correct(corner[color_attribute][j])

            if channels_gamma[j] == "Inverse":
                for vert in bm.verts:
                    for corner in vert.link_loops:
                        corner[color_attribute][j] = inverse_gamma(corner[color_attribute][j])

    def combine_layers_bpy():
        for col_attribute in obj.data.color_attributes:
            for i in range(4):
                if col_attribute.name == channels_list[i]:
                    color_attributes[i] = col_attribute

        def color_map(i: int, j: int):
            if color_attributes[j] is None:
                return channels_values[j]

            if j < 3:
                return color_attributes[j].data[i].color[j]

            if layers[color_attributes[j].name].channels == "A":
                obj_color = tuple(color_attributes[j].data[i].color)[:-1]
                obj_hsv_color = colorsys.rgb_to_hsv(*obj_color)
                return obj_hsv_color[2]

            if channels == "A":
                return color_attributes[j].data[i].color[3]

            return color_attributes[j].data[i].color[j]

        if channels == "A":
            for i, l in enumerate(obj.data.loops):
                for j in range(3):
                    color_attribute.data[i].color[j] = color_map(i, 3)

            if channels_gamma[3] == "Gamma":
                for i, l in enumerate(obj.data.loops):
                    for j in range(3):
                        color_attribute.data[i].color[j] = gamma_correct(color_attribute.data[i].color[j])

            if channels_gamma[3] == "Inverse":
                for i, l in enumerate(obj.data.loops):
                    for j in range(3):
                        color_attribute.data[i].color[j] = inverse_gamma(color_attribute.data[i].color[j])

            return

        for i, l in enumerate(obj.data.loops):
            for j in range(4):
                color_attribute.data[i].color[j] = color_map(i, j)

        for j in range(4):
            if channels_gamma[j] == "Gamma":
                for i, l in enumerate(obj.data.loops):
                    color_attribute.data[i].color[j] = gamma_correct(color_attribute.data[i].color[j])

            if channels_gamma[j] == "Inverse":
                for i, l in enumerate(obj.data.loops):
                    color_attribute.data[i].color[j] = inverse_gamma(color_attribute.data[i].color[j])

    if bpy.context.mode == "EDIT_MESH":
        bm = bmesh.from_edit_mesh(obj.data)
        combine_layers_bmesh()
        bmesh.update_edit_mesh(obj.data)
    else:
        combine_layers_bpy()


def get_active_tris():
    """Get positions of selected triangles."""

    obj = bpy.context.object
    if obj is None:
        return None

    # tris = []

    # # for polygon in obj.data.polygons:
    # #     if polygon.select:
    # #         for i in range(0, len(polygon.vertices), 3):
    # #             tris.append(polygon.vertices[i:i+3])
    # # obj.data.loop_triangles
    # for tri in obj.data.loop_triangles:
    #     if tri.select:
    #         tris.append(tri.vertices)

    # return tris

    try:
        poly_mode = obj.data.use_paint_mask
    except AttributeError:
        return []
    
    if not poly_mode:
        return []

    selected_poly_loops = []

    for polygon in obj.data.polygons:
        if polygon.select:
            poly_set = set()
            for i in polygon.loop_indices:
                # selected_poly_loops.append(i)
                poly_set.add(i)

            selected_poly_loops.append(poly_set)

    tris = []

    mat = obj.matrix_world

    for tri in obj.data.loop_triangles:
        tri_set = set(tri.loops)
        for poly_set in selected_poly_loops:
            if poly_set.issuperset(tri_set):
                # tris.append([obj.data.vertices[i] for i in tri.vertices])
                # v = ob.data.vertices[0].co
                # mat = ob.matrix_world

                # # Multiply matrix by vertex (see also: https://developer.blender.org/T56276)
                # loc = mat @ v
                tris_coords = [i.co for i in obj.data.vertices]
                tris.append([mat @ tris_coords[i] for i in tri.vertices])
                break

    return tris


def calculate_alpha(neg_axis, pos_axis, min_z, max_z, z):
    """Calculate alpha value for vertex."""
    div = max_z - min_z if max_z - min_z != 0 else 1
    alpha = (z - min_z) / div * (pos_axis - neg_axis) + neg_axis
    return alpha


def apply_alpha_gradient(neg_axis: float, pos_axis: float):
    """Create alpha gradient on all selected objects"""

    active_obj = bpy.context.object
    objects = bpy.context.selected_objects
    if not objects:
        if active_obj is None:
            return None
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
        return

    min_z = min(obj_verts_coords, key=lambda x: x[2])[2]
    max_z = max(obj_verts_coords, key=lambda x: x[2])[2]

    if bpy.context.mode == "EDIT_MESH":
        rolling_i = 0
        for i, obj in enumerate(objects):
            if obj.type != "MESH":
                continue

            bm = bmesh.from_edit_mesh(obj.data)
            active_name = obj.data.color_attributes.active_color.name
            channels = obj.sna_layers[active_name].channels
            color_attribute = bm.loops.layers.color.get(active_name)

            for vert in bm.verts:
                if not vert.select:
                    continue

                alpha = calculate_alpha(neg_axis, pos_axis, min_z, max_z, obj_verts_coords[rolling_i][2])
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

            channels = obj.sna_layers[obj.data.color_attributes.active_color.name].channels

            vert_corners = [[] for _ in range(len(obj.data.vertices))]
            for corner in obj.data.loops:
                vert_corners[corner.vertex_index].append(corner.index)

            for i in range(len(obj.data.vertices)):
                alpha = calculate_alpha(neg_axis, pos_axis, min_z, max_z, obj_verts_coords[rolling_i + i][2])

                for corner in vert_corners[i]:
                    if channels == 'A':
                        obj.data.color_attributes.active_color.data[corner].color[0] = alpha
                        obj.data.color_attributes.active_color.data[corner].color[1] = alpha
                        obj.data.color_attributes.active_color.data[corner].color[2] = alpha
                    else:
                        obj.data.color_attributes.active_color.data[corner].color[3] = alpha

            rolling_i += len(obj.data.vertices)
