import colorsys

import bpy

from .tools import items_to_enum, on_name_update


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


def refresh_default_material():
    if 'display material vertx artist' not in bpy.data.materials:
        bpy.data.materials.new(name='display material vertx artist')
        bpy.data.materials['display material vertx artist'].use_nodes = True

    bpy.data.materials['display material vertx artist'].node_tree.nodes.clear()

    if bpy.context.view_layer.objects.active.vrtxa_modification_stack_enum == 'None':
        return bpy.data.materials['display material vertx artist']

    # create connections
    modification_stack = bpy.context.view_layer.objects.active.vrtxa_modification_stacks[bpy.context.view_layer.objects.active.vrtxa_modification_stack_enum]
    modifications = modification_stack.modifications if modification_stack.name != 'None' else None

    node_tree = bpy.data.materials['display material vertx artist'].node_tree

    material_output = node_tree.nodes.new(type="ShaderNodeOutputMaterial")
    color_input = node_tree.nodes.new(type="ShaderNodeVertexColor")
    color_input.layer_name = modification_stack.base_layer
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

    return bpy.data.materials['display material vertx artist']


def on_update_refresh(self, context):
    refresh_default_material()


class VRTXA_GROUP_Modification(bpy.types.PropertyGroup):
    node_name: bpy.props.StringProperty(name='node_name')
    input_node_name: bpy.props.StringProperty(name='input_node_name')
    include: bpy.props.BoolProperty(name='include', default=True, update=on_update_refresh)

    def on_blend_type_update(self, context):
        update_transformation(material=bpy.data.materials['display material vertx artist'], modification=self, blend_type=self.blend_type)

    blend_type: bpy.props.EnumProperty(
        name='blend_type',
        items=[
            ('Mix', 'Mix', ''),
            ('Darken', 'Darken', ''),
            ('Multiply', 'Multiply', ''),
            ('Color Burn', 'Color Burn', ''),
            ('Lighten', 'Lighten', ''),
            ('Screen', 'Screen', ''),
            ('Color Dodge', 'Color Dodge', ''),
            ('Add', 'Add', ''),
            ('Overlay', 'Overlay', ''),
            ('Soft Light', 'Soft Light', ''),
            ('Linear Light', 'Linear Light', '',),
            ('Difference', 'Difference', '',),
            ('Subtract', 'Subtract', '',),
            ('Divide', 'Divide', '',),
            ('Hue', 'Hue', '',),
            ('Saturation', 'Saturation', '',),
            ('Color', 'Color', '',),
            ('Value', 'Value', '',)
        ],
        update=on_blend_type_update
    )

    def blend_layer_items(self, context):
        return items_to_enum('flat color', *[i.name for i in bpy.context.object.data.color_attributes])

    def on_blend_layer_update(self, context):
        update_transformation(material=bpy.data.materials['display material vertx artist'], modification=self, blend_layer=self.blend_layer)

    blend_layer: bpy.props.EnumProperty(
        name='blend_layer',
        items=blend_layer_items,
        update=on_blend_layer_update
    )

    def on_blend_color_update(self, context):
        update_transformation(material=bpy.data.materials['display material vertx artist'], modification=self, blend_color=self.blend_color)

    blend_color: bpy.props.FloatVectorProperty(
        name='blend_color',
        size=3,
        default=(1.0, 1.0, 1.0),
        subtype='COLOR',
        min=0.0, max=1.0,
        update=on_blend_color_update
    )

    def on_factor_update(self, context):
        update_transformation(material=bpy.data.materials['display material vertx artist'], modification=self, factor=self.factor)

    factor: bpy.props.FloatProperty(
        name='factor',
        default=0.5,
        min=0.0, max=1.0,
        precision=2,
        update=on_factor_update
    )


class VRTXA_GROUP_ModificationStack(bpy.types.PropertyGroup):
    def on_modification_name_update(self, context):
        on_name_update(self, [i.name for i in bpy.context.view_layer.objects.active.vrtxa_modification_stacks], "Attribute")

    name: bpy.props.StringProperty(name='name', update=on_modification_name_update)
    modifications: bpy.props.CollectionProperty(name='modifications', type=VRTXA_GROUP_Modification)

    def base_layer_items(self, context):
        return items_to_enum(*[x.name for x in bpy.context.object.data.color_attributes])

    def on_base_layer_update(self, context):
        update_transformation(material=bpy.data.materials['display material vertx artist'], base_layer=self.base_layer)

    base_layer: bpy.props.EnumProperty(
        name='base_layer',
        items=base_layer_items,
        update=on_base_layer_update
    )
    index: bpy.props.IntProperty(name='index', default=0, min=0)


