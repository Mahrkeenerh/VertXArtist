import mathutils
import operator
import os
import subprocess
import sys

import blf
import bpy
import gpu
import gpu_extras




handler_BCC2E = []
last_hex_color = ''


def get_color(event):
    """Get color from mouse position"""

    global last_hex_color

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
    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    batch = gpu_extras.batch.batch_for_shader(shader, 'TRIS', {"pos": quad}, indices=indices)
    shader.bind()
    shader.uniform_float("color", color)
    gpu.state.blend_set('ALPHA')
    batch.draw(shader)


def draw_eyedropper(mouse_position, color_rgb, color_hex):
    base_position = vector_math(mouse_position, (30, -1), operator.add)

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

    draw_quad((bottom_left, bottom_right, top_left, top_right), (*color_rgb, 1.0))

    # Draw hex
    offset = (30, 3)
    font_id = 0

    x = base_position[0] + offset[0]
    y = base_position[1] + offset[1]

    blf.position(font_id, x, y, 0)
    blf.size(font_id, 20.0)
    blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
    blf.enable(font_id, blf.WORD_WRAP)
    blf.draw(font_id, '#' + color_hex)
    blf.disable(font_id, blf.ROTATION)
    blf.disable(font_id, blf.WORD_WRAP)


handler = None
eyedropper_running = False

class VRTXA_OT_Eyedropper(bpy.types.Operator):
    bl_idname = "vertx_artist.eyedropper"
    bl_label = "VertX Eyedropper"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}
    cursor = "EYEDROPPER"

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def some_func(self, context, event):
        global handler

        color_rgb, color_hex = get_color(event=event)

        if event.value == 'RELEASE':
            if event.type in ['RIGHTMOUSE', 'ESC']:
                self.execute(context)
                return {'CANCELLED'}

            self.execute(context)
            return {"FINISHED"}
        else:
            if handler:
                bpy.types.SpaceView3D.draw_handler_remove(handler, 'WINDOW')
                handler = None
                for a in bpy.context.screen.areas:
                    a.tag_redraw()

            handler = bpy.types.SpaceView3D.draw_handler_add(
                draw_eyedropper,
                ((event.mouse_region_x, event.mouse_region_y), color_rgb, color_hex),
                'WINDOW', 'POST_PIXEL'
            )
            for a in bpy.context.screen.areas:
                a.tag_redraw()

        bpy.context.scene.vrtxa_static_color = color_rgb

    def execute(self, context):
        global eyedropper_running, handler

        eyedropper_running = False
        context.window.cursor_set("DEFAULT")

        if handler:
            bpy.types.SpaceView3D.draw_handler_remove(handler, 'WINDOW')
            handler = None
            for a in bpy.context.screen.areas:
                a.tag_redraw()

        set_clipboard()

        for area in context.screen.areas:
            area.tag_redraw()

        return {"FINISHED"}

    def modal(self, context, event):
        if not context.area or not eyedropper_running:
            self.execute(context)
            return {'CANCELLED'}

        context.window.cursor_set('EYEDROPPER')
        self.some_func(context, event)

        if event.type in ['RIGHTMOUSE', 'ESC']:
            self.execute(context)
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        global eyedropper_running

        if eyedropper_running:
            eyedropper_running = False
            return {'FINISHED'}

        else:
            self.start_pos = (event.mouse_x, event.mouse_y)
            context.window.cursor_set('EYEDROPPER')
            self.some_func(context, event)
            context.window_manager.modal_handler_add(self)
            eyedropper_running = True
            return {'RUNNING_MODAL'}


def register():
    bpy.utils.register_class(VRTXA_OT_Eyedropper)


def unregister():
    bpy.utils.unregister_class(VRTXA_OT_Eyedropper)
