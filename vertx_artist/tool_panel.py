import os

import bpy
import bpy.utils.previews

from .tools import col_attr_exists
from .layers import display_alpha_extractbake, display_alpha_panel


_icons = None


class VRTXA_PT_PreferencesPopout(bpy.types.Panel):
    bl_label = 'Preferences'
    bl_idname = 'VRTXA_PT_PreferencesPopout'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        layout = self.layout
        layout.label(text='Preferences')

        row = layout.row()
        row.label(text='Panel Location:')
        row.prop(bpy.context.preferences.addons['vertx_artist'].preferences, 'panel_location', text='')

        col = layout.column(align=True)
        col.prop(bpy.context.preferences.addons['vertx_artist'].preferences, 'color_grid_columns', text='Color Grid Columns')
        col.prop(bpy.context.preferences.addons['vertx_artist'].preferences, 'object_color_columns', text='Object Color Columns')
        col.prop(bpy.context.preferences.addons['vertx_artist'].preferences, 'palette_grid_columns', text='Palette Columns')

        layout.prop(bpy.context.preferences.addons['vertx_artist'].preferences, 'selection_tolerance', text='Default Selection Tolerance')

        box = layout.box()
        box.prop(bpy.context.preferences.addons['vertx_artist'].preferences, 'hide_edit_warning', text='Hide Edit Warning')
        box.prop(bpy.context.preferences.addons['vertx_artist'].preferences, 'hide_refresh_stack_warning', text='Hide Refresh Stack Warning')


# Main header panel
class VRTXA_PT_Header(bpy.types.Panel):
    bl_label = "Header"
    bl_idname = "VRTXA_PT_Header"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VertX Artist"
    bl_order = 0  # Will be displayed first

    @classmethod
    def poll(cls, context):
        return bpy.context.mode in ['PAINT_VERTEX', 'EDIT_MESH', 'OBJECT']

    def draw(self, context):
        display_header(self.layout)

# Palettes panel
class VRTXA_PT_Palettes(bpy.types.Panel):
    bl_label = "Color Palettes"
    bl_idname = "VRTXA_PT_Palettes"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VertX Artist"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 1  # Default display order

    @classmethod
    def poll(cls, context):
        return bpy.context.mode in ['PAINT_VERTEX', 'EDIT_MESH']

    def draw(self, context):
        layout = self.layout
        display_palettes(layout)

        row = layout.row(align=True)
        row.operator('vertx_artist.import_palette', text='Import Palette', icon_value=706)
        row.operator('vertx_artist.create_palette', text='Create Palette', icon_value=31)


# Object colors panel
class VRTXA_PT_ObjectColors(bpy.types.Panel):
    bl_label = "Object Colors"
    bl_idname = "VRTXA_PT_ObjectColors"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VertX Artist"
    bl_order = 2  # Default display order

    @classmethod
    def poll(cls, context):
        if bpy.context.mode == 'OBJECT':
            return True
        elif bpy.context.mode == 'EDIT_MESH':
            return col_attr_exists()
        return False

    def draw(self, context):
        display_object_colors(self.layout)


# Vertex tools panel
class VRTXA_PT_VertexTools(bpy.types.Panel):
    bl_label = "Vertex Paint Tools"
    bl_idname = "VRTXA_PT_VertexTools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VertX Artist"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 3  # Default display order

    @classmethod
    def poll(cls, context):
        return bpy.context.mode == 'PAINT_VERTEX'

    def draw(self, context):
        layout = self.layout
        split = layout.split(align=True)
        split.enabled = bpy.context.mode == 'PAINT_VERTEX'

        inner_split = split.split(align=True)
        inner_split.operator('paint.vertex_color_brightness_contrast', text='Brightness/Contrast')
        inner_split.operator('paint.vertex_color_hsv', text='HSV')

        split = layout.split(align=True)
        inner_split = split.split(align=True)
        inner_split.operator('paint.vertex_color_smooth', text='Smooth')
        inner_split.operator('paint.vertex_color_dirt', text='Dirt')


