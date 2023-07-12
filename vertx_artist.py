"""Vertex color script for blender."""

import os
import math
import re
import colorsys

import bpy


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


loop_data_color = []
last_active_loop = None
last_mode = "POLYGON"
mode_bools = (False, False)
last_selection = []
request_refresh = False
last_view_transform = None


def set_restricted_color(color: tuple, new_color: tuple, channels: str):
    """Set color according to restrictions."""

    if bpy.context.scene.view_settings.view_transform != "Raw":
        new_color = inverse_gamma_color(new_color)

    if "R" in channels:
        color[0] = new_color[0]
    
    if "G" in channels:
        color[1] = new_color[1]
    
    if "B" in channels:
        color[2] = new_color[2]
    
    if "A" == channels:
        for i in range(3):
            color[i] = new_color[0]


def set_color(color: tuple, channels: str):
    """Set color of active selection."""

    # color = from_blender_color(color)

    obj = bpy.context.object
    if obj is None:
        return None

    color_attribute = obj.data.color_attributes.active_color

    if color_attribute is None:
        return None

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


def on_color_change(color: tuple, channels: str):
    """Update color of everything with same color."""

    global request_refresh

    obj = bpy.context.object
    if obj is None:
        return None

    color_attribute = obj.data.color_attributes.active_color

    if color_attribute is None:
        return None

    if last_active_loop is None:
        return None
    
    if not loop_data_color:
        return None

    for i in loop_data_color[last_active_loop]["loops"]:
        set_restricted_color(
            color_attribute.data[i].color,
            color,
            channels
        )

    request_refresh = True


def on_colors_change(colors: list, channels: str):
    """Update colors of everything with same color."""

    global request_refresh

    obj = bpy.context.object
    if obj is None:
        return None

    color_attribute = obj.data.color_attributes.active_color

    if color_attribute is None:
        return None
    
    if not loop_data_color:
        return None
    
    for i in range(len(colors)):
        color = tuple(colors[i].color)
        if color != loop_data_color[i]["color"]:
            for j in loop_data_color[i]["loops"]:
                set_restricted_color(
                    color_attribute.data[j].color,
                    color,
                    channels
                )

    request_refresh = True


def refresh_colors(force: bool = False):
    """Handle selection changes, return active color and object colors"""

    global loop_data_color, last_active_loop, last_mode, mode_bools, last_selection, request_refresh, last_view_transform

    if last_view_transform is None:
        last_view_transform = bpy.context.scene.view_settings.view_transform

    output_size = 2

    obj = bpy.context.object
    if obj is None:
        loop_data_color = []
        last_active_loop = None
        return (None, ) * output_size

    color_attribute = obj.data.color_attributes.active_color

    if color_attribute is None:
        loop_data_color = []
        last_active_loop = None
        return (None, ) * output_size

    try:
        vert_mode = obj.data.use_paint_mask_vertex
        poly_mode = obj.data.use_paint_mask

        mode_changed = mode_bools[0] != vert_mode or mode_bools[1] != poly_mode
    except AttributeError:
        loop_data_color = []
        last_active_loop = None
        return (None, ) * output_size

    object_colors = {}
    selection_changed = False

    # vertices
    if vert_mode or (not poly_mode and last_mode == "VERTEX"):
        selected_vert_idx = []

        if vert_mode:
            for vertex in obj.data.vertices:
                if vertex.select:
                    selected_vert_idx.append(vertex.index)
            
            last_mode = "VERTEX"
        
        if not selected_vert_idx:
            selected_vert_idx = last_selection

        for i, l in enumerate(obj.data.loops):
            if l.vertex_index not in selected_vert_idx:
                continue

            color = tuple(color_attribute.data[i].color)[:-1]
            object_colors[color] = object_colors.get(color, 0) + 1

        if selected_vert_idx != last_selection:
            last_selection = selected_vert_idx
            selection_changed = True

    # polygons
    if poly_mode or (not vert_mode and last_mode == "POLYGON"):
        selected_poly_loops = []

        if poly_mode:
            for polygon in obj.data.polygons:
                if polygon.select:
                    selected_poly_loops.extend(polygon.loop_indices)

            last_mode = "POLYGON"

        if not selected_poly_loops:
            selected_poly_loops = last_selection

        for i in selected_poly_loops:
            color = tuple(color_attribute.data[i].color)[:-1]
            object_colors[color] = object_colors.get(color, 0) + 1

        if selected_poly_loops != last_selection:
            last_selection = selected_poly_loops
            selection_changed = True

    # if len(object_colors) == 0:
    #     return (None, ) * output_size

    view_transform_changed = bpy.context.scene.view_settings.view_transform != last_view_transform
    last_view_transform = bpy.context.scene.view_settings.view_transform

    if not selection_changed and not mode_changed and not force and not request_refresh and not view_transform_changed:
        return (None, ) * output_size

    if mode_changed:
        mode_bools = (vert_mode, poly_mode)

    # last_colors = [x["color"] for x in loop_data_color]

    # Set object loop data
    if request_refresh:
        for element in loop_data_color:
            element["color"] = tuple(color_attribute.data[element["loops"][0]].color)[:-1]
    else:
        loop_data_color = []

        for i, l in enumerate(obj.data.loops):
            color = tuple(color_attribute.data[i].color)[:-1]
            
            element = [x for x in loop_data_color if x["color"] == color]

            if len(element) == 0:
                loop_data_color.append({"color": color, "loops": [i]})
            else:
                element[0]["loops"].append(i)

    colors = [x["color"] for x in loop_data_color]
    color = max(object_colors, key=object_colors.get) if len(object_colors) > 0 else colors[0]

    if not request_refresh:
        last_active_loop = [i for i, x in enumerate(loop_data_color) if x["color"] == color][0]

    request_refresh = False

    # Gamma correction
    if bpy.context.scene.view_settings.view_transform != "Raw":
        color = gamma_correct_color(color)
        colors = [gamma_correct_color(x) for x in colors]

    return color, colors


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


