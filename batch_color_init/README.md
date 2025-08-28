# Batch Color Init - VertX Artist Extension

A simple Blender addon extension for VertX Artist that initializes color attributes on multiple selected mesh objects at once.

**⚠️ IMPORTANT: This addon requires VertX Artist to be installed and enabled to function properly.**

## Features

- Initialize color attributes named "Color" on multiple selected mesh objects at once
- Set a custom initial color value via an interactive popup dialog
- Creates BYTE_COLOR attributes in the CORNER domain
- Automatically skips objects that already have color attributes
- Sets the active color index for newly created attributes
- Works in Object Mode only
- Integrates seamlessly with VertX Artist Color Layers panel
- Perfect for preparing objects before using VertX Artist's advanced color tools

## Requirements

- Blender 4.0+
- **VertX Artist addon must be installed and enabled**

## Installation

1. **First, make sure VertX Artist addon is installed and enabled**
2. Go to Edit > Preferences > Add-ons
3. Click "Install..." button
4. Select the `batch_color_init.py` file
5. Click "Install Add-on"
6. Search for "Batch Color Init" in the add-ons list
7. Check the checkbox to enable it

## Usage

1. Select one or more mesh objects in Object Mode (non-mesh objects will be ignored)
2. Go to Properties panel > Data Properties 
3. Find the "Color Layers" section (VertX Artist panel)
4. At the top, you'll see the "Batch Color Init" section
5. Click "Initialize Selected Objects"
6. **A popup dialog will appear** - choose your desired initial color using the color picker
7. Click "OK" to apply

The addon will:
- Create a color attribute named "Color" (BYTE_COLOR type, CORNER domain) on mesh objects that don't have any color attributes
- Set the initial color to your chosen RGB value (alpha is automatically set to 1.0)
- Set the active color attribute index to the newly created attribute
- Skip objects that already have color attributes
- Display a report showing how many objects were processed and how many were skipped

## Integration with VertX Artist

This addon extends VertX Artist by adding batch initialization functionality to the Color Layers panel. It integrates by prepending its UI to the existing VertX Artist Color Layers panel (`VRTXA_PT_ColorLayers`), providing a seamless workflow for preparing multiple objects before using VertX Artist's advanced color manipulation tools.

The button appears with a COLOR icon and the text "Initialize Selected Objects" at the top of the VertX Artist Color Layers section.

## Troubleshooting

If the addon doesn't appear in the VertX Artist panel:
1. Make sure VertX Artist is installed and enabled first
2. Restart Blender after enabling both addons
3. Check the console for error messages

**Common Issues:**
- If you get a "No mesh objects selected" warning, make sure you have selected at least one mesh object
- Objects that are not mesh type (cameras, lights, empties, etc.) will be automatically ignored
- The addon only works in Object Mode - switch from Edit Mode if needed
