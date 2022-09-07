"""Script for layer modifications."""


import colorsys


blend_map = {
    "Mix": "MIX",
    "Darken": "DARKEN",
    "Multiply": "MULTIPLY",
    "Color Burn": "BURN",
    "Lighten": "LIGHTEN",
    "Screen": "SCREEN",
    "Color Dodge": "DODGE",
    "Add": "ADD",
    "Overlay": "OVERLAY",
    "Soft Light": "SOFT_LIGHT",
    "Linear Light": "LINEAR_LIGHT",
    "Difference": "DIFFERENCE",
    "Subtract": "SUBTRACT",
    "Divide": "DIVIDE",
    "Hue": "HUE",
    "Saturation": "SATURATION",
    "Color": "COLOR",
    "Value": "VALUE"
}


def create_material_connections(material, modifications, base_layer):
    """Create connections between nodes."""

    node_tree = material.node_tree

    material_output = node_tree.nodes.new(type="ShaderNodeOutputMaterial")
    color_input = node_tree.nodes.new(type="ShaderNodeVertexColor")
    color_input.layer_name = base_layer
    color_input.location = (-200, 0)

    nodes = []

    if modifications is not None and len(modifications) > 0:
        for modification in modifications:
            if not modification.include:
                continue

            node = node_tree.nodes.new(type="ShaderNodeMixRGB")
            modification.node_name = node.name
            node.blend_type = blend_map[modification.blend_type]
            node.inputs[0].default_value = modification.factor
            node.location = (len(nodes) * 200, 0)

            if modification.blend_layer != "flat color":
                node_input = node_tree.nodes.new(type="ShaderNodeVertexColor")
                node_input.location = (len(nodes) * 200, -200)
                modification.input_node_name = node_input.name
                node_input.layer_name = modification.blend_layer
                node_tree.links.new(node_input.outputs[0], node.inputs[2])
            else:
                modification.input_node_name = ""
                node.inputs[2].default_value = (*modification.blend_color, 1)

            if not nodes:
                node_tree.links.new(color_input.outputs[0], node.inputs[1])
            else:
                node_tree.links.new(nodes[-1].outputs[0], node.inputs[1])

            nodes.append(node)

    if len(nodes) == 0:
        nodes.append(color_input)
    
    material_output.location = (len(nodes) * 200, 0)
    node_tree.links.new(nodes[-1].outputs[0], material_output.inputs[0])


