import bpy


keymaps = {}


class VRTXA_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = 'vertx_artist'

    color_grid_columns: bpy.props.IntProperty(
        name='color_grid_columns',
        description='Number of columns to use for grid color display',
        default=1, min=1, max=100
    )
    object_color_columns: bpy.props.IntProperty(
        name='object_color_columns',
        description='Number of columns to use for grid object color display',
        default=4, min=2, max=100
    )
    palette_grid_columns: bpy.props.IntProperty(
        name='palette_grid_columns',
        description='Number of columns to use for palette grid display',
        default=1, min=1, max=100
    )
    selection_tolerance: bpy.props.FloatProperty(
        name='selection_tolerance',
        description='How much can a vertex/face have other colors.',
        default=0.0, min=0.0, max=1.0
    )
    hide_edit_warning: bpy.props.BoolProperty(
        name='hide_edit_warning',
        description='Hide warning about editing layer channels',
        default=False
    )
    hide_refresh_stack_warning: bpy.props.BoolProperty(
        name='hide_refresh_stack_warning',
        description='Hide warning about refreshing color transformatin stack',
        default=False
    )


    override_selection_color: bpy.props.EnumProperty(
        name='override_selection_color',
        items=[('None', 'None', '', 0, 0), ('White Override', 'White Override', '', 0, 1), ('Full Override', 'Full Override', '', 0, 2)]
    )
    selection_color: bpy.props.FloatVectorProperty(
        name='selection_color',
        description='',
        size=4,
        subtype='COLOR_GAMMA',
        min=0.0, max=1.0,
        default=(0.9058823585510254, 0.6078431606292725, 0.250980406999588, 0.5)
    )

    def draw(self, context):
        layout = self.layout 
        layout.prop(keymaps['set_color'][1], 'type', text='Set Color', full_event=True)
        layout.prop(keymaps['pie_menu'][1], 'type', text='Color Eyedropper', full_event=True)
        layout.prop(keymaps['eyedropper'][1], 'type', text='Quick Access Menu', full_event=True)


def create_keymaps():
    kc = bpy.context.window_manager.keyconfigs.addon

    km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
    kmi = km.keymap_items.new(
        'vertx_artist.eyedropper', 'S', 'PRESS',
        ctrl=False, alt=True, shift=True,
        repeat=False
    )
    keymaps['eyedropper'] = (km, kmi)

    km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
    kmi = km.keymap_items.new(
        'wm.call_menu_pie', 'V', 'PRESS',
        ctrl=False, alt=False, shift=False,
        repeat=False
    )
    kmi.properties.name = 'VIEW3D_MT_vertx_artist_pie'
    keymaps['pie_menu'] = (km, kmi)

    km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
    kmi = km.keymap_items.new(
        'vertx_artist.set_color', 'K', 'PRESS',
        ctrl=False, alt=True, shift=True,
        repeat=False
    )
    keymaps['set_color'] = (km, kmi)


def remove_keymaps():
    for km, kmi in keymaps.values():
        km.keymap_items.remove(kmi)
    keymaps.clear()


def register():
    create_keymaps()

    bpy.utils.register_class(VRTXA_AddonPreferences)


def unregister():
    remove_keymaps()

    bpy.utils.unregister_class(VRTXA_AddonPreferences)