# Alpha gradients panel 
class VRTXA_PT_AlphaGradient(bpy.types.Panel):
    bl_label = "Alpha Gradients"
    bl_idname = "VRTXA_PT_AlphaGradient"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VertX Artist"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 4  # Default display order

    @classmethod
    def poll(cls, context):
        return bpy.context.mode == 'EDIT_MESH' and col_attr_exists()

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(bpy.context.scene, 'vrtxa_neg_axis', text='Negative', icon_value=0, emboss=True)
        row.prop(bpy.context.scene, 'vrtxa_pos_axis', text='Positive', icon_value=0, emboss=True)

        row = layout.row()
        op = row.operator('vertx_artist.apply_alpha_gradient', text='Apply Gradient')
        op.neg_axis = bpy.context.scene.vrtxa_neg_axis
        op.pos_axis = bpy.context.scene.vrtxa_pos_axis

        op = row.operator('vertx_artist.apply_alpha_gradient', text='Apply Positive')
        op.neg_axis = bpy.context.scene.vrtxa_pos_axis
        op.pos_axis = bpy.context.scene.vrtxa_pos_axis

        display_alpha_extractbake(layout, 'Show Alpha', 'Hide Alpha')


def can_draw():
    obj_att_exists = col_attr_exists()
    paint_enabled = bpy.context.object.data.use_paint_mask or bpy.context.object.data.use_paint_mask_vertex
    return obj_att_exists and (paint_enabled or bpy.context.mode == 'EDIT_MESH')


def display_header(layout):
    box = layout.box()
    row = box.row()
    row.template_icon(icon_value=77, scale=1.0)
    row.label(text='VertX Artist')
    row.popover('VRTXA_PT_PreferencesPopout', text='', icon_value=233)

    row = box.row()
    row.prop(bpy.context.scene, 'vrtxa_static_color', text='Set Color', emboss=True)

    col = row.column(align=True)
    col.enabled = can_draw()

    op = col.operator('vertx_artist.set_color', text='', icon_value=36)
    op.color = bpy.context.scene.vrtxa_static_color

    if not col_attr_exists():
        row = box.row()
        row.alert = True
        op = row.operator('vertx_artist.add_layer', text='Add Color Layer')


def display_object_colors(layout):
    box = layout.box()
    row = box.row()
    row.label(text='Adjust Object Colors', icon_value=202)
    row.operator('vertx_artist.showhide_object_colors', text='', icon_value=254 if bpy.context.scene.vrtxa_show_object_colors else 253, emboss=False)

    if bpy.context.scene.vrtxa_show_object_colors:
        row = row.row(align=True)
        row.operator('vertx_artist.checkpoint', text='', icon_value=_icons['white_flag.png'].icon_id)
        row.operator('vertx_artist.refresh', text='', icon_value=692)

        split = box.split()
        split.label(text='Active Color:')
        row = split.row(align=True)
        if len(bpy.context.scene.vrtxa_object_colors) != 0:
            op = row.operator('vertx_artist.select_by_color', text='', icon_value=256)
            op.selection_tolerance = bpy.context.preferences.addons['vertx_artist'].preferences.selection_tolerance
            op.select_color = bpy.context.scene.vrtxa_object_colors[bpy.context.scene.vrtxa_active_color_index].color
            op.select_color_idx = bpy.context.scene.vrtxa_object_colors[bpy.context.scene.vrtxa_active_color_index].index

            row.prop(bpy.context.scene.vrtxa_object_colors[bpy.context.scene.vrtxa_active_color_index], 'color', text='')

        box.label(text='Object Colors:', icon_value=251)
        grid = box.grid_flow(
            columns=bpy.context.preferences.addons['vertx_artist'].preferences.object_color_columns,
            row_major=True, even_columns=False, even_rows=False, align=False
        )
        for i in range(len(bpy.context.scene.vrtxa_object_colors)):
            row = grid.row(align=True)
            op = row.operator('vertx_artist.select_by_color', text='', icon_value=256)
            op.selection_tolerance = bpy.context.preferences.addons['vertx_artist'].preferences.selection_tolerance
            op.select_color = bpy.context.scene.vrtxa_object_colors[i].color
            op.select_color_idx = bpy.context.scene.vrtxa_object_colors[i].index

            row.prop(bpy.context.scene.vrtxa_object_colors[i], 'color', text='', emboss=True)


class VRTXA_UL_DisplayPalette(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, 'name', text='', emboss=False)
        row = layout.row(align=True)
        row.prop(item, 'color', text='')

        row = row.column(align=True)
        row.enabled = can_draw()
        op = row.operator('vertx_artist.set_color', text='', icon_value=36)
        op.color = item.color