def compare_hsv(color1: tuple, color2: tuple, ignore_hsv: tuple):
    """Compare the two colors, ignoring HSV flags."""

    equals = (
        (color1[0] == color2[0]) or ignore_hsv[0],
        (color1[1] == color2[1]) or ignore_hsv[1],
        (color1[2] == color2[2]) or ignore_hsv[2]
    )

    return all(equals)


def select_by_color(tolerance: float, color: tuple, ignore_hsv):
    """Select all vertices/polygons with color within tolerance."""

    obj = bpy.context.object
    if obj is None:
        return None

    color_attribute = obj.data.color_attributes.active_color

    if color_attribute is None:
        return None

    try:
        vert_mode = obj.data.use_paint_mask_vertex
        poly_mode = obj.data.use_paint_mask
    except AttributeError:
        return None

    if not vert_mode and not poly_mode:
        obj.data.use_paint_mask = True
        poly_mode = True

    color = tuple(color)
    hsv_color = colorsys.rgb_to_hsv(*color)

    if vert_mode:
        vert_colors = {}

        for vertex in obj.data.vertices:
            if vertex.select:
                vertex.select = False

        for i, l in enumerate(obj.data.loops):
            obj_color = tuple(color_attribute.data[i].color)[:-1]
            obj_hsv_color = colorsys.rgb_to_hsv(*obj_color)

            if l.vertex_index not in vert_colors:
                vert_colors[l.vertex_index] = [0, 0]

            if compare_hsv(obj_hsv_color, hsv_color, ignore_hsv):
                vert_colors[l.vertex_index][0] += 1

            vert_colors[l.vertex_index][1] += 1

        for k, v in vert_colors.items():
            if v[0] and v[0] / v[1] >= (1 - tolerance):
                obj.data.vertices[k].select = True

    if poly_mode:
        poly_colors = {}

        for polygon in obj.data.polygons:
            if polygon.select:
                polygon.select = False

        for polygon in obj.data.polygons:
            for j in polygon.loop_indices:
                obj_color = tuple(color_attribute.data[j].color)[:-1]
                obj_hsv_color = colorsys.rgb_to_hsv(*obj_color)

                if polygon.index not in poly_colors:
                    poly_colors[polygon.index] = [0, 0]
                
                if compare_hsv(obj_hsv_color, hsv_color, ignore_hsv):
                    poly_colors[polygon.index][0] += 1
                
                poly_colors[polygon.index][1] += 1
        
        for k, v in poly_colors.items():
            if v[0] and v[0] / v[1] >= (1 - tolerance):
                obj.data.polygons[k].select = True


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

    color_attributes = [None] * 4

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
            return color_attributes[j].data[i].color[0]

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
