import pydoc
import re
import gpu
import blf
import bpy
from gpu_extras.batch import batch_for_shader
from .utils import CharInfo, get_pref ,debug, shorten_with_prefix
from.event_tracker import EventTracker
class InfoUi:
    callback_handle = None
    mouse_tracker = None
    vertices = None
    area = None
    pref = None
    text = None
    line_height = 20
    font_size = 15
    char_info = None
    # For scrolling of text
    text_range = None
    visibilty_index = 1 # Starts at 1, not 0 due to first line 

    def __init__(self,context, mousepos):
        InfoUi.char_info = CharInfo(context, context.space_data)
        InfoUi.area = bpy.context.area
        InfoUi.pref = get_pref(context)
        self.update(context,mousepos)

    @classmethod
    def show(cls):
        """
        Show the function info box. If already shown, this does nothing.
        """
        if cls.callback_handle is not None:
            return

        def draw_ui_callback(vertices):
            """
            Draw the function info box in the 3D view.
            """
            if cls.area != bpy.context.area or cls.hide:
                return

            color = (0.47, 0.4, 0.1, 1)
            indices = ((0, 1, 2), (2, 1, 3))
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
            batch = batch_for_shader(shader, 'TRIS', {"pos": cls.vertices}, indices=indices)
            shader.uniform_float("color", color)
            batch.draw(shader)
        def text_callback(_):
            """
            Draw the text of the UI.
            """
            if cls.area != bpy.context.area or cls.hide:
                return

            x_pos = cls.vertices[0][0] + 10  # Add padding
            y_pos = cls.vertices[0][1] # + 10  # Add padding

            for i in range(cls.text_range[0], cls.text_range[1]):
                text = cls.text[i]
                blf.position(0, x_pos, y_pos - (i * cls.line_height), 0)
                blf.size(0, cls.pref.font_size)
                # Draw text with line wrapping if necessary
                blf.draw(0, text)
        cls.callback_handle = bpy.types.SpaceTextEditor.draw_handler_add(
            draw_ui_callback,
            (None, ),
            'WINDOW',
            'POST_PIXEL' # ('POST_PIXEL', 'POST_VIEW', 'PRE_VIEW', 'BACKDROP')
        )
        cls.text_handle = bpy.types.SpaceTextEditor.draw_handler_add(
            text_callback,
            (None, ),
            'WINDOW',
            'POST_PIXEL' # ('POST_PIXEL', 'POST_VIEW', 'PRE_VIEW', 'BACKDROP')
        )

    @staticmethod
    def erase():
        bpy.types.SpaceTextEditor.draw_handler_remove(InfoUi.callback_handle, 'WINDOW')
        InfoUi.callback_handle = None
    @classmethod
    def update(cls, context, mouse_position):
        """
        Update the position and visibility of the function info box based on the mouse position.
        """
        line_idx, char_idx = cls.char_info.find_cursor_position(mouse_position[0], mouse_position[1])
        if line_idx < 0 or char_idx < 0:
            cls.hide = True
            return
        cls.hide = False

        line_content = context.space_data.text.lines[line_idx].body
        prefix = line_content[:char_idx]
        suffix = line_content[char_idx:].split(".")[0].rstrip(')').rstrip('(')

        function_name = prefix + suffix
        try:
            doc_output = pydoc.render_doc(function_name, title="%s", renderer=pydoc.plaintext)
        except Exception as e:
            debug(e)
            cls.hide = True
            return
        cls.text = format_renderdoc_output(doc_output)

        cls.cal_ui(line_idx, char_idx)
        
        EventTracker.redraw()
        if not cls.callback_handle:
            cls.show()
    @classmethod
    def cal_ui(cls, line_index, char_index):
        """
        Calculate the vertices and visibility range for the function info box based on the mouse position.

        Args:
            line_index (int): The line index of the mouse position.
            char_index (int): The character index of the mouse position.
        """
        x, y, _ = cls.char_info.get_char_location(line_index, char_index)
        max_height = 500
        text_height = len(cls.text) * cls.line_height
        
        if text_height > max_height:
            height  = max_height
            cls.text_range = (cls.visibilty_index, max_height // cls.line_height)
        else:
            height = text_height
            cls.text_range = (cls.visibilty_index  , len(cls.text))
        
        max_width = 500
        largest_text = max(cls.text, key=len)
        char_width = cls.get_charwidth()
        width = len(largest_text) * char_width
        if width > max_width:
            width = max_width
        cls.vertices = (
            (x, y),
            (x + width, y),
            (x, y - height),
            (x + width, y - height),
        )


    @classmethod
    def get_charwidth(cls):
        blf.size(0, cls.pref.font_size)
        return blf.dimensions(0, "_")[0]

def format_renderdoc_output(output):
    # Split the output into lines
    lines = output.split('\n')
    # Initialize variables
    formatted_lines = []
    current_level = 0
    
    # Process each line
    for line in lines:
        # Check for headings
        if re.match(r'^\s*([A-Za-z0-9\s]+)$', line):
            heading_level = len(line.split())
            formatted_lines.append('{' + '#' * heading_level + '} ' + line.strip())
            current_level = max(current_level, heading_level)
        
        # Check for bold text
        elif re.search(r'\*\*', line):
            formatted_lines.append(re.sub(r'\*\*', '**', line))
        
        # Check for italic text
        elif re.search(r'_', line):
            formatted_lines.append(re.sub(r'_', '_', line))
        
        # Check for lists
        elif line.startswith((' ', '-')):
            formatted_lines.append('- ' + line[2:])
        
        # Check for code blocks
        elif re.match(r'^\s*`', line):
            formatted_lines.append(line.strip() + ':')
            current_level += 1
        elif line == '':
            pass
        else:
            formatted_lines.append(line)
    
    # Join the formatted lines back together
    return formatted_lines