def display_palettes(layout):
    outer_grid = layout.grid_flow(
        columns=bpy.context.preferences.addons['vertx_artist'].preferences.palette_grid_columns,
        row_major=True, even_columns=False, even_rows=False, align=False
    )
    for p_i in range(len(bpy.context.scene.vrtxa_palettes)):
        box = outer_grid.box()
        box.prop(bpy.context.scene.vrtxa_palettes[p_i], 'name', text='', icon_value=54)

        if bpy.context.preferences.addons['vertx_artist'].preferences.color_grid_columns != 1:
            grid = box.grid_flow(
                columns=bpy.context.preferences.addons['vertx_artist'].preferences.color_grid_columns,
                row_major=True, even_columns=False, even_rows=False, align=False
            )
            for c_i in range(len(bpy.context.scene.vrtxa_palettes[p_i].palette_colors)):
                outer_row = grid.row(align=True)
                outer_row.prop(bpy.context.scene.vrtxa_palettes[p_i].palette_colors[c_i], 'color', text='')
                col = outer_row.column(align=True)
                col.enabled = can_draw()
                op = col.operator('vertx_artist.set_color', text='', icon_value=36)
                op.color = bpy.context.scene.vrtxa_palettes[p_i].palette_colors[c_i].color

        else:
            outer_row = box.row()
            outer_row.template_list('VRTXA_UL_DisplayPalette', '', bpy.context.scene.vrtxa_palettes[p_i], 'palette_colors', bpy.context.scene.vrtxa_palettes[p_i], 'index')
            col = outer_row.column()
            inner_col = col.column(align=True)
            row = inner_col.row(align=True)
            op = row.operator('vertx_artist.add_palette_color', text='', icon_value=31)
            op.palette_index = p_i
            op.palette_color_index = bpy.context.scene.vrtxa_palettes[p_i].index
            op.color_name = 'Color'
            op.color = (1.0, 1.0, 1.0)

            row = inner_col.row(align=True)
            row.enabled = len(bpy.context.scene.vrtxa_palettes[p_i].palette_colors) != 0
            op = row.operator('vertx_artist.remove_palette_color', text='', icon_value=32)
            op.palette_index = p_i
            op.palette_color_index = bpy.context.scene.vrtxa_palettes[p_i].index

            col.separator(factor=0.25)

            col = col.column(align=True)
            row = col.row(align=True)
            row.enabled = len(list(bpy.context.scene.vrtxa_palettes[p_i].palette_colors)) != 0 and bpy.context.scene.vrtxa_palettes[p_i].index != 0
            op = row.operator('vertx_artist.move_palette_color', text='', icon_value=7)
            op.palette_index = p_i
            op.palette_color_index = bpy.context.scene.vrtxa_palettes[p_i].index
            op.direction = -1

            row = col.row(align=True)
            row.enabled = len(bpy.context.scene.vrtxa_palettes[p_i].palette_colors) != 0 and bpy.context.scene.vrtxa_palettes[p_i].index != len(bpy.context.scene.vrtxa_palettes[p_i].palette_colors) - 1
            op = row.operator('vertx_artist.move_palette_color', text='', icon_value=5)
            op.palette_index = p_i
            op.palette_color_index = bpy.context.scene.vrtxa_palettes[p_i].index
            op.direction = 1

        row = box.row(align=True)
        op = row.operator('vertx_artist.import_palette', text='Import', icon_value=706)
        op.palette_index = p_i
        op.replace = True

        inner_row = row.row(align=True)
        inner_row.enabled = len(bpy.context.scene.vrtxa_palettes[p_i].palette_colors) != 0
        op = inner_row.operator('vertx_artist.export_palettes', text='Export', icon_value=707)
        op.palette_index = p_i
        op = row.operator('vertx_artist.remove_palette', text='Remove', icon_value=21)
        op.palette_index = p_i
        row.separator(factor=0.25)

        inner_row = row.row(align=True)
        inner_inner_row = inner_row.row(align=True)
        inner_inner_row.enabled = p_i != 0
        op = inner_inner_row.operator('vertx_artist.move_palette', text='', icon_value=7)
        op.palette_index = p_i
        op.direction = -1

        inner_inner_row = inner_row.row(align=True)
        inner_inner_row.enabled = p_i != len(bpy.context.scene.vrtxa_palettes) - 1
        op = inner_inner_row.operator('vertx_artist.move_palette', text='', icon_value=5)
        op.palette_index = p_i
        op.direction = 1


