'''
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import bpy

from . import (
    eyedropper,
    layers,
    object_colors,
    palettes,
    preferences,
    tool_panel,
    transformations
)


bl_info = {
    "name": "VertX Artist",
    "author": "Mahrkeenerh",
    "doc_url": "https://github.com/Mahrkeenerh/VertXArtist",
    "description": "Vertex coloring tool using Color Attributes",
    "blender": (3, 4, 0),
    "version": (3, 5, 2),
    "location": "Edit Mode",
    "category": "Paint",
}


def register():
    eyedropper.register()
    layers.register()
    object_colors.register()
    palettes.register()
    preferences.register()
    tool_panel.register()
    transformations.register()


def unregister():
    eyedropper.unregister()
    layers.unregister()
    object_colors.unregister()
    palettes.unregister()
    preferences.unregister()
    tool_panel.unregister()
    transformations.unregister()
