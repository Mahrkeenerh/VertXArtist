import operator
import subprocess
import sys

import blf
import bmesh
import bpy
from bpy_extras import view3d_utils
import gpu
import gpu_extras

from .object_colors import gamma_correct_color


last_hex_color = ''


def get_color(context, event):
    """Get color from mouse position.
    First, try to raycast to get the color from the color attribute of the object,
    if it fails, get the color from the screen buffer.
    """

    global last_hex_color

    # Raycast
    region = context.region
    rv3d = context.region_data
    mouse_coord = event.mouse_region_x, event.mouse_region_y

    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, mouse_coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, mouse_coord)

    depsgraph = context.evaluated_depsgraph_get()
    result, location, normal, index, obj, matrix = context.scene.ray_cast(depsgraph, ray_origin, view_vector)
    color_rgb = None

    # Raycast color
    if result:
        # Edit mode
        if context.mode == 'EDIT_MESH':
            bm = bmesh.from_edit_mesh(obj.data)
            active_layer = bm.loops.layers.color.active

            corner_colors = [list(corner[active_layer]) for corner in bm.faces[index].loops]

        # Object or vertex paint mode
        else:
            color_attribute = obj.data.color_attributes.active_color
            corner_colors = [list(color_attribute.data[i].color) for i in obj.data.polygons[index].loop_indices]

        # If all colors are the same, use that color
        if all(corner_colors[0] == corner_colors[i] for i in range(1, len(corner_colors))):
            color_rgb = corner_colors[0][:3]

        if context.mode != 'EDIT_MESH' and color_rgb is not None:
            color_rgb = gamma_correct_color(color_rgb)

    # Pixel color
    if not result or color_rgb is None:
        fb = gpu.state.active_framebuffer_get()
        screen_buffer = fb.read_color(event.mouse_x, event.mouse_y, 1, 1, 3, 0, 'FLOAT')
        color_rgb = screen_buffer.to_list()[0][0]

    color_hex = '%02x%02x%02x'.upper() % (round(color_rgb[0]*255), round(color_rgb[1]*255), round(color_rgb[2]*255))
    last_hex_color = color_hex

    return color_rgb, color_hex


def set_clipboard():
    """Copy color to clipboard"""

    if sys.platform == 'darwin':
        cmd = f'echo {last_hex_color}|pbcopy'
    elif sys.platform == 'win32':
        cmd = f'echo {last_hex_color}|clip'
    else:
        print(f'Sorry, "{sys.platform}" is not currently supported, report it, and I will add it.')
        return

    return subprocess.check_call(cmd, shell=True)


def vector_math(v1, v2, operation):
    out = []

    for i in range(len(v1)):
        out.append(operation(v1[i], v2[i]))

    return tuple(out)


def draw_quad(quad, color):
    """Draw a quad on screen"""

    indices = ((0, 1, 2), (2, 1, 3))
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    batch = gpu_extras.batch.batch_for_shader(shader, 'TRIS', {"pos": quad}, indices=indices)
    shader.bind()
    shader.uniform_float("color", color)
    gpu.state.blend_set('ALPHA')
    batch.draw(shader)


eyedropper_running = False

class VRTXA_OT_Eyedropper(bpy.types.Operator):
    bl_idname = "vertx_artist.eyedropper"
    bl_label = "VertX Eyedropper"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}
    cursor = "EYEDROPPER"

    handle = None

    mouse_position = ()
    color_rgb = (1.0, 1.0, 1.0)
    color_hex = 'FFFFFF'

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D' or context.area.type == 'EDIT_MESH' or context.area.type == 'PAINT_VERTEX'

    def draw_eyedropper(self):
        base_position = vector_math(self.mouse_position, (30, -1), operator.add)

        # Draw background
        bg_offset = (-5, -5)
        height = 30
        width = 135

        bottom_left = vector_math(base_position, bg_offset, operator.add)
        bottom_right = vector_math(bottom_left, (width, 0), operator.add)
        top_left = vector_math(bottom_left, (0, height), operator.add)
        top_right = vector_math(bottom_left, (width, height), operator.add)

        draw_quad((bottom_left, bottom_right, top_left, top_right), (0.18397267162799835, 0.18397267162799835, 0.18397286534309387, 1.0))

        # Draw color
        size = 20

        bottom_left = base_position
        bottom_right = vector_math(bottom_left, (size, 0), operator.add)
        top_left = vector_math(bottom_left, (0, size), operator.add)
        top_right = vector_math(bottom_left, (size, size), operator.add)

        draw_quad((bottom_left, bottom_right, top_left, top_right), (*self.color_rgb, 1.0))

        # Draw hex
        offset = (30, 3)
        font_id = 0

        x = base_position[0] + offset[0]
        y = base_position[1] + offset[1]

        blf.position(font_id, x, y, 0)
        blf.size(font_id, 20.0)
        blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
        blf.enable(font_id, blf.WORD_WRAP)
        blf.draw(font_id, '#' + self.color_hex)
        blf.disable(font_id, blf.ROTATION)
        blf.disable(font_id, blf.WORD_WRAP)

    def execute(self, context):
        global eyedropper_running

        eyedropper_running = False
        context.window.cursor_set("DEFAULT")

        bpy.types.SpaceView3D.draw_handler_remove(self.handle, 'WINDOW')
        self.handle = None
        for a in bpy.context.screen.areas:
            a.tag_redraw()

        set_clipboard()

        return {"FINISHED"}

    def modal(self, context, event):
        self.mouse_position = (event.mouse_region_x, event.mouse_region_y)

        if not context.area or not eyedropper_running:
            self.execute(context)
            return {'CANCELLED'}

        context.area.tag_redraw()
        context.window.cursor_set('EYEDROPPER')
        
        self.color_rgb, self.color_hex = get_color(context, event)

        if event.value == 'RELEASE':
            if event.type in ['RIGHTMOUSE', 'ESC']:
                self.execute(context)
                return {'CANCELLED'}

            self.execute(context)
            return {"FINISHED"}

        bpy.context.scene.vrtxa_static_color = self.color_rgb

        # select object colors with same color
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            bpy.ops.vertx_artist.select_by_color(
                'INVOKE_DEFAULT',
                selection_tolerance=bpy.context.preferences.addons['vertx_artist'].preferences.selection_tolerance,
                select_color=bpy.context.scene.vrtxa_static_color,
                select_color_idx=-1,
                ignore_hue=False, ignore_saturation=False, ignore_value=False,
            )

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        global eyedropper_running

        if eyedropper_running:
            eyedropper_running = False
            return {'FINISHED'}

        else:
            self.start_pos = (event.mouse_x, event.mouse_y)
            context.window.cursor_set('EYEDROPPER')
            self.handle = bpy.types.SpaceView3D.draw_handler_add(
                self.draw_eyedropper, (),
                'WINDOW', 'POST_PIXEL'
            )
            context.window_manager.modal_handler_add(self)
            eyedropper_running = True
            return {'RUNNING_MODAL'}


def register():
    bpy.utils.register_class(VRTXA_OT_Eyedropper)


def unregister():
    bpy.utils.unregister_class(VRTXA_OT_Eyedropper)
