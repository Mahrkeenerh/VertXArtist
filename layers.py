"""Script for layer modifications."""

def layer_test(node_tree):
    new_node = node_tree.nodes.new(type="ShaderNodeMixRGB")

    return new_node


def change_node_blend_type(node, blend_type):
    node.blend_type = blend_type
