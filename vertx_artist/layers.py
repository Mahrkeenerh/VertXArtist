import colorsys

import bpy
import bmesh
from bpy.app.handlers import persistent

from .object_colors import gamma_correct, inverse_gamma
from .tools import on_name_update, col_attr_exists
from .transformations import refresh_default_material


class VRTXA_GROUP_Layer(bpy.types.PropertyGroup):
    def on_layer_name_update(self, context):
        on_name_update(self, [i.name for i in context.view_layer.objects.active.vrtxa_layers], "Attribute")
    name: bpy.props.StringProperty(
        name='name',
        description='Name of the layer',
        update=on_layer_name_update
    )
    channels: bpy.props.EnumProperty(
        name='channels',
        items=[
            ('RGBA', 'RGBA', ''),
            ('RGB', 'RGB', ''),
            ('R', 'R', ''),
            ('G', 'G', ''),
            ('B', 'B', ''),
            ('A', 'A', ''),
            ('RG', 'RG', ''),
            ('RB', 'RB', ''),
            ('GB', 'GB', '')
        ]
    )


class VRTXA_OT_ToggleLayerEditing(bpy.types.Operator):
    bl_idname = "vertx_artist.toggle_layer_editing"
    bl_label = "Toggle Layer Editing with Warning"
    bl_description = "Enable or disable channel editing"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bpy.context.scene.vrtxa_enable_editing = not bpy.context.scene.vrtxa_enable_editing

        for a in bpy.context.screen.areas:
            a.tag_redraw()

        return {"FINISHED"}

    def draw(self, context):
        if bpy.context.preferences.addons['vertx_artist'].preferences.hide_edit_warning:
            return

        layout = self.layout
        layout.label(text='Warning - editing layer channels may result in unwanted behavior.', icon_value=2)
        layout.prop(bpy.context.preferences.addons['vertx_artist'].preferences, 'hide_edit_warning', text="Don't show again", icon_value=0)

    def invoke(self, context, event):
        if bpy.context.preferences.addons['vertx_artist'].preferences.hide_edit_warning:
            return self.execute(context)

        return context.window_manager.invoke_props_dialog(self, width=400)


class VRTXA_OT_ToggleRenderColorLayer(bpy.types.Operator):
    bl_idname = "vertx_artist.toggle_render_color_layer"
    bl_label = "Toggle Render Color Layer"
    bl_description = "Set Color Attribute used for rendering, and Color Transformation preview"
    bl_options = {"REGISTER", "UNDO"}
    layer_name: bpy.props.StringProperty(name='layer_name')

    def execute(self, context):
        bpy.ops.geometry.color_attribute_render_set('INVOKE_DEFAULT', name=self.layer_name)
        refresh_default_material()
        return {"FINISHED"}


channel_names_enum = {'None': ('None', 'None', 'None')}

def generate_layers_enum_function(allowed_layers, with_none=True):
    channel_list = []

    if with_none:
        channel_list.append(channel_names_enum['None'])

    for i in range(len(bpy.context.view_layer.objects.active.vrtxa_layers)):
        if bpy.context.view_layer.objects.active.vrtxa_layers[i].channels in allowed_layers:
            channel_names_enum[bpy.context.view_layer.objects.active.vrtxa_layers[i].name] = (
                bpy.context.view_layer.objects.active.vrtxa_layers[i].name,
                bpy.context.view_layer.objects.active.vrtxa_layers[i].name,
                bpy.context.view_layer.objects.active.vrtxa_layers[i].name
            )

            channel_list.append(channel_names_enum[bpy.context.view_layer.objects.active.vrtxa_layers[i].name])

    return channel_list


