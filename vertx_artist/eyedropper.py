import mathutils
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




def sna_draw_eyedropper_display_function_046A8(mouse_position, color_rgb, color_hex):
    quads = [[tuple((int(tuple(map(lambda v: int(v), tuple(mathutils.Vector(tuple(mathutils.Vector(mouse_position) + mathutils.Vector((30.0, -1.0)))) + mathutils.Vector((-5.0, -5.0)))))[0]), int(tuple(map(lambda v: int(v), tuple(mathutils.Vector(tuple(mathutils.Vector(mouse_position) + mathutils.Vector((30.0, -1.0)))) + mathutils.Vector((-5.0, -5.0)))))[1]))), tuple((int(int(tuple(map(lambda v: int(v), tuple(mathutils.Vector(tuple(mathutils.Vector(mouse_position) + mathutils.Vector((30.0, -1.0)))) + mathutils.Vector((-5.0, -5.0)))))[0]) + 135), int(tuple(map(lambda v: int(v), tuple(mathutils.Vector(tuple(mathutils.Vector(mouse_position) + mathutils.Vector((30.0, -1.0)))) + mathutils.Vector((-5.0, -5.0)))))[1]))), tuple((int(tuple(map(lambda v: int(v), tuple(mathutils.Vector(tuple(mathutils.Vector(mouse_position) + mathutils.Vector((30.0, -1.0)))) + mathutils.Vector((-5.0, -5.0)))))[0]), int(int(tuple(map(lambda v: int(v), tuple(mathutils.Vector(tuple(mathutils.Vector(mouse_position) + mathutils.Vector((30.0, -1.0)))) + mathutils.Vector((-5.0, -5.0)))))[1]) + 30))), tuple((int(int(tuple(map(lambda v: int(v), tuple(mathutils.Vector(tuple(mathutils.Vector(mouse_position) + mathutils.Vector((30.0, -1.0)))) + mathutils.Vector((-5.0, -5.0)))))[0]) + 135), int(int(tuple(map(lambda v: int(v), tuple(mathutils.Vector(tuple(mathutils.Vector(mouse_position) + mathutils.Vector((30.0, -1.0)))) + mathutils.Vector((-5.0, -5.0)))))[1]) + 30)))]]
    vertices = []
    indices = []
    for i_727C8, quad in enumerate(quads):
        vertices.extend(quad)
        indices.extend([(i_727C8 * 4, i_727C8 * 4 + 1, i_727C8 * 4 + 2), (i_727C8 * 4 + 2, i_727C8 * 4 + 1, i_727C8 * 4 + 3)])
    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    batch = gpu_extras.batch.batch_for_shader(shader, 'TRIS', {"pos": tuple(vertices)}, indices=tuple(indices))
    shader.bind()
    shader.uniform_float("color", (0.18397267162799835, 0.18397267162799835, 0.18397286534309387, 1.0))
    gpu.state.blend_set('ALPHA')
    batch.draw(shader)
    quads = [[tuple((int(tuple(map(lambda v: int(v), tuple(mathutils.Vector(mouse_position) + mathutils.Vector((30.0, -1.0)))))[0]), int(tuple(map(lambda v: int(v), tuple(mathutils.Vector(mouse_position) + mathutils.Vector((30.0, -1.0)))))[1]))), tuple((int(int(tuple(map(lambda v: int(v), tuple(mathutils.Vector(mouse_position) + mathutils.Vector((30.0, -1.0)))))[0]) + 20), int(tuple(map(lambda v: int(v), tuple(mathutils.Vector(mouse_position) + mathutils.Vector((30.0, -1.0)))))[1]))), tuple((int(tuple(map(lambda v: int(v), tuple(mathutils.Vector(mouse_position) + mathutils.Vector((30.0, -1.0)))))[0]), int(int(tuple(map(lambda v: int(v), tuple(mathutils.Vector(mouse_position) + mathutils.Vector((30.0, -1.0)))))[1]) + 20))), tuple((int(int(tuple(map(lambda v: int(v), tuple(mathutils.Vector(mouse_position) + mathutils.Vector((30.0, -1.0)))))[0]) + 20), int(int(tuple(map(lambda v: int(v), tuple(mathutils.Vector(mouse_position) + mathutils.Vector((30.0, -1.0)))))[1]) + 20)))]]
    vertices = []
    indices = []
    for i_83E95, quad in enumerate(quads):
        vertices.extend(quad)
        indices.extend([(i_83E95 * 4, i_83E95 * 4 + 1, i_83E95 * 4 + 2), (i_83E95 * 4 + 2, i_83E95 * 4 + 1, i_83E95 * 4 + 3)])
    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    batch = gpu_extras.batch.batch_for_shader(shader, 'TRIS', {"pos": tuple(vertices)}, indices=tuple(indices))
    shader.bind()
    shader.uniform_float("color", eval("(*color_rgb, 1.0)"))
    gpu.state.blend_set('ALPHA')
    batch.draw(shader)
    font_id = 0
    if r'' and os.path.exists(r''):
        font_id = blf.load(r'')
    if font_id == -1:
        print("Couldn't load font!")
    else:
        x_AE6C4, y_AE6C4 = tuple(mathutils.Vector(tuple(mathutils.Vector(mouse_position) + mathutils.Vector((30.0, -1.0)))) + mathutils.Vector((30.0, 3.0)))
        blf.position(font_id, x_AE6C4, y_AE6C4, 0)
        if bpy.app.version >= (3, 4, 0):
            blf.size(font_id, 20.0)
        else:
            blf.size(font_id, 20.0, 72)
        clr = (1.0, 1.0, 1.0, 1.0)
        blf.color(font_id, clr[0], clr[1], clr[2], clr[3])
        if 0:
            blf.enable(font_id, blf.WORD_WRAP)
            blf.word_wrap(font_id, 0)
        if 0.0:
            blf.enable(font_id, blf.ROTATION)
            blf.rotation(font_id, 0.0)
        blf.enable(font_id, blf.WORD_WRAP)
        blf.draw(font_id, '#' + color_hex)
        blf.disable(font_id, blf.ROTATION)
        blf.disable(font_id, blf.WORD_WRAP)