class VRTXA_UL_DisplayModifications(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row()
        op = row.operator('vertx_artist.toggle_color_transformation_visibility', text='', icon='HIDE_OFF' if item.include else 253, emboss=False)
        op.modification_index = index
        row.prop(item, 'blend_type', text='')
        row.prop(item, 'blend_layer', text='')

        if item.blend_layer == 'flat color':
            row.prop(item, 'blend_color', text='')

        row = layout.row()
        row.prop(item, 'factor', text='Fac', slider=True)


class VRTXA_OT_MoveTransformationLayer(bpy.types.Operator):
    bl_idname = "vertx_artist.move_transformation_layer"
    bl_label = "Move Transformation Layer"
    bl_description = "Move Color Transformation Layer one step higher/lower"
    bl_options = {"REGISTER", "UNDO"}

    direction: bpy.props.IntProperty(name='direction', options={'HIDDEN'})

    def execute(self, context):
        modification_stack = bpy.context.view_layer.objects.active.vrtxa_modification_stacks[bpy.context.view_layer.objects.active.vrtxa_modification_stack_enum]

        if modification_stack.index == 0 and self.direction == -1:
            return {"FINISHED"}

        if modification_stack.index == len(modification_stack.modifications) - 1 and self.direction == 1:
            return {"FINISHED"}

        modification_stack.modifications.move(
            modification_stack.index,
            modification_stack.index + self.direction
        )

        modification_stack.index = modification_stack.index + self.direction

        refresh_default_material()
        return {"FINISHED"}


class VRTXA_OT_RemoveColorTransformation(bpy.types.Operator):
    bl_idname = "vertx_artist.remove_color_transformation"
    bl_label = "Remove Color Transformation"
    bl_description = "Remove selected Color Transformation"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        modification_stacks = bpy.context.view_layer.objects.active.vrtxa_modification_stacks

        for i, modification_stack in enumerate(modification_stacks):
            if modification_stack == [bpy.context.view_layer.objects.active.vrtxa_modification_stack_enum]:
                modification_stacks.remove(i)
                break

        bpy.context.view_layer.objects.active.vrtxa_modification_stack_enum = 'None'
        return {"FINISHED"}


class VRTXA_OT_AddColorTransformation(bpy.types.Operator):
    bl_idname = "vertx_artist.add_color_transformation"
    bl_label = "Add Color Transformation"
    bl_description = "Add new Color Transformation"
    bl_options = {"REGISTER", "UNDO"}
    transformation_name: bpy.props.StringProperty(name='transformation_name', default='New Transformation')

    def execute(self, context):
        item = bpy.context.view_layer.objects.active.vrtxa_modification_stacks.add()
        item.name = self.transformation_name
        bpy.context.view_layer.objects.active.vrtxa_modification_stack_enum = item.name

        return {"FINISHED"}


class VRTXA_OT_RemoveColorTransformationLayer(bpy.types.Operator):
    bl_idname = "vertx_artist.remove_color_transformation_layer"
    bl_label = "Remove Color Transformation Layer"
    bl_description = "Remove selected Color Transformation from the active Color Transformations Stack"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        modification_stack = bpy.context.view_layer.objects.active.vrtxa_modification_stacks[bpy.context.view_layer.objects.active.vrtxa_modification_stack_enum]

        if len(modification_stack.modifications) > modification_stack.index:
            modification_stack.modifications.remove(modification_stack.index)

        if modification_stack.index == len(modification_stack.modifications):
            modification_stack.index = modification_stack.index - 1

        refresh_default_material()
        return {"FINISHED"}


class VRTXA_OT_AddColorTransformationLayer(bpy.types.Operator):
    bl_idname = "vertx_artist.add_color_transformation_layer"
    bl_label = "Add Color Transformation Layer"
    bl_description = "Add new Color Transformation to the active Color Transformations Stack"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        modification_stack = bpy.context.view_layer.objects.active.vrtxa_modification_stacks[bpy.context.view_layer.objects.active.vrtxa_modification_stack_enum]
        modification_stack.modifications.add()

        refresh_default_material()

        modification_stack.index = len(modification_stack.modifications) - 1

        return {"FINISHED"}


class VRTXA_OT_RefreshColorTransformationView(bpy.types.Operator):
    bl_idname = "vertx_artist.refresh_color_transformation_view"
    bl_label = "Refresh Color Transformation View"
    bl_description = "Refresh render view of Color Transformation material"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        while len(bpy.context.object.material_slots) != 0:
            bpy.ops.object.material_slot_remove('INVOKE_DEFAULT')

        bpy.context.object.data.materials.append(refresh_default_material())

        return {"FINISHED"}

    def draw(self, context):
        self.layout.label(text='Warning - refreshing view WILL remove and replace all your object materials.', icon='ERROR')
        self.layout.prop(bpy.context.preferences.addons['vertx_artist'].preferences, 'hide_refresh_stack_warning', text="Don't show again")

    def invoke(self, context, event):
        if bpy.context.preferences.addons['vertx_artist'].preferences.hide_refresh_stack_warning:
            return self.execute(context)

        return context.window_manager.invoke_props_dialog(self, width=450)


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


class VRTXA_OT_ApplyColorTransformationStack(bpy.types.Operator):
    bl_idname = "vertx_artist.apply_color_transformation_stack"
    bl_label = "Apply Color Transformation Stack Popup"
    bl_description = "Create a new Color Layer from base layer, and apply the whole Color Transformation Stack"
    bl_options = {"REGISTER", "UNDO"}

    only_visible: bpy.props.EnumProperty(
        name='transformations_visible_enum',
        description='Apply only visible/all modifications',
        items=[('All', 'All', ''), ('Only Visible', 'Only Visible', '')]
    )

    @classmethod
    def poll(cls, context):
        return not bpy.context.object is None

    def execute(self, context):
        only_visible = self.only_visible == 'Only Visible'
        modification_stack = bpy.context.view_layer.objects.active.vrtxa_modification_stacks[bpy.context.view_layer.objects.active.vrtxa_modification_stack_enum]

        bpy.ops.geometry.color_attribute_add(name=f'{modification_stack.base_layer} / {modification_stack.name}', domain='CORNER', data_type='BYTE_COLOR')

        obj = bpy.context.object

        color_attributes = obj.data.color_attributes
        base_layer = color_attributes.get(modification_stack.base_layer)

        if base_layer is None:
            self.report({'WARNING'}, message="Base layer not found.")
            return {"FINISHED"}

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

        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'only_visible', text='Apply', icon='NONE', emboss=True)

    def invoke(self, context, event):
        modification_stack = bpy.context.view_layer.objects.active.vrtxa_modification_stacks[bpy.context.view_layer.objects.active.vrtxa_modification_stack_enum]

        if all(i.include for i in modification_stack.modifications):
            return self.execute(context)

        return context.window_manager.invoke_props_dialog(self, width=300)