def combine_layers(
    channels: str,
    channels_list: list,
    channels_values: list,
    channels_gamma: list
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
    layers = bpy.context.view_layer.objects.active.vrtxa_layers

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


class VRTXA_OT_AddLayer(bpy.types.Operator):
    bl_idname = "vertx_artist.add_layer"
    bl_label = "Add Layer"
    bl_description = "Add new layer, or combine channels from other layers"
    bl_options = {"REGISTER", "UNDO"}

    layer_name: bpy.props.StringProperty(name='layer_name', default='Attribute', options={'SKIP_SAVE'})
    channels: bpy.props.EnumProperty(name='channels', options={'SKIP_SAVE'}, items=[
        ('RGBA', 'RGBA', ''),
        ('RGB', 'RGB', ''),
        ('R', 'R', ''),
        ('G', 'G', ''),
        ('B', 'B', ''),
        ('A', 'A', ''),
        ('RG', 'RG', ''),
        ('RB', 'RB', ''),
        ('GB', 'GB', '')
    ])

    def r_channel_enum_items(self, context):
        return generate_layers_enum_function(['RGBA', 'RGB', 'RB', 'R', 'RG'])

    def g_channel_enum_items(self, context):
        return generate_layers_enum_function(['GB', 'RGBA', 'RGB', 'G', 'RG'])

    def b_channel_enum_items(self, context):
        return generate_layers_enum_function(['GB', 'RGBA', 'B', 'RGB', 'RB'])

    def a_channel_enum_items(self, context):
        return generate_layers_enum_function(['A', 'RGBA'])

    r_channel: bpy.props.EnumProperty(name='r_channel', items=r_channel_enum_items, options={'SKIP_SAVE'})
    g_channel: bpy.props.EnumProperty(name='g_channel', items=g_channel_enum_items, options={'SKIP_SAVE'})
    b_channel: bpy.props.EnumProperty(name='b_channel', items=b_channel_enum_items, options={'SKIP_SAVE'})
    a_channel: bpy.props.EnumProperty(name='a_channel', items=a_channel_enum_items, options={'SKIP_SAVE'})
    r_channel_value: bpy.props.FloatProperty(name='r_channel_value', default=0.0, min=0.0, max=1.0, options={'SKIP_SAVE'})
    g_channel_value: bpy.props.FloatProperty(name='g_channel_value', default=0.0, min=0.0, max=1.0, options={'SKIP_SAVE'})
    b_channel_value: bpy.props.FloatProperty(name='b_channel_value', default=0.0, min=0.0, max=1.0, options={'SKIP_SAVE'})
    a_channel_value: bpy.props.FloatProperty(name='a_channel_value', default=1.0, min=0.0, max=1.0, options={'SKIP_SAVE'})

    r_gamma: bpy.props.EnumProperty(name='r_gamma', options={'SKIP_SAVE'}, items=[
        ('None', 'None', 'None'),
        ('Gamma', 'Gamma', 'Gamma'),
        ('Inverse', 'Inverse', 'Inverse')
    ])
    g_gamma: bpy.props.EnumProperty(name='g_gamma', options={'SKIP_SAVE'}, items=[
        ('None', 'None', 'None'),
        ('Gamma', 'Gamma', 'Gamma'),
        ('Inverse', 'Inverse', 'Inverse')
    ])
    b_gamma: bpy.props.EnumProperty(name='b_gamma', options={'SKIP_SAVE'}, items=[
        ('None', 'None', 'None'),
        ('Gamma', 'Gamma', 'Gamma'),
        ('Inverse', 'Inverse', 'Inverse')
    ])
    a_gamma: bpy.props.EnumProperty(name='a_gamma', options={'SKIP_SAVE'}, items=[
        ('None', 'None', 'None'),
        ('Gamma', 'Gamma', 'Gamma'),
        ('Inverse', 'Inverse', 'Inverse')
    ])

    def execute(self, context):
        bpy.ops.geometry.color_attribute_add(name=self.layer_name, domain='CORNER', data_type='BYTE_COLOR', color=(0.0, 0.0, 0.0, 1.0))
        bpy.context.view_layer.objects.active.vrtxa_layers[bpy.context.object.data.color_attributes.active_color.name].channels = self.channels

        combine_layers(
            channels=self.channels,
            channels_list=[self.r_channel, self.g_channel, self.b_channel, self.a_channel],
            channels_values=[self.r_channel_value, self.g_channel_value, self.b_channel_value, self.a_channel_value],
            channels_gamma=[self.r_gamma, self.g_gamma, self.b_gamma, self.a_gamma]
        )

        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        row = layout.row(heading='Layer Name')
        row.prop(self, 'layer_name', text='')

        row = layout.row(heading='Channels')
        row.prop(self, 'channels', text='')

        layout.separator(factor=0.5)
        row = layout.row(heading='Layer Name')
        row.label(text='')
        row.label(text='Color Layer')
        row.label(text='Flat Value')
        row.label(text='Correction')

        for ch in ['R', 'G', 'B', 'A']:
            if ch in self.channels:
                row = layout.row(heading=f'{ch} channel')
                row.prop(self, f'{ch.lower()}_channel', text='')
                inner_row = row.row()
                inner_row.enabled = getattr(self, f'{ch.lower()}_channel') == 'None'
                inner_row.prop(self, f'{ch.lower()}_channel_value', text='')
                inner_row.prop(self, f'{ch.lower()}_gamma', text='')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)