_FE493_running = False
class VRTXA_OT_Eyedropper(bpy.types.Operator):
    bl_idname = "vertx_artist.eyedropper"
    bl_label = "VertX Eyedropper"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}
    cursor = "EYEDROPPER"
    _handle = None
    _event = {}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        if not False or context.area.spaces[0].bl_rna.identifier == 'SpaceNodeEditor':
            return not False
        return False

    def save_event(self, event):
        event_options = ["type", "value", "alt", "shift", "ctrl", "oskey", "mouse_region_x", "mouse_region_y", "mouse_x", "mouse_y", "pressure", "tilt"]
        if bpy.app.version >= (3, 2, 1):
            event_options += ["type_prev", "value_prev"]
        for option in event_options: self._event[option] = getattr(event, option)

    def draw_callback_px(self, context):
        event = self._event
        if event.keys():
            event = dotdict(event)
            try:
                pass
            except Exception as error:
                print(error)

    def execute(self, context):
        global _FE493_running
        _FE493_running = False
        context.window.cursor_set("DEFAULT")
        if handler_BCC2E:
            bpy.types.SpaceView3D.draw_handler_remove(handler_BCC2E[0], 'WINDOW')
            handler_BCC2E.pop(0)
            for a in bpy.context.screen.areas: a.tag_redraw()
        return_D7176 = set_clipboard()
        for area in context.screen.areas:
            area.tag_redraw()
        return {"FINISHED"}

    def modal(self, context, event):
        global _FE493_running
        if not context.area or not _FE493_running:
            self.execute(context)
            return {'CANCELLED'}
        self.save_event(event)
        context.window.cursor_set('EYEDROPPER')
        try:
            return_41CCC = get_color(event=eval("event"))
            if (event.value == 'RELEASE'):
                if event.type in ['RIGHTMOUSE', 'ESC']:
                    self.execute(context)
                    return {'CANCELLED'}
                self.execute(context)
                return {"FINISHED"}
            else:
                if handler_BCC2E:
                    bpy.types.SpaceView3D.draw_handler_remove(handler_BCC2E[0], 'WINDOW')
                    handler_BCC2E.pop(0)
                    for a in bpy.context.screen.areas: a.tag_redraw()
                handler_BCC2E.append(bpy.types.SpaceView3D.draw_handler_add(sna_draw_eyedropper_display_function_046A8, ((event.mouse_region_x, event.mouse_region_y), return_41CCC[0], return_41CCC[1], ), 'WINDOW', 'POST_PIXEL'))
                for a in bpy.context.screen.areas: a.tag_redraw()
            bpy.context.scene.vrtxa_static_color = return_41CCC[0]
        except Exception as error:
            print(error)
        if event.type in ['RIGHTMOUSE', 'ESC']:
            self.execute(context)
            return {'CANCELLED'}
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        global _FE493_running
        if _FE493_running:
            _FE493_running = False
            return {'FINISHED'}
        else:
            self.save_event(event)
            self.start_pos = (event.mouse_x, event.mouse_y)
            context.window.cursor_set('EYEDROPPER')
            return_41CCC = get_color(event=eval("event"))
            if (event.value == 'RELEASE'):
                if event.type in ['RIGHTMOUSE', 'ESC']:
                    self.execute(context)
                    return {'CANCELLED'}
                self.execute(context)
                return {"FINISHED"}
            else:
                if handler_BCC2E:
                    bpy.types.SpaceView3D.draw_handler_remove(handler_BCC2E[0], 'WINDOW')
                    handler_BCC2E.pop(0)
                    for a in bpy.context.screen.areas: a.tag_redraw()
                handler_BCC2E.append(bpy.types.SpaceView3D.draw_handler_add(sna_draw_eyedropper_display_function_046A8, ((event.mouse_region_x, event.mouse_region_y), return_41CCC[0], return_41CCC[1], ), 'WINDOW', 'POST_PIXEL'))
                for a in bpy.context.screen.areas: a.tag_redraw()
            bpy.context.scene.vrtxa_static_color = return_41CCC[0]
            context.window_manager.modal_handler_add(self)
            _FE493_running = True
            return {'RUNNING_MODAL'}



def register():
    bpy.utils.register_class(VRTXA_OT_Eyedropper)


def unregister():
    bpy.utils.unregister_class(VRTXA_OT_Eyedropper)