class VRTXA_OT_ToggleColorTransformationVisibility(bpy.types.Operator):
    bl_idname = "vertx_artist.toggle_color_transformation_visibility"
    bl_label = "Toggle Color Transformation Visibility"
    bl_description = "Change Color Transformation Visibility"
    bl_options = {"REGISTER", "UNDO"}

    modification_index: bpy.props.IntProperty(name='modification_index', default=0)

    def execute(self, context):
        modification_stack = bpy.context.view_layer.objects.active.vrtxa_modification_stacks[bpy.context.view_layer.objects.active.vrtxa_modification_stack_enum]
        modification_stack.modifications[self.modification_index].include = not modification_stack.modifications[self.modification_index].include

        return {"FINISHED"}


class VRTXA_PT_ColorTransformations(bpy.types.Panel):
    bl_label = 'Color Transformations'
    bl_idname = 'VRTXA_PT_ColorTransformations'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'
    bl_category = 'Color Transformations - VertX Artist'

    @classmethod
    def poll(cls, context):
        return bpy.context.object is not None

    def draw(self, context):
        row = self.layout.row()            

        if bpy.context.view_layer.objects.active.vrtxa_modification_stack_enum != 'None':
            split = row.split(factor=0.93, align=True)
            active_modification_stack = bpy.context.view_layer.objects.active.vrtxa_modification_stacks[bpy.context.view_layer.objects.active.vrtxa_modification_stack_enum]
            split.prop(active_modification_stack, 'name', text='')
            split.prop(bpy.context.view_layer.objects.active, 'vrtxa_modification_stack_enum', text='')
        else:
            row.prop(bpy.context.view_layer.objects.active, 'vrtxa_modification_stack_enum', text='')

        row = row.row(align=True)
        row.operator('vertx_artist.add_color_transformation', text='', icon='ADD')
        inner_row = row.row(align=True)
        inner_row.enabled = bpy.context.view_layer.objects.active.vrtxa_modification_stack_enum != 'None'
        inner_row.operator('vertx_artist.remove_color_transformation', text='', icon='REMOVE')

        if bpy.context.view_layer.objects.active.vrtxa_modification_stack_enum != 'None':
            top_col = self.layout.column()
            top_col.prop(active_modification_stack, 'base_layer', text='Base Layer')
            row = top_col.row()

            row.template_list('VRTXA_UL_DisplayModifications', '', active_modification_stack, 'modifications', active_modification_stack, 'index')

            outer_col = row.column()
            outer_col.separator(factor=0.5)
            col = outer_col.column(align=True)
            col.operator('vertx_artist.add_color_transformation_layer', text='', icon='ADD')

            row = col.row(align=True)
            row.enabled = len(active_modification_stack.modifications) != 0
            row.operator('vertx_artist.remove_color_transformation_layer', text='', icon='REMOVE')

            outer_col.separator(factor=0.25)
            col = outer_col.column(align=True)
            row = col.row(align=True)
            row.enabled = len(active_modification_stack.modifications) != 0 and active_modification_stack.index != 0
            op = row.operator('vertx_artist.move_transformation_layer', text='', icon='TRIA_UP')
            op.direction = -1

            row = col.row(align=True)
            row.enabled = len(active_modification_stack.modifications) != 0 and active_modification_stack.index != len(active_modification_stack.modifications) - 1
            op = row.operator('vertx_artist.move_transformation_layer', text='', icon='TRIA_DOWN')
            op.direction = 1

            col.separator(factor=0.0)

            row = top_col.row()
            row.operator('vertx_artist.refresh_color_transformation_view', text='Refresh Material Preview', icon='FILE_REFRESH')

            row = row.row()
            row.enabled = len(active_modification_stack.modifications) != 0
            op = row.operator('vertx_artist.apply_color_transformation_stack', text='Apply Stack', icon='CHECKMARK')


