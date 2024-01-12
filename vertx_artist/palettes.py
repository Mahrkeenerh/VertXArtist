import os
import re

import bpy
from bpy_extras.io_utils import ImportHelper, ExportHelper

from .tools import on_name_update


def on_palette_name_update(self, context):
    on_name_update(self, [i.name for i in context.scene.vrtxa_palettes], "Palette")


class VRTXA_OT_CreatePalette(bpy.types.Operator):
    bl_idname = "vertx_artist.create_palette"
    bl_label = "Create Palette"
    bl_description = "Create empty palette"
    bl_options = {"REGISTER", "UNDO"}
    palette_name: bpy.props.StringProperty(
        name='name',
        description='Name of the added palette',
        default='New Palette',
        update=on_palette_name_update
    )

    def execute(self, context):
        new_palette = bpy.context.scene.vrtxa_palettes.add()
        new_palette.name = self.palette_name
        return {"FINISHED"}


class VRTXA_OT_ImportPalette(bpy.types.Operator, ImportHelper):
    bl_idname = "vertx_artist.import_palette"
    bl_label = "Import Palette"
    bl_description = "Import a new palette and add it to the bottom"
    bl_options = {"REGISTER", "UNDO"}
    filter_glob: bpy.props.StringProperty(default='*.ccb;*.colors;*.gpl', options={'HIDDEN'})
    replace: bpy.props.BoolProperty(name='replace', description='Replace current palette', default=False, options={'HIDDEN', 'SKIP_SAVE'})
    palette_index: bpy.props.IntProperty(name='palette_index', options={'HIDDEN'}, min=0)

    def execute(self, context):
        path = self.filepath

        palette_name = os.path.basename(path).split(".")[0]
        palette_name = palette_name.replace("_", " ")
        file_extension = path.split(".")[-1]

        names = []
        colors = []

        match file_extension:
            case 'ccb':
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

            case 'colors':
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

            case 'gpl':
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

            case _:
                self.report({'ERROR'}, "Unknown file extension: " + file_extension)
                return {"CANCELLED"}

        new_palette = bpy.context.scene.vrtxa_palettes.add()
        new_palette.name = palette_name

        for name, color in zip(names, colors):
            new_col = new_palette.palette_colors.add()
            new_col.name = name
            new_col.color = color

        if self.replace and len(bpy.context.scene.vrtxa_palettes) > self.palette_index:
            bpy.context.scene.vrtxa_palettes.remove(self.palette_index)
            bpy.context.scene.vrtxa_palettes.move(len(bpy.context.scene.vrtxa_palettes) - 1, self.palette_index)

        return {"FINISHED"}


class VRTXA_OT_ExportPalettes(bpy.types.Operator):
    bl_idname = "vertx_artist.export_palettes"
    bl_label = "Export Palettes"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}
    palette_index: bpy.props.IntProperty(name='palette_index')

    def execute(self, context):
        return {"FINISHED"}

    def draw(self, context):
        op = self.layout.operator('vertx_artist.export_palette', text='Export as .ccb', icon_value=707, emboss=True, depress=False)
        op.palette_index = self.palette_index
        op.file_extension = "ccb"

        op = self.layout.operator('vertx_artist.export_palette', text='Export as .gpl', icon_value=707, emboss=True, depress=False)
        op.palette_index = self.palette_index
        op.file_extension = "gpl"

    def invoke(self, context, event):
        context.window_manager.invoke_props_popup(self, event)
        return self.execute(context)


