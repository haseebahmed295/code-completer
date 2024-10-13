import bpy
import rna_keymap_ui
import textwrap

try:
    import icecream
    debug = icecream.ic
except ImportError:
    debug = print

def get_pref(context: bpy.types.Context) -> bpy.types.AddonPreferences: 
    return context.preferences.addons[__package__].preferences
def shorten_with_prefix(text: str, width: int, placeholder: str = "...") -> str:
    if len(text) <= width:
        return text
    
    # Calculate the maximum length we can use for the prefix
    prefix_length = width - len(placeholder)
    
    # Find the last space before the prefix_length
    last_space_index = text.rfind(' ', 0, prefix_length + 1)
    
    if last_space_index == -1:
        # No space found, truncate at prefix_length
        return text[:prefix_length] + placeholder
    
    # Truncate at the last space
    return text[:last_space_index] + placeholder
def get_character_widht(text_editor: bpy.types.SpaceTextEditor, firstx: float, lines: list[bpy.types.TextLine]) -> float:
    """
    Returns the width of a single character in the text editor.

    This function takes into account the width of the line numbers and
    the current character position in the line.

    Parameters
    ----------
    st : SpaceTextEditor
        The SpaceTextEditor containing the text.
    firstx : float
        The x coordinate of the first character of the current line.
    lines : list[TextLine]
        The list of TextLine objects representing the text.

    Returns
    -------
    float
        The width of a single character in the text editor.
    """
    # Iterate over the lines and find the first line with more than one character
    for idx, line in enumerate(lines):
        if len(line.body) > 1:
            # Calculate the width of the character by subtracting the x coordinate of the first character
            # from the x coordinate of the second character
            return text_editor.region_location_from_cursor(idx, 1)[0] - firstx
    else:
        # If no line with more than one character is found, use the x coordinate of the first character of the first line
        return text_editor.region_location_from_cursor(0, 1)[0] - firstx
    
def get_cursor_location(text_editor: bpy.types.SpaceTextEditor) -> tuple:
    """
    Returns the x, y coordinates of the 3D view cursor as a tuple of two floats.

    This function takes into account the width of the line numbers and
    the current character position in the line.

    Parameters
    ----------
    text_editor : bpy.types.SpaceTextEditor
        The SpaceTextEditor containing the text.

    Returns
    -------
    tuple
        A tuple of two floats representing the x, y coordinates of the cursor.
    """
    # Get the lines of the text and the current line index
    lines = text_editor.text.lines
    current_line = text_editor.text.current_line_index

    # Get the x, y coordinates of the first character of the current line
    first_x, y = text_editor.region_location_from_cursor(current_line, 0)

    # Calculate the x offset of the cursor based on the line numbers and
    # the current character in the line
    x_offset = get_character_widht(text_editor, first_x, lines)

    # Calculate the x position of the cursor
    char_count = text_editor.text.current_character
    if text_editor.show_line_numbers:
        # Include the width of the line numbers in the calculation
        x = x_offset * (char_count + len(repr(len(lines))) + 2)
    else:
        x = x_offset * char_count

    return (x, y , x_offset)

def draw_keymap_items(self, context: bpy.types.Context, keymaps: list[tuple[bpy.types.KeyMap, bpy.types.KeyMapItem]]) -> None:
    """Draw keymap items into the UI.

    Parameters
    ----------
    context : bpy.types.Context
        The current context.
    keymaps : list[tuple[bpy.types.KeyMap, bpy.types.KeyMapItem]]
        The list of keymaps and their corresponding keymap items to draw.
    """
    layout = self.layout
    user_keyconfig = context.window_manager.keyconfigs.user
    last_keymap_name = ""

    for keymap, keymap_item in keymaps:
        # Get the keymap and keymap item from the user's keyconfig
        user_keymap = user_keyconfig.keymaps[keymap.name]
        user_keymap_item = next((item for item in user_keymap.keymap_items if item.idname == keymap_item.idname), None)

        if user_keymap_item:
            # Draw a label with the keymap name if it has changed
            if user_keymap.name != last_keymap_name:
                layout.label(text=user_keymap.name, icon="DOT")

            # Set the context pointer for the keymap item
            layout.context_pointer_set("keymap", user_keymap)

            # Draw the keymap item
            rna_keymap_ui.draw_kmi([], user_keyconfig, user_keymap, user_keymap_item, layout, 0)

            # Add a separator
            layout.separator()

            # Store the current keymap name
            last_keymap_name = user_keymap.name