class VRTXA_OT_SynchronizeLayers(bpy.types.Operator):
    bl_idname = "vertx_artist.synchronize_layers"
    bl_label = "Synchronize Layers"
    bl_description = "Synchronize VertX Artist Color Layers with Color Attributes"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        refresh_layers()
        return {"FINISHED"}


@persistent
def refresh_layers(dummy):
    if bpy.context.object is  None:
        return

    # same size
    if len(bpy.context.object.data.color_attributes) == len(bpy.context.view_layer.objects.active.vrtxa_layers):
        for i in range(len(bpy.context.object.data.color_attributes)):
            if bpy.context.object.data.color_attributes[i].name not in bpy.context.view_layer.objects.active.vrtxa_layers:
                bpy.context.view_layer.objects.active.vrtxa_layers[i].name = bpy.context.object.data.color_attributes[i].name
                return

    if len(bpy.context.object.data.color_attributes) > len(bpy.context.view_layer.objects.active.vrtxa_layers):
        for i in range(len(bpy.context.object.data.color_attributes)):
            if bpy.context.object.data.color_attributes[i].name not in bpy.context.view_layer.objects.active.vrtxa_layers:
                new_layer = bpy.context.view_layer.objects.active.vrtxa_layers.add()
                new_layer.name = bpy.context.object.data.color_attributes[i].name
                return

    for i in range(len(bpy.context.view_layer.objects.active.vrtxa_layers)):
        if bpy.context.view_layer.objects.active.vrtxa_layers[i].name not in bpy.context.object.data.color_attributes:
            bpy.context.view_layer.objects.active.vrtxa_layers.remove(i)
            return


class VRTXA_UL_DisplayLayers(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(bpy.context.object.data.color_attributes[index], 'name', text='', icon_value=202, emboss=False)
        row = layout.row()
        row.enabled = bpy.context.scene.vrtxa_enable_editing

        if bpy.context.scene.vrtxa_enable_editing:
            row.prop(item, 'channels', text='')
        else:
            row.label(text=item.channels)

        if index == bpy.context.object.data.color_attributes.render_color_index:
            op = layout.operator('vertx_artist.toggle_render_color_layer', text='', icon_value=258, emboss=False)
            op.layer_name = bpy.context.object.data.color_attributes[index].name
        else:
            op = layout.operator('vertx_artist.toggle_render_color_layer', text='', icon_value=257, emboss=False)
            op.layer_name = bpy.context.object.data.color_attributes[index].name


class VRTXA_PT_ColorLayers(bpy.types.Panel):
    bl_label = 'Color Layers'
    bl_idname = 'VRTXA_PT_ColorLayers'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'
    bl_category = 'Color Layers - VertX Artist'

    @classmethod
    def poll(cls, context):
        return bpy.context.object is not None

    def draw(self, context):
        layout = self.layout
        if bpy.context.object.data is None or bpy.context.object.data.color_attributes.active_color is None:
            row = layout.row()
            row.alert = True
            row.operator('vertx_artist.add_layer', text='Add Color Layer', icon_value=31)

        if len(bpy.context.object.data.color_attributes) != len(bpy.context.view_layer.objects.active.vrtxa_layers):
            row = layout.row()
            row.label(text=f'VertX Artist Color Layers: {len(bpy.context.view_layer.objects.active.vrtxa_layers)}, Color Attributes: {len(bpy.context.object.data.color_attributes)}')
            row.alert = True
            row.operator('vertx_artist.synchronize_layers', text='Refresh', icon_value=692)

        row = layout.row()
        row.template_list('VRTXA_UL_DisplayLayers', '', bpy.context.view_layer.objects.active, 'vrtxa_layers', bpy.context.object.data.color_attributes, 'active_color_index')
    
        control_col = row.column()
        add_remove_col = control_col.column(align=True)
        add_remove_col.operator('vertx_artist.add_layer', text='', icon_value=31)
        add_remove_col.operator('geometry.color_attribute_remove', text='', icon_value=32)
        control_col.separator(factor=0.25)
        control_col.operator('vertx_artist.toggle_layer_editing', text='', icon_value=197, depress=bpy.context.scene.vrtxa_enable_editing)

        display_alpha_extractbake(self.layout, 'Extract Alpha', 'Bake Alpha')


def display_alpha_extractbake(layout, extract_name, bake_name):
    if not col_attr_exists():
        return

    channels = bpy.context.view_layer.objects.active.vrtxa_layers[bpy.context.object.data.color_attributes.active_color_index].channels

    if channels == 'RGBA':
        layout.operator('vertx_artist.extract_alpha', text=extract_name, icon_value=598)

    if channels == 'A':
        op = layout.operator('vertx_artist.bake_alpha', text=bake_name, icon_value=599)
        op.layer_name = ''


def display_alpha_panel(self, context):
    if not (bpy.context.mode == 'OBJECT' or bpy.context.mode == 'EDIT_MESH'):
        return

    box = self.layout.box()
    box.label(text='Alpha Gradients', icon_value=126)
    row = box.row()
    row.prop(bpy.context.scene, 'vrtxa_neg_axis', text='Negative', icon_value=0, emboss=True)
    row.prop(bpy.context.scene, 'vrtxa_pos_axis', text='Positive', icon_value=0, emboss=True)

    row = box.row()
    op = row.operator('vertx_artist.apply_alpha_gradient', text='Apply Gradient')
    op.neg_axis = bpy.context.scene.vrtxa_neg_axis
    op.pos_axis = bpy.context.scene.vrtxa_pos_axis

    op = row.operator('vertx_artist.apply_alpha_gradient', text='Apply Positive')
    op.neg_axis = bpy.context.scene.vrtxa_pos_axis
    op.pos_axis = bpy.context.scene.vrtxa_pos_axis

    display_alpha_extractbake(box, 'Show Alpha', 'Hide Alpha')
    self.layout.separator(factor=2.0)


class VRTXA_OT_SelectRGBALayer(bpy.types.Operator):
    bl_idname = "vertx_artist.select_rgba_layer"
    bl_label = "Select RGBA Layer"
    bl_description = "Select RGBA layer to bake Alpha into"
    bl_options = {"REGISTER", "UNDO"}

    def rgba_layers_enum_items(self, context):
        values = generate_layers_enum_function(['RGBA'], False)

        if len(values) == 0:
            values = [('None', 'None', 'None')]

        return values

    rgba_layers: bpy.props.EnumProperty(name='rgba_layers', items=rgba_layers_enum_items)

    def execute(self, context):
        bake_alpha(self.rgba_layers)
        return {"FINISHED"}

    def draw(self, context):
        self.layout.prop(self, 'rgba_layers', text='')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)