class VRTXA_OT_ExportPalette(bpy.types.Operator, ExportHelper):
    bl_idname = "vertx_artist.export_palette"
    bl_label = "Export a Palette"
    bl_description = "Export selected Palette"
    bl_options = {"REGISTER", "UNDO"}
    filter_glob: bpy.props.StringProperty(default='*.ccb;*.colors;*.gpl', options={'HIDDEN'})
    filename_ext = '.ccb'
    palette_index: bpy.props.IntProperty(name='palette_index', options={'HIDDEN'}, min=0)
    file_extension: bpy.props.EnumProperty(
        name='file_extension', description='File extension',
        items=[
            ('ccb', 'ccb', ''),
            ('gpl', 'gpl', '')
        ],
        options={'HIDDEN'}
    )

    def check(self, context):
        dirname = os.path.dirname(self.filepath)

        self.filename_ext = f'.{self.file_extension}'
        self.filepath = os.path.join(dirname, bpy.context.scene.vrtxa_palettes[self.palette_index].name + self.filename_ext)

        return True

    def execute(self, context):        
        colors = bpy.context.scene.vrtxa_palettes[self.palette_index].palette_colors

        if self.file_extension == "ccb":
            with open(os.path.join(os.path.dirname(__file__), 'ccb_header.txt'), "r", encoding="utf8") as f:
                contents = f.readlines()

            with open(self.filepath, "w", encoding="utf16") as out:
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

            return {"FINISHED"}

        if self.file_extension == "gpl":
            with open(self.filepath, "w", encoding="utf8") as out:
                print("GIMP Palette", file=out)
                print("Name:", os.path.basename(self.filepath).split(".")[0], file=out)
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

            return {"FINISHED"}

        self.report({'ERROR'}, "Unknown file extension: " + self.file_extension)
        return {"CANCELLED"}


def move_palette_color(palette_index, palette_color_index, value):
    """Move palette color and set active index."""

    bpy.context.scene.vrtxa_palettes[palette_index].palette_colors.move(
        palette_color_index,
        max(0, min(
            palette_color_index + value,
            len(bpy.context.scene.vrtxa_palettes[palette_index].palette_colors) - 1)
        )
    )
    bpy.context.scene.vrtxa_palettes[palette_index].index = max(
        0, min(
            palette_color_index + value,
            len(bpy.context.scene.vrtxa_palettes[palette_index].palette_colors) - 1
        )
    )
    return


class VRTXA_OT_AddPaletteColor(bpy.types.Operator):
    bl_idname = "vertx_artist.add_palette_color"
    bl_label = "Add palette_color"
    bl_description = "Add single palette color into the palette"
    bl_options = {"REGISTER", "UNDO"}
    palette_index: bpy.props.IntProperty(
        name='palette_index',
        options={'HIDDEN'},
        min=0
    )
    palette_color_index: bpy.props.IntProperty(
        name='palette_color_index',
        options={'HIDDEN'},
        min=0
    )
    color_name: bpy.props.StringProperty(name='color_name')
    color: bpy.props.FloatVectorProperty(
        name='new_color',
        size=3, default=(0.0, 0.0, 0.0),
        subtype='COLOR',
        min=0.0, max=1.0
    )

    def execute(self, context):
        new_color = bpy.context.scene.vrtxa_palettes[self.palette_index].palette_colors.add()
        new_color.name = self.color_name
        new_color.color = self.color

        move_palette_color(
            self.palette_index,
            len(bpy.context.scene.vrtxa_palettes[self.palette_index].palette_colors) - 1,
            self.palette_color_index + 2 - len(bpy.context.scene.vrtxa_palettes[self.palette_index].palette_colors)
        )

        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class VRTXA_OT_RemovePalette(bpy.types.Operator):
    bl_idname = "vertx_artist.remove_palette"
    bl_label = "Remove Palette"
    bl_description = "Remove this palette"
    bl_options = {"REGISTER", "UNDO"}
    palette_index: bpy.props.IntProperty(
        name='palette_index',
        options={'HIDDEN'},
        min=0
    )

    def execute(self, context):
        if len(bpy.context.scene.vrtxa_palettes) > self.palette_index:
            bpy.context.scene.vrtxa_palettes.remove(self.palette_index)

        return {"FINISHED"}


class VRTXA_OT_RemovePaletteColor(bpy.types.Operator):
    bl_idname = "vertx_artist.remove_palette_color"
    bl_label = "Remove palette_color"
    bl_description = "Remove single palette color from the palette"
    bl_options = {"REGISTER", "UNDO"}
    palette_index: bpy.props.IntProperty(name='palette_index', options={'HIDDEN'}, min=0)
    palette_color_index: bpy.props.IntProperty(name='palette_color_index', options={'HIDDEN'}, min=0)

    def execute(self, context):
        if len(bpy.context.scene.vrtxa_palettes[self.palette_index].palette_colors) > self.palette_color_index:
            bpy.context.scene.vrtxa_palettes[self.palette_index].palette_colors.remove(self.palette_color_index)

        if bpy.context.scene.vrtxa_palettes[self.palette_index].index >= len(bpy.context.scene.vrtxa_palettes[self.palette_index].palette_colors):
            bpy.context.scene.vrtxa_palettes[self.palette_index].index = len(bpy.context.scene.vrtxa_palettes[self.palette_index].palette_colors) - 1

        return {"FINISHED"}


