import bpy

bl_info = {
    "name": "VertX Artist - Batch Color Init Extension",
    "author": "Mahrkeenerh",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "Properties > Data Properties > Color Layers",
    "description": "Initialize color attributes on multiple selected objects (requires VertX Artist addon)",
    "category": "Mesh",
}


class BATCH_COLOR_INIT_OT_init_colors(bpy.types.Operator):
    """Initialize color attributes on multiple selected objects"""
    bl_idname = "batch_color_init.init_colors"
    bl_label = "Batch Color Init"
    bl_description = "Add color attribute to selected objects that don't have one and set initial color"
    bl_options = {"REGISTER", "UNDO"}

    init_color: bpy.props.FloatVectorProperty(
        name="Initial Color",
        description="Color to apply to newly created color attributes",
        size=3,
        subtype='COLOR_GAMMA',
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0)
    )

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and len(context.selected_objects) > 0

    def invoke(self, context, event):
        # Show popup dialog
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "init_color", text="Initial Color")

    def execute(self, context):
        # Store the original active object
        original_active = context.view_layer.objects.active
        processed_count = 0
        skipped_count = 0

        # Get all selected mesh objects at the start - don't rely on context during iteration
        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not selected_meshes:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}

        for obj in selected_meshes:
            print(f"Processing {obj.name}")

            # Check if object already has color attributes (check the data directly)
            if len(obj.data.color_attributes) > 0:
                print(f"  Skipping {obj.name} - already has color attributes")
                skipped_count += 1
                continue
                
            print(f"  Creating color attribute for {obj.name}")
            
            # Create color attribute directly
            color_attribute = obj.data.color_attributes.new(
                name='Color',
                type='BYTE_COLOR',
                domain='CORNER'
            )
            
            # Set the initial color for all corners
            color_with_alpha = (self.init_color[0], self.init_color[1], self.init_color[2], 1.0)
            for i in range(len(color_attribute.data)):
                color_attribute.data[i].color = color_with_alpha
            
            # Set active color index if it's not valid
            num_color_attrs = len(obj.data.color_attributes)
            current_index = obj.data.color_attributes.active_color_index
            
            if not isinstance(current_index, int) or current_index < 0 or current_index >= num_color_attrs:
                # Set to the last index (our newly created attribute)
                obj.data.color_attributes.active_color_index = num_color_attrs - 1
                print(f"  Set active color index to {num_color_attrs - 1} for {obj.name}")
            
            processed_count += 1

        # Restore original active object
        context.view_layer.objects.active = original_active

        # Report results
        info_message = ""
        if processed_count > 0:
            info_message += f"Color attributes created on {processed_count} objects\n"
        if skipped_count > 0:
            info_message += f"Skipped {skipped_count} objects (already have color attributes)"

        self.report({'INFO'}, info_message)

        return {'FINISHED'}


def draw_batch_init_ui(self, context):
    """Function to add batch init UI to existing VertX Artist panel"""
    layout = self.layout
        
    # Simple operator button with icon
    layout.operator("batch_color_init.init_colors", text="Initialize Selected Objects", icon='COLOR')


def register():
    bpy.utils.register_class(BATCH_COLOR_INIT_OT_init_colors)
    
    # Try to append to VertX Artist panel if it exists
    try:
        from vertx_artist.layers import VRTXA_PT_ColorLayers
        # Add our UI to the beginning of the VertX Artist panel
        VRTXA_PT_ColorLayers.prepend(draw_batch_init_ui)
        print("Batch Color Init: Successfully integrated with VertX Artist")
    except ImportError:
        print("VertX Artist not found - Batch Color Init requires VertX Artist addon to function properly")


def unregister():
    bpy.utils.unregister_class(BATCH_COLOR_INIT_OT_init_colors)
    
    # Remove from VertX Artist panel if it was added
    try:
        from vertx_artist.layers import VRTXA_PT_ColorLayers
        VRTXA_PT_ColorLayers.remove(draw_batch_init_ui)
    except (ImportError, ValueError):
        pass


if __name__ == "__main__":
    register()