# https://github.com/blender/blender/blob/57013e2a44e974d307f08f41793d810a49537f96/source/blender/blenkernel/intern/material.c#L1521
def mix_color(r_col, col, blend_type, fac):
    """Mix color with modification."""

    facm = 1 - fac

    match blend_type:
        case "Mix":
            r_col[0] = facm * r_col[0] + fac * col[0]
            r_col[1] = facm * r_col[1] + fac * col[1]
            r_col[2] = facm * r_col[2] + fac * col[2]

        case "Add":
            r_col[0] += fac * col[0]
            r_col[1] += fac * col[1]
            r_col[2] += fac * col[2]

        case "Multiply":
            r_col[0] *= (facm + fac * col[0])
            r_col[1] *= (facm + fac * col[1])
            r_col[2] *= (facm + fac * col[2])

        case "Screen":
            r_col[0] = 1 - (facm + fac * (1 - col[0])) * (1 - r_col[0])
            r_col[1] = 1 - (facm + fac * (1 - col[1])) * (1 - r_col[1])
            r_col[2] = 1 - (facm + fac * (1 - col[2])) * (1 - r_col[2])

        case "Overlay":
            if r_col[0] < 0.5:
                r_col[0] *= (facm + 2 * fac * col[0])
            else:
                r_col[0] = 1 - (facm + 2 * fac * (1 - col[0])) * (1 - r_col[0])

            if r_col[1] < 0.5:
                r_col[1] *= (facm + 2 * fac * col[1])
            else:
                r_col[1] = 1 - (facm + 2 * fac * (1 - col[1])) * (1 - r_col[1])

            if r_col[2] < 0.5:
                r_col[2] *= (facm + 2 * fac * col[2])
            else:
                r_col[2] = 1 - (facm + 2 * fac * (1 - col[2])) * (1 - r_col[2])

        case "Subtract":
            r_col[0] -= fac * col[0]
            r_col[1] -= fac * col[1]
            r_col[2] -= fac * col[2]

        case "Divide":
            if col[0] != 0:
                r_col[0] = facm * r_col[0] + fac * r_col[0] / col[0]
            if col[1] != 0:
                r_col[1] = facm * r_col[1] + fac * r_col[1] / col[1]
            if col[2] != 0:
                r_col[2] = facm * r_col[2] + fac * r_col[2] / col[2]

        case "Difference":
            r_col[0] = facm * r_col[0] + fac * abs(r_col[0] - col[0])
            r_col[1] = facm * r_col[1] + fac * abs(r_col[1] - col[1])
            r_col[2] = facm * r_col[2] + fac * abs(r_col[2] - col[2])

        case "Darken":
            r_col[0] = min(r_col[0], col[0]) * fac + r_col[0] * facm
            r_col[1] = min(r_col[1], col[1]) * fac + r_col[1] * facm
            r_col[2] = min(r_col[2], col[2]) * fac + r_col[2] * facm

        case "Lighten":
            tmp = fac * col[0]

            if tmp > r_col[0]:
                r_col[0] = tmp

            tmp = fac * col[1]

            if tmp > r_col[1]:
                r_col[1] = tmp

            tmp = fac * col[2]

            if tmp > r_col[2]:
                r_col[2] = tmp

        case "Color Dodge":
            if r_col[0] != 0:
                tmp = 1 - fac * col[0]

                if tmp <= 0:
                    r_col[0] = 1
                elif (tmp := r_col[0] / tmp) > 1:
                    r_col[0] = 1
                else:
                    r_col[0] = tmp

            if r_col[1] != 0:
                tmp = 1 - fac * col[1]

                if tmp <= 0:
                    r_col[1] = 1
                elif (tmp := r_col[1] / tmp) > 1:
                    r_col[1] = 1
                else:
                    r_col[1] = tmp

            if r_col[2] != 0:
                tmp = 1 - fac * col[2]

                if tmp <= 0:
                    r_col[2] = 1
                elif (tmp := r_col[2] / tmp) > 1:
                    r_col[2] = 1
                else:
                    r_col[2] = tmp

        case "Color Burn":
            tmp = facm + fac * col[0]

            if tmp <= 0:
                r_col[0] = 0
            elif (tmp := 1 - (1 - r_col[0]) / tmp) < 0:
                r_col[0] = 0
            elif tmp > 1:
                r_col[0] = 1
            else:
                r_col[0] = tmp

            tmp = facm + fac * col[1]

            if tmp <= 0:
                r_col[1] = 0
            elif (tmp := 1 - (1 - r_col[1]) / tmp) < 0:
                r_col[1] = 0
            elif tmp > 1:
                r_col[1] = 1
            else:
                r_col[1] = tmp

            tmp = facm + fac * col[2]

            if tmp <= 0:
                r_col[2] = 0
            elif (tmp := 1 - (1 - r_col[2]) / tmp) < 0:
                r_col[2] = 0
            elif tmp > 1:
                r_col[2] = 1
            else:
                r_col[2] = tmp

        case "Hue":
            col_h, col_s, col_v = colorsys.rgb_to_hsv(col[0], col[1], col[2])

            if col_s != 0:
                r_h, r_s, r_v = colorsys.rgb_to_hsv(r_col[0], r_col[1], r_col[2])
                tmp_r, tmp_g, tmp_b = colorsys.hsv_to_rgb(col_h, r_s, r_v)

                r_col[0] = facm * r_col[0] + fac * tmp_r
                r_col[1] = facm * r_col[1] + fac * tmp_g
                r_col[2] = facm * r_col[2] + fac * tmp_b

        case "Saturation":
            r_h, r_s, r_v = colorsys.rgb_to_hsv(r_col[0], r_col[1], r_col[2])

            if r_s != 0:
                col_h, col_s, col_v = colorsys.rgb_to_hsv(col[0], col[1], col[2])
                r_col[0], r_col[1], r_col[2] = colorsys.hsv_to_rgb(r_h, facm * r_s + fac * col_s, r_v)

        case "Value":
            r_h, r_s, r_v = colorsys.rgb_to_hsv(r_col[0], r_col[1], r_col[2])
            col_h, col_s, col_v = colorsys.rgb_to_hsv(col[0], col[1], col[2])
            r_col[0], r_col[1], r_col[2] = colorsys.hsv_to_rgb(r_h, r_s, facm * r_v + fac * col_v)

        case "Color":
            col_h, col_s, col_v = colorsys.rgb_to_hsv(col[0], col[1], col[2])

            if col_s != 0:
                r_h, r_s, r_v = colorsys.rgb_to_hsv(r_col[0], r_col[1], r_col[2])
                tmp_r, tmp_g, tmp_b = colorsys.hsv_to_rgb(col_h, col_s, r_v)

                r_col[0] = facm * r_col[0] + fac * tmp_r
                r_col[1] = facm * r_col[1] + fac * tmp_g
                r_col[2] = facm * r_col[2] + fac * tmp_b

        case "Soft Light":
            scr = 1 - (1 - col[0]) * (1 - r_col[0])
            scg = 1 - (1 - col[1]) * (1 - r_col[1])
            scb = 1 - (1 - col[2]) * (1 - r_col[2])

            r_col[0] = facm * r_col[0] + fac * ((1 - r_col[0]) * col[0] * r_col[0] + r_col[0] * scr)
            r_col[1] = facm * r_col[1] + fac * ((1 - r_col[1]) * col[1] * r_col[1] + r_col[1] * scg)
            r_col[2] = facm * r_col[2] + fac * ((1 - r_col[2]) * col[2] * r_col[2] + r_col[2] * scb)

        case "Linear Light":
            if col[0] > 0.5:
                r_col[0] += fac * (2 * (col[0] - 0.5))
            else:
                r_col[0] += fac * (2 * col[0] - 1)
            
            if col[1] > 0.5:
                r_col[1] += fac * (2 * (col[1] - 0.5))
            else:
                r_col[1] += fac * (2 * col[1] - 1)
        
            if col[2] > 0.5:
                r_col[2] += fac * (2 * (col[2] - 0.5))
            else:
                r_col[2] += fac * (2 * col[2] - 1)