class VRTXA_OT_MovePalette(bpy.types.Operator):
    bl_idname = "vertx_artist.move_palette"
    bl_label = "Move palette Up"
    bl_description = "Move palette one step higher"
    bl_options = {"REGISTER", "UNDO"}
    palette_index: bpy.props.IntProperty(name='palette_index', options={'HIDDEN'}, min=0)
    direction: bpy.props.IntProperty(name='direction', options={'HIDDEN'})

    def execute(self, context):
        bpy.context.scene.vrtxa_palettes.move(self.palette_index, self.palette_index + self.direction)
        return {"FINISHED"}


class VRTXA_OT_MovePaletteColor(bpy.types.Operator):
    bl_idname = "vertx_artist.move_palette_color"
    bl_label = "Move palette_color Down"
    bl_description = "Move palette color one step lower"
    bl_options = {"REGISTER", "UNDO"}
    palette_index: bpy.props.IntProperty(name='palette_index', options={'HIDDEN'}, min=0)
    palette_color_index: bpy.props.IntProperty(name='palette_color_index', options={'HIDDEN'}, min=0)
    direction: bpy.props.IntProperty(name='direction', options={'HIDDEN'})

    def execute(self, context):
        move_palette_color(self.palette_index, self.palette_color_index, self.direction)
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class VRTXA_GROUP_PaletteColor(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name='name', description='Palette_color name',
        default='Color',
        update=on_palette_name_update
    )
    color: bpy.props.FloatVectorProperty(
        name='color', description='Palette_color color',
        size=3, default=(0.0, 0.0, 0.0),
        subtype='COLOR_GAMMA',
        min=0.0, max=1.0
    )


class VRTXA_GROUP_Palette(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name='name', description='Palette name')
    palette_colors: bpy.props.CollectionProperty(name='palette_colors', type=VRTXA_GROUP_PaletteColor)
    index: bpy.props.IntProperty(name='index', description='Palette index', min=0)


def register():
    bpy.utils.register_class(VRTXA_GROUP_PaletteColor)
    bpy.utils.register_class(VRTXA_GROUP_Palette)
    bpy.types.Scene.vrtxa_palettes = bpy.props.CollectionProperty(name='palettes', type=VRTXA_GROUP_Palette)

    bpy.utils.register_class(VRTXA_OT_CreatePalette)
    bpy.utils.register_class(VRTXA_OT_ImportPalette)
    bpy.utils.register_class(VRTXA_OT_ExportPalette)
    bpy.utils.register_class(VRTXA_OT_ExportPalettes)
    bpy.utils.register_class(VRTXA_OT_AddPaletteColor)
    bpy.utils.register_class(VRTXA_OT_RemovePalette)
    bpy.utils.register_class(VRTXA_OT_RemovePaletteColor)
    bpy.utils.register_class(VRTXA_OT_MovePalette)
    bpy.utils.register_class(VRTXA_OT_MovePaletteColor)


def unregister():
    del bpy.types.Scene.vrtxa_palettes
    bpy.utils.unregister_class(VRTXA_GROUP_PaletteColor)
    bpy.utils.unregister_class(VRTXA_GROUP_Palette)

    bpy.utils.unregister_class(VRTXA_OT_CreatePalette)
    bpy.utils.unregister_class(VRTXA_OT_ImportPalette)
    bpy.utils.unregister_class(VRTXA_OT_ExportPalette)
    bpy.utils.unregister_class(VRTXA_OT_ExportPalettes)
    bpy.utils.unregister_class(VRTXA_OT_AddPaletteColor)
    bpy.utils.unregister_class(VRTXA_OT_RemovePalette)
    bpy.utils.unregister_class(VRTXA_OT_RemovePaletteColor)
    bpy.utils.unregister_class(VRTXA_OT_MovePalette)
    bpy.utils.unregister_class(VRTXA_OT_MovePaletteColor)
