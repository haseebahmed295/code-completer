import bpy
from console_python import get_console 
from bl_console_utils.autocomplete import intellisense
from contextlib import contextmanager
import sys
from typing import Optional, Tuple

def complete(context: bpy.types.Context) -> Optional[Tuple[str, int, str]]:
    """
    Autocomplete the current line of the given context.

    Args:
        context: The context to complete text for.

    Returns:
        A tuple of the autocompleted string, new cursor position, and the new
        text following the cursor. If the line is empty or can't be
        autocompleted, returns None.
    """
    sc = context.space_data
    try:
        text = sc.text
        if context.scene.auto_import:
            module_importer(context)
        console = get_autoconsole(context)
        # line = text.current_line.body
        cursor = text.current_character
        line = text.current_line.body[:cursor]
        # try:
        #     if "[" == line[-1]:
        #         cursor -= 1
        # except IndexError:
        #     pass
        result = intellisense.expand(line, cursor, console.locals, private=bpy.app.debug_python)
    except AttributeError:
        result = None
    return result

@contextmanager
def redirect_stdin(new_target):
    try:
        old_target = sys.stdin
        sys.stdin = new_target
        yield
    finally:
        sys.stdin = old_target

def ShowMessageBox(message = "", title = "Sendc Console Message", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

def module_importer(context , im_libs = []):
    lines = context.space_data.text.lines
    for line in lines:
        if not line == context.space_data.text.current_line and line.body.startswith("import ") and not line.body in im_libs:
            try: 
                execute_code(context , line)
            except ModuleNotFoundError:
                pass
            finally:
                im_libs.append(line.body)
    
def get_autoconsole(context):
    for area in context.screen.areas:
        if area.type == "CONSOLE":
            region = area.regions[1]
            break
    else:
        return {'CANCELLED'}
    return get_console(hash(region))[0]

def execute_code(context , line):
    console= get_autoconsole(context)
    console.runcode(line.body)