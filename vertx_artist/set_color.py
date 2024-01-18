import colorsys
import math

import bmesh
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

    # return r, g, b
    return inverse_gamma(rgb[0]), inverse_gamma(rgb[1]), inverse_gamma(rgb[2])


def gamma_correct_color(rgb):
    """Gamma correction."""

    # return r / 255, g / 255, b / 255
    return gamma_correct(rgb[0]), gamma_correct(rgb[1]), gamma_correct(rgb[2])


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


class VRTXA_OT_SetColor(bpy.types.Operator):
    bl_idname = "vertx_artist.set_color"
    bl_label = "Set Color"
    bl_description = "Apply color to active selection"
    bl_options = {"REGISTER", "UNDO"}

    color: bpy.props.FloatVectorProperty(
        name='color',
        description='Color to apply to selection',
        size=3,
        subtype='COLOR_GAMMA',
        min=0.0,
        max=1.0
    )
    use_static: bpy.props.BoolProperty(
        name='use_static',
        description='Apply static color instead of operator color',
        default=False,
        options={'HIDDEN'}
    )

    @classmethod
    def poll(cls, context):
        in_edit_mode = context.mode == 'EDIT_MESH'
        in_paint_mode = context.mode == 'PAINT_VERTEX'
        paint_select = bpy.context.object.data.use_paint_mask or bpy.context.object.data.use_paint_mask_vertex

        return in_edit_mode or (in_paint_mode and paint_select)

    def execute(self, context):
        obj = bpy.context.object
        color_attribute = obj.data.color_attributes.active_color

        if obj is None or color_attribute is None :
            self.report({'WARNING'}, message="Can't set color")
            return {"FINISHED"}

        if self.use_static:
            color = bpy.context.scene.vrtxa_static_color
        else:
            color = self.color

        channels = obj.vrtxa_layers[obj.data.color_attributes.active_color_index].channels

        # VERTEX PAINT MODE
        if bpy.context.mode == "PAINT_VERTEX":
            try:
                vert_mode = obj.data.use_paint_mask_vertex
                poly_mode = obj.data.use_paint_mask
            except AttributeError:
                return {"FINISHED"}

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

            return {"FINISHED"}

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

        if bpy.context.scene.vrtxa_show_object_colors and bpy.context.mode == 'EDIT_MESH':
            bpy.ops.vertx_artist.refresh('INVOKE_DEFAULT')

        return {"FINISHED"}


def register():
    bpy.types.Scene.vrtxa_static_color = bpy.props.FloatVectorProperty(
        name='static_color',
        description='Color to apply to selection',
        size=3,
        subtype='COLOR_GAMMA',
        min=0.0, max=1.0
    )
    bpy.utils.register_class(VRTXA_OT_SetColor)


def unregister():
    del bpy.types.Scene.vrtxa_static_color
    bpy.utils.unregister_class(VRTXA_OT_SetColor)