class VRTXA_OT_ExtractAlpha(bpy.types.Operator):
    bl_idname = "vertx_artist.extract_alpha"
    bl_label = "Extract Alpha"
    bl_description = "Create a new alpha layer from the selected RGBA layer"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        active_obj = bpy.context.view_layer.objects.active

        for obj in bpy.context.view_layer.objects.selected:
            bpy.context.view_layer.objects.active = obj

            if len(bpy.context.view_layer.objects.active.vrtxa_layers) == 0:
                bpy.ops.geometry.color_attribute_add(name='Attribute', domain='CORNER', data_type='BYTE_COLOR')

            if bpy.context.view_layer.objects.active.vrtxa_layers[bpy.context.object.data.color_attributes.active_color_index].channels == 'RGBA':
                bpy.ops.vertx_artist.add_layer(
                    layer_name=bpy.context.view_layer.objects.active.vrtxa_layers[bpy.context.object.data.color_attributes.active_color_index].name + '_alpha',
                    channels='A',
                    a_channel=bpy.context.view_layer.objects.active.vrtxa_layers[bpy.context.object.data.color_attributes.active_color_index].name,
                )

        bpy.context.view_layer.objects.active = active_obj
        bpy.ops.vertx_artist.refresh('INVOKE_DEFAULT')

        return {"FINISHED"}


class VRTXA_OT_Bake_Alpha(bpy.types.Operator):
    bl_idname = "vertx_artist.bake_alpha"
    bl_label = "Bake Alpha"
    bl_description = "Write the Alpha layer into the original RGBA layer. Will ask to select RGBA layer if it can't be detected automatically"
    bl_options = {"REGISTER", "UNDO"}
    
    layer_name: bpy.props.StringProperty(name='layer_name')

    def execute(self, context):
        active_obj = bpy.context.view_layer.objects.active

        for obj in bpy.context.view_layer.objects.selected:
            bpy.context.view_layer.objects.active = obj

            if len(bpy.context.view_layer.objects.active.vrtxa_layers) == 0:
                bpy.ops.geometry.color_attribute_add(name='Attribute', domain='CORNER', data_type='BYTE_COLOR')

            if bpy.context.view_layer.objects.active.vrtxa_layers[bpy.context.object.data.color_attributes.active_color_index].channels == 'A':
                bake_alpha(self.layer_name)

        bpy.context.view_layer.objects.active = active_obj
        bpy.ops.vertx_artist.refresh('INVOKE_DEFAULT')

        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