def prepend_tool_panel(self, context):
    if bpy.context.mode not in ['PAINT_VERTEX', 'EDIT_MESH']:
        return

    display_header(self.layout)
    display_palettes(self.layout)

    row = self.layout.row(align=True)
    row.operator('vertx_artist.import_palette', text='Import Palette', icon_value=706)
    row.operator('vertx_artist.create_palette', text='Create Palette', icon_value=31)

    if bpy.context.mode == 'EDIT_MESH':
        if col_attr_exists():
            self.layout.separator(factor=1.0)
            display_object_colors(self.layout)

    else:
        self.layout.separator(factor=0.5)

        split = self.layout.split(align=True)
        split.enabled = bpy.context.mode == 'PAINT_VERTEX'

        inner_split = split.split(align=True)
        inner_split.operator('paint.vertex_color_brightness_contrast', text='Bri/Con')
        inner_split.operator('paint.vertex_color_hsv', text='HSV')

        inner_split = split.split(align=True)
        inner_split.operator('paint.vertex_color_smooth', text='Smooth')
        inner_split.operator('paint.vertex_color_dirt', text='Dirt')

    self.layout.separator(factor=0.5)


def prepend_object_tool_panel(self, context):
    if  bpy.context.mode == 'OBJECT':
        box = self.layout.box()
        row = box.row()
        row.label(text='Adjust Object Colors', icon_value=202)
        row.operator('vertx_artist.showhide_object_colors', text='', icon_value=254 if bpy.context.scene.vrtxa_show_object_colors else 253, emboss=False, depress=True)
        self.layout.separator(factor=0.5)


class VRTXA_MT_Pie(bpy.types.Menu):
    bl_idname = "VIEW3D_MT_vertx_artist_pie"
    bl_label = "VertXArtist: Quick Access"

    @classmethod
    def poll(cls, context):
        return bpy.context.mode == 'EDIT_MESH' or bpy.context.mode == 'PAINT_VERTEX'

    def draw(self, context):
        layout = self.layout.menu_pie()

        display_alpha_extractbake(layout, 'Show Alpha', 'Hide Alpha')
        op = layout.operator('vertx_artist.set_color', text='Set Color', icon_value=36)
        op.use_static = True

        layout.operator('vertx_artist.checkpoint', icon_value=_icons['white_flag.png'].icon_id)
        layout.operator('vertx_artist.refresh', text='Refresh', icon_value=692)


def register():
    global _icons
    _icons = bpy.utils.previews.new()
    if not 'white_flag.png' in _icons:
        _icons.load('white_flag.png', os.path.join(os.path.dirname(__file__), 'white_flag.png'), "IMAGE")

    bpy.utils.register_class(VRTXA_UL_DisplayPalette)
    bpy.utils.register_class(VRTXA_PT_PreferencesPopout)
    bpy.utils.register_class(VRTXA_MT_Pie)

    # Panel location based on preferences
    try:
        panel_location = bpy.context.preferences.addons['vertx_artist'].preferences.panel_location
    except:
        panel_location = 'TOOLS'  # Default to tools panel if preference not found

    if panel_location == 'NPANEL':
        # Register all N-panel classes as independent panels
        bpy.utils.register_class(VRTXA_PT_Header)
        bpy.utils.register_class(VRTXA_PT_Palettes)
        bpy.utils.register_class(VRTXA_PT_ObjectColors)
        bpy.utils.register_class(VRTXA_PT_VertexTools)
        bpy.utils.register_class(VRTXA_PT_AlphaGradient)
    else:
        # Original tool panel approach
        bpy.types.VIEW3D_PT_tools_active.prepend(display_alpha_panel)
        bpy.types.VIEW3D_PT_tools_active.prepend(prepend_tool_panel)
        bpy.types.VIEW3D_PT_tools_active.prepend(prepend_object_tool_panel)


def unregister():
    bpy.utils.previews.remove(_icons)

    bpy.utils.unregister_class(VRTXA_UL_DisplayPalette)
    bpy.utils.unregister_class(VRTXA_PT_PreferencesPopout)
    bpy.utils.unregister_class(VRTXA_MT_Pie)

    # Always try to remove tool panel prepends regardless of current setting
    try:
        bpy.types.VIEW3D_PT_tools_active.remove(display_alpha_panel)
        bpy.types.VIEW3D_PT_tools_active.remove(prepend_tool_panel)
        bpy.types.VIEW3D_PT_tools_active.remove(prepend_object_tool_panel)
    except:
        print('Could not remove tool panel')

    # Always try to unregister N panel classes regardless of current setting
    try:
        bpy.utils.unregister_class(VRTXA_PT_Header)
        bpy.utils.unregister_class(VRTXA_PT_Palettes)
        bpy.utils.unregister_class(VRTXA_PT_ObjectColors)
        bpy.utils.unregister_class(VRTXA_PT_VertexTools)
        bpy.utils.unregister_class(VRTXA_PT_AlphaGradient)
    except:
        print('Could not unregister N panel')
