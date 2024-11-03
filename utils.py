import bpy
import rna_keymap_ui
import textwrap

try:
    import icecream
    debug = icecream.ic
except ImportError:
    debug = print


class CharInfo:
    def __init__(self,context,  text_editor: bpy.types.SpaceTextEditor):
        self.text_editor = text_editor
        self.context = context
        self.lines = text_editor.text.lines
        
    def get_charwidth(self) -> tuple[float, float]:
        """
        Returns the width of a single character in the text editor and the y position of the first character of the current line.

        This function takes into account the width of the line numbers and
        the current character position in the line.

        Parameters
        ----------
        self : CharInfo
            The CharInfo object containing the text editor and the text lines.

        Returns
        -------
        tuple[float, float]
            A tuple containing the width of a single character in the text editor and the y position of the first character of the current line.
        """
        current_line = self.text_editor.text.current_line_index
        firstx, y = self.text_editor.region_location_from_cursor(current_line, 0)
        # Iterate over the lines and find the first line with more than one character
        for idx, line in enumerate(self.text_editor.text.lines):
            if len(line.body) > 1:
                # Calculate the width of the character by subtracting the x coordinate of the first character
                # from the x coordinate of the second character
                return self.text_editor.region_location_from_cursor(idx, 1)[0] - firstx, y
        else:
            # If no line with more than one character is found, use the x coordinate of the first character of the first line
            return self.text_editor.region_location_from_cursor(0, 1)[0] - firstx, y
        
    def get_cursor(self) -> tuple[float, float]:
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
        lines = self.text_editor.text.lines

        # Get the x, y coordinates of the first character of the current line
        x_offset , y = self.get_charwidth()

        # Calculate the x position of the cursor
        char_count = self.text_editor.text.current_character
        if self.text_editor.show_line_numbers:
            # Include the width of the line numbers in the calculation
            x = x_offset * (char_count + len(repr(len(lines))) + 2)
        else:
            x = x_offset * char_count

        return x, y 
    def get_char_location(self, line_index, char_index) -> tuple[float, float]:
        """
        Returns the x, y coordinates of a character in the text editor as a tuple of two floats.

        This function takes into account the width of the line numbers and
        the current character position in the line.

        Parameters
        ----------
        line_index : int
            The index of the line containing the character.
        char_index : int
            The index of the character in the line.

        Returns
        -------
        tuple
            A tuple of two floats representing the x, y coordinates of the character.
        """
        # Get the x, y coordinates of the first character of the specified line
        first_x, y = self.text_editor.region_location_from_cursor(line_index, 0)

        # Calculate the x offset of the character based on the line numbers and
        # the character's position in the line
        char_width = self.get_charwidth()[0]

        # Calculate the x position of the character
        if self.text_editor.show_line_numbers:
            x = char_width * (char_index + len(repr(len(self.lines))) + 2)
        else:
            x = char_width * char_index

        return x, y
    def get_y_loc(self, target_y):
        font_size = self.context.space_data.font_size
        line_hight = get_widget_unit(self.context)
        for i in range(len(self.lines)):
            _ , y1 = self.context.space_data.region_location_from_cursor(i, 0)
            diff  = abs(y1-(target_y-line_hight))
            if diff <= font_size:
                return i
        else:
            return -1

    def find_cursor_position(self,mouse_x, mouse_y):
        line_index = self.get_y_loc(mouse_y)
        # # Check if the line exists
        lines = self.lines
        if line_index < 0 or line_index >= len(lines):
            return -1, -1

        line = lines[line_index]
        char_count = len(line.body)
        char = -1
        x_offset, _ = self.get_charwidth()
        x = x_offset * (char_count + len(repr(len(lines))) + 3)
        min_diff = abs(x - mouse_x)
        for i in range(char_count):
            x = x_offset * (i + len(repr(len(lines))) + 2)
            if abs(x - mouse_x) < min_diff:
                min_diff = abs(x - mouse_x)
                char = i

        # If we reach the end of the line, return the last character index
        return line_index , char

def get_widget_unit(context):
    system = context.preferences.system
    p = system.pixel_size
    pd = p * system.dpi
    return int((pd * 20 + 36) / 72 + (2 * (p - pd // 72)))

# source/blender/windowmanager/intern/wm_window.c$515
def get_line_height_dpi(context):
    wunits = get_widget_unit(context)
    line_height_dpi = (wunits * context.space_data.font_size) / 20
    return int(line_height_dpi + 0.3 * line_height_dpi)    

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

def get_text_editor_context():
    # Find Text Editor area
    text_area = next((area for area in bpy.context.screen.areas if area.type == 'TEXT_EDITOR'), None)

    if not text_area:
        # Create new Text Editor area if none exists
        return None

    # Create context override
    ctx = bpy.context.copy()
    ctx['window'] = bpy.context.window
    ctx['screen'] = bpy.context.screen
    ctx['area'] = text_area
    ctx['region'] = text_area.regions[-1]

    return ctx