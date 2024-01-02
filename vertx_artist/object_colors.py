import colorsys

import bpy
import bmesh

from .set_color import set_restricted_color


ignore_color_change = False

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



def object_color_update(self, context):
    """Update color of everything with same color."""

    if not ignore_color_change:
        color_idx = self.index
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
                        bpy.context.view_layer.objects.active.vrtxa_layers[bpy.context.object.data.color_attributes.active_color_index].channels
                    )

            bmesh.update_edit_mesh(obj.data)


class VRTXA_GROUP_ObjectColor(bpy.types.PropertyGroup):
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

        # TODO FIX CORNER LOOKUP
        # FIX SORTING
        import time

        cur = time.time()

        out_colors = [x for x in colors.keys()]
        out_colors.sort(key=lambda rgb: colorsys.rgb_to_hsv(*rgb))
        # sorted_colors = sorter.sort(out_colors)
        active_color_index = 0

        end_time = time.time()

        print("Time: " + str(end_time - cur))
        # active_color_index = max(colors.values(), key=lambda x: x[1])[0] if len(colors) > 0 else None
        # out_colors = [x for x in colors.keys()]

        # return active_color_index, out_colors

        if active_color_index is None:
            return {"FINISHED"}


        ignore_color_change = True

        # TODO change to remove all items and then add new ones when faster
        while len(bpy.context.scene.vrtxa_object_colors) > len(out_colors):
            if len(bpy.context.scene.vrtxa_object_colors) > len(bpy.context.scene.vrtxa_object_colors) - 1:
                bpy.context.scene.vrtxa_object_colors.remove(len(bpy.context.scene.vrtxa_object_colors) - 1)

        while len(bpy.context.scene.vrtxa_object_colors) < len(out_colors):
            new_color = bpy.context.scene.vrtxa_object_colors.add()
            new_color.index = len(bpy.context.scene.vrtxa_object_colors) - 1

        bpy.context.scene.vrtxa_active_color_index = active_color_index
        for i, color in enumerate(out_colors):
            bpy.context.scene.vrtxa_object_colors[i].color = color

        ignore_color_change = False

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
        # ignore_hsv=(self.sna_ignore_hue, self.sna_ignore_saturation, self.sna_ignore_value)

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
            for obj_name in color_corner_lookup[self.select_color_idx]:
                obj = obj_name_map[obj_name]
                bm = bmesh.from_edit_mesh(obj.data)

                bm.verts.ensure_lookup_table()
                for vert_idx in color_corner_lookup[self.select_color_idx][obj_name]:
                    if len(color_corner_lookup[self.select_color_idx][obj_name][vert_idx]) / len(bm.verts[vert_idx].link_loops) >= (1 - self.selection_tolerance):
                        bm.verts[vert_idx].select = True

                # edge mode
                if bpy.context.tool_settings.mesh_select_mode[1]:
                    for edge in bm.edges:
                        if edge.verts[0].select and edge.verts[1].select:
                            edge.select = True

                bmesh.update_edit_mesh(obj.data)

        # face mode
        if bpy.context.tool_settings.mesh_select_mode[2]:
            for obj_name in color_corner_lookup[self.select_color_idx]:
                obj = obj_name_map[obj_name]
                bm = bmesh.from_edit_mesh(obj.data)

                bm.faces.ensure_lookup_table()
                for face in bm.faces:
                    loops_in_face = [x for x in face.loops if x.vert.index in color_corner_lookup[self.select_color_idx][obj_name]]
                    if len(loops_in_face) / len(face.loops) >= (1 - self.selection_tolerance):
                        face.select = True

                bmesh.update_edit_mesh(obj.data)


        return {"FINISHED"}


def register():
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
    bpy.utils.unregister_class(VRTXA_GROUP_ObjectColor)
    del bpy.types.Scene.vrtxa_object_colors
    del bpy.types.Scene.vrtxa_object_colors_index
    del bpy.types.Scene.vrtxa_show_object_colors

    bpy.utils.unregister_class(VRTXA_OT_ShowhideObjectColors)
    bpy.utils.unregister_class(VRTXA_OT_Checkpoint)
    bpy.utils.unregister_class(VRTXA_OT_Refresh)
    bpy.utils.unregister_class(VRTXA_OT_SelectByColor)