def bake_alpha(layer_name):
    if layer_name == 'None':
        return

    # auto detect layer name
    if layer_name == '':
        active_layer_name = bpy.context.view_layer.objects.active.vrtxa_layers[bpy.context.object.data.color_attributes.active_color_index].name
        base_layer_name = active_layer_name.split('_alpha')[0]

        if base_layer_name in bpy.context.view_layer.objects.active.vrtxa_layers and active_layer_name != base_layer_name:
            layer_name = base_layer_name
        else:
            bpy.ops.vertx_artist.select_rgba_layer('INVOKE_DEFAULT')
            return

    temp_layer_idx = bpy.context.object.data.color_attributes.active_color_index
    bpy.context.object.data.color_attributes.active_color_index = bpy.context.view_layer.objects.active.vrtxa_layers.find(layer_name)

    combine_layers(
        channels='NONE',
        channels_list=[layer_name, layer_name, layer_name, bpy.context.view_layer.objects.active.vrtxa_layers[temp_layer_idx].name],
        channels_values=[],
        channels_gamma=['None', 'None', 'None', 'None']
    )

    bpy.context.object.data.color_attributes.active_color_index = temp_layer_idx
    bpy.ops.geometry.color_attribute_remove('INVOKE_DEFAULT')
    bpy.context.object.data.color_attributes.active_color_index = bpy.context.view_layer.objects.active.vrtxa_layers.find(layer_name)


def register():
    bpy.utils.register_class(VRTXA_GROUP_Layer)
    bpy.types.Object.vrtxa_layers = bpy.props.CollectionProperty(name='layers', description='', type=VRTXA_GROUP_Layer)
    bpy.types.Scene.vrtxa_enable_editing = bpy.props.BoolProperty(name='vrtxa_enable_editing', default=False)
    bpy.types.Scene.vrtxa_neg_axis = bpy.props.FloatProperty(name='neg_axis', default=0.0, min=0.0, max=1.0)
    bpy.types.Scene.vrtxa_pos_axis = bpy.props.FloatProperty(name='pos_axis', default=1.0, min=0.0, max=1.0)

    bpy.utils.register_class(VRTXA_OT_ToggleLayerEditing)
    bpy.utils.register_class(VRTXA_OT_ToggleRenderColorLayer)
    bpy.utils.register_class(VRTXA_OT_AddLayer)
    bpy.utils.register_class(VRTXA_OT_SynchronizeLayers)
    bpy.utils.register_class(VRTXA_OT_SelectRGBALayer)
    bpy.utils.register_class(VRTXA_OT_ExtractAlpha)
    bpy.utils.register_class(VRTXA_OT_Bake_Alpha)

    bpy.app.handlers.depsgraph_update_post.append(refresh_layers)
    bpy.types.VIEW3D_PT_tools_active.prepend(display_alpha_panel)

    bpy.utils.register_class(VRTXA_UL_DisplayLayers)
    bpy.utils.register_class(VRTXA_PT_ColorLayers)


def unregister():
    bpy.utils.unregister_class(VRTXA_GROUP_Layer)
    del bpy.types.Object.vrtxa_layers
    del bpy.types.Scene.vrtxa_enable_editing
    del bpy.types.Scene.vrtxa_neg_axis
    del bpy.types.Scene.vrtxa_pos_axis

    bpy.utils.unregister_class(VRTXA_OT_ToggleLayerEditing)
    bpy.utils.unregister_class(VRTXA_OT_ToggleRenderColorLayer)
    bpy.utils.unregister_class(VRTXA_OT_AddLayer)
    bpy.utils.unregister_class(VRTXA_OT_SynchronizeLayers)
    bpy.utils.unregister_class(VRTXA_OT_SelectRGBALayer)
    bpy.utils.unregister_class(VRTXA_OT_ExtractAlpha)
    bpy.utils.unregister_class(VRTXA_OT_Bake_Alpha)

    bpy.app.handlers.depsgraph_update_post.remove(refresh_layers)
    bpy.types.VIEW3D_PT_tools_active.remove(display_alpha_panel)

    bpy.utils.unregister_class(VRTXA_UL_DisplayLayers)
    bpy.utils.unregister_class(VRTXA_PT_ColorLayers)