def aplly_color_transformation_stack(modification_stack, only_visible):
    """Apply color transformation stack."""

    obj = bpy.context.object

    if obj is None:
        return "No object selected."

    color_attributes = obj.data.color_attributes
    base_layer = color_attributes.get(modification_stack.base_layer)

    if base_layer is None:
        return "Base layer not found."

    out_layer = color_attributes.active_color

    for i, l in enumerate(obj.data.loops):
        out_layer.data[i].color = base_layer.data[i].color

    for modification in modification_stack.modifications:
        if only_visible and not modification.include:
            continue

        if modification.blend_layer == "flat color":
            for i, l in enumerate(obj.data.loops):
                mix_color(
                    out_layer.data[i].color,
                    modification.blend_color,
                    modification.blend_type,
                    modification.factor
                )
        else:
            mix_layer = color_attributes.get(modification.blend_layer)
            for i, l in enumerate(obj.data.loops):
                mix_color(
                    out_layer.data[i].color,
                    mix_layer.data[i].color,
                    modification.blend_type,
                    modification.factor
                )


def update_transformation(
    material,
    modification = None,
    base_layer = None,
    blend_type = None,
    blend_layer = None,
    blend_color = None,
    factor = None
):
    """Update transformation."""

    node_tree = material.node_tree

    if base_layer is not None:
        input_node = node_tree.nodes.get("Color Attribute")
        input_node.layer_name = base_layer

        return
    
    if not modification.include:
        return

    node = node_tree.nodes.get(modification.node_name)

    if blend_type is not None:
        node.blend_type = blend_map[blend_type]

        return

    if blend_layer is not None:
        if blend_layer == "flat color":
            node.inputs[2].default_value = (*modification.blend_color, 1)
            node_tree.nodes.remove(node_tree.nodes.get(modification.input_node_name))
            modification.input_node_name = ""
        else:
            if modification.input_node_name == "":
                node_input = node_tree.nodes.new(type="ShaderNodeVertexColor")
                node_input.location = (node.location[0], node.location[1] - 200)
                modification.input_node_name = node_input.name

                node_tree.links.new(node_input.outputs[0], node.inputs[2])

            node_tree.nodes.get(modification.input_node_name).layer_name = blend_layer

        return

    if blend_color is not None:
        node.inputs[2].default_value = (*blend_color, 1)

        return

    if factor is not None:
        node.inputs[0].default_value = factor

        return


def get_unique_transformation_name(name_list, name):
    """Check, if name_list containst `name`. If so, return a unique name."""

    if name.lower() == "none":
        name = "New Transformation"

    if name_list.count(name) < 2:
        return name

    i = 1

    while True:
        new_name = f"{name} {i:03}"

        if new_name not in name_list:
            return new_name

        i += 1

