"""Script for layer modifications."""


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
        for i, modification in enumerate(modifications):
            node = node_tree.nodes.new(type="ShaderNodeMixRGB")
            modification.node_name = node.name
            node.blend_type = blend_map[modification.blend_type]
            node.inputs[0].default_value = modification.factor
            node.location = (i * 200, 0)

            if modification.blend_layer != "flat color":
                node_input = node_tree.nodes.new(type="ShaderNodeVertexColor")
                node_input.location = (i * 200, -200)
                modification.input_node_name = node_input.name
                node_input.layer_name = modification.blend_layer
                node_tree.links.new(node_input.outputs[0], node.inputs[2])
            else:
                modification.input_node_name = ""
                node.inputs[2].default_value = modification.blend_color

            if not nodes:
                node_tree.links.new(color_input.outputs[0], node.inputs[1])
            else:
                node_tree.links.new(nodes[-1].outputs[0], node.inputs[1])

            nodes.append(node)
    else:
        nodes.append(color_input)
    
    material_output.location = (len(nodes) * 200, 0)
    node_tree.links.new(nodes[-1].outputs[0], material_output.inputs[0])


def update_transformation(
    material,
    modification,
    blend_type = None,
    blend_layer = None,
    blend_color = None,
    factor = None
):
    """Update transformation."""

    node_tree = material.node_tree
    node = node_tree.nodes.get(modification.node_name)

    if blend_type is not None:
        node.blend_type = blend_map[blend_type]

    if blend_layer is not None:
        if blend_layer == "flat color":
            node.inputs[2].default_value = modification.blend_color
            node_tree.nodes.remove(node_tree.nodes.get(modification.input_node_name))
            modification.input_node_name = ""
        else:
            if modification.input_node_name == "":
                node_input = node_tree.nodes.new(type="ShaderNodeVertexColor")
                node_input.location = (node.location[0], node.location[1] - 200)
                modification.input_node_name = node_input.name
                
                node_tree.links.new(node_input.outputs[0], node.inputs[2])

            node_tree.nodes.get(modification.input_node_name).layer_name = blend_layer

    if blend_color is not None:
        node.inputs[2].default_value = blend_color
    
    if factor is not None:
        node.inputs[0].default_value = factor


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