def register():
    bpy.utils.register_class(VRTXA_GROUP_Modification)
    bpy.utils.register_class(VRTXA_GROUP_ModificationStack)

    def modification_stack_enum_items(self, context):
        return items_to_enum('None', *[i.name for i in bpy.context.view_layer.objects.active.vrtxa_modification_stacks])

    bpy.types.Object.vrtxa_modification_stack_enum = bpy.props.EnumProperty(
        name='modification_stack_enum',
        items=modification_stack_enum_items,
        update=on_update_refresh
    )
    bpy.types.Object.vrtxa_modification_stacks = bpy.props.CollectionProperty(
        name='modification_stacks',
        type=VRTXA_GROUP_ModificationStack
    )
    bpy.types.Scene.vrtxa_transformations_visible_enum = bpy.props.EnumProperty(
        name='transformations_visible_enum',
        items=[('All', 'All', ''), ('Only Visible', 'Only Visible', '')]
    )

    bpy.utils.register_class(VRTXA_OT_MoveTransformationLayer)
    bpy.utils.register_class(VRTXA_OT_RemoveColorTransformation)
    bpy.utils.register_class(VRTXA_OT_AddColorTransformation)
    bpy.utils.register_class(VRTXA_OT_RemoveColorTransformationLayer)
    bpy.utils.register_class(VRTXA_OT_AddColorTransformationLayer)
    bpy.utils.register_class(VRTXA_OT_RefreshColorTransformationView)
    bpy.utils.register_class(VRTXA_OT_ApplyColorTransformationStack)
    bpy.utils.register_class(VRTXA_OT_ToggleColorTransformationVisibility)

    bpy.utils.register_class(VRTXA_UL_DisplayModifications)
    bpy.utils.register_class(VRTXA_PT_ColorTransformations)


def unregister():
    bpy.utils.unregister_class(VRTXA_GROUP_Modification)
    bpy.utils.unregister_class(VRTXA_GROUP_ModificationStack)

    del bpy.types.Object.vrtxa_modification_stack_enum
    del bpy.types.Object.vrtxa_modification_stacks
    del bpy.types.Scene.vrtxa_transformations_visible_enum

    bpy.utils.unregister_class(VRTXA_OT_MoveTransformationLayer)
    bpy.utils.unregister_class(VRTXA_OT_RemoveColorTransformation)
    bpy.utils.unregister_class(VRTXA_OT_AddColorTransformation)
    bpy.utils.unregister_class(VRTXA_OT_RemoveColorTransformationLayer)
    bpy.utils.unregister_class(VRTXA_OT_AddColorTransformationLayer)
    bpy.utils.unregister_class(VRTXA_OT_RefreshColorTransformationView)
    bpy.utils.unregister_class(VRTXA_OT_ApplyColorTransformationStack)
    bpy.utils.unregister_class(VRTXA_OT_ToggleColorTransformationVisibility)

    bpy.utils.unregister_class(VRTXA_UL_DisplayModifications)
    bpy.utils.unregister_class(VRTXA_PT_ColorTransformations)
