![Blender](https://img.shields.io/badge/blender%203.2%20+-%23F5792A.svg?style=for-the-badge&logo=blender&logoColor=white) ![Serpens 3](https://img.shields.io/badge/SERPENS%203-00eda9?style=for-the-badge&logo=blender&logoColor=white)



# VertX Artist

All-in-one Blender Vertex Painting tools. Adds support for External Palettes and Color Layer System, utilizing individual channels, even the Alpha channel.

| [Blender Market](https://blendermarket.com/products/vertx-artist-vertex-painting-tools) | [Download](https://github.com/Mahrkeenerh/VertXArtist/releases/latest/download/vertx_artist.zip) |
| - | - |



# NOW IN EDIT MODE

Most of the functionality has been moved to Edit mode, as it offers more flexibility and control.



# Easily Fine-Tune Object Colors

(The active color is no longer updated automatically, you need to press Refresh. This decision was made, as the operation is computationally expensive, and it was causing performance issues.)

![Adjust Object Colors](/docu/adjust_object_colors.gif)


# Utilize Color Layers

Now supporting Blender gamma corrections.

![Layers](/docu/layers.gif)

![Gamma layer correction](/docu/gamma.png)

- `Gamma correction` - Blender gamma color transformation, from `Raw` to `Standard`
- `Inverse correction` - Inverse correction, from `Standard` to `Raw`



# Preview and Apply Color Transformations

Custom Color Transformations are applied based on the Stack, not the material itself.

The material only provides a visual preview.

![Color Transformations](/docu/color_transformations.gif)




# Set Object Colors and Create Gradients

![Set Object Colors](/docu/set_colors.gif)



# Quickly Select All By Color

![Select All By Color](/docu/select_by_color.gif)



# Create Custom Palettes

![Custom Palettes](/docu/custom_palettes.gif)



# Customize Layout

![Customize Layout](/docu/customize_layout.gif)



# Alpha Gradients

They work for multiple objects, both in `Object` and `Edit` mode.

![Alpha Gradients](/docu/alpha_gradients.gif)



# Quick Access Pie Menu

To enable Quick Access Pie Menu, you need to disable the default Blender shortcut for the same key, in the Vertex Paint window.

![Shortcut Addon](/docu/shortcut_addon.png)

![Shorctut Default](/docu/shortcut_default.png)



# Checkpoint

Only adjusting object colors doesn't generate undo-steps. That's why `Checkpoint` operator is introduced. Pressing this button generates a save-state you can later return to. Making it possible to save object at different stages of coloring.

- Adjust object color
- `Checkpoint`
- Now you are able to undo before and after the change

If you didn't save after adjusting the object color, Blender will undo the last action performed (face selection, enter `Vertex Paint` mode ...)

![Checkpoint](/docu/checkpoint.png)



# Layer Channels Override

If you remove the addon completely, or you just didn't have it installed yet, the layers might have broken channels, and all display `RGBA`. If you need to edit it at any point, you can use the `Layer Editing Toggle`.

**`Warning`**: changing channels may result in unwanted behavior, because RGB channel holds no information about the alpha channel.

![Toggle Layer Editing](/docu/layer_override.png)



# Eyedropper

Added new Eyedropper functionality. You can sample any color on your screen (within Blender). It will also be copied to your clipboard (Windows and MacOS only, if you have a different OS, please let me know, I will add support for it).

![Eyedropper](/docu/eyedropper.gif)



# Bugs, Requests and Questions

To report bugs, request features or ask questions regarding VertX Artist, visit: [GitHub Issues](https://github.com/Mahrkeenerh/VertXArtist/issues)
