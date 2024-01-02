"""Random tools."""

import bpy


def on_name_update(self, name_list, default_name):
    def get_unique_name(name_list, name, default_name):
        """Check, if name_list containst `name`. If so, return a unique name."""
        if name.lower() == "none":
            name = default_name
        if name_list.count(name) < 2:
            return name
        i = 1
        while True:
            new_name = f"{name}.{i:03}"
            if new_name not in name_list:
                return new_name
            i += 1

    new_name = get_unique_name(name_list, self.name, default_name)
    if (new_name == self.name):
        pass
    else:
        self.name = new_name


def col_attr_exists():
    return bpy.context.object is not None and bpy.context.object.data is not None and bpy.context.object.data.color_attributes.active_color is not None


enum_items = {}


def items_to_enum(*items):
    """Convert list to enum."""

    for item in items:
        if item not in enum_items:
            enum_items[item] = item, item, item

    return [enum_items[item] for item in items]
