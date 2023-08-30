import subprocess
import sys
import gpu


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
