import code
import bpy
from console_python import get_console 
from bl_console_utils.autocomplete import intellisense
from typing import Optional, Tuple
from .utils import debug
Console = None
def complete(context: bpy.types.Context) -> Optional[Tuple[str, int, str]]:
    """
    Autocomplete the current line of the given context.

    This function works by using the `intellisense` module to autocomplete the
    current line of the given context. It uses the `code.InteractiveConsole`
    class to track the state of the current line and provide completions.

    Args:
        context: The context to complete text for.

    Returns:
        A tuple of the autocompleted string, new cursor position, and the new
        text following the cursor. If the line is empty or can't be
        autocompleted, returns None.
    """
    try:
        text = context.space_data.text
        cursor = text.current_character
        line = text.current_line.body[:cursor]
        
        # Get the console locals
        global Console
        if Console is None:
            b_console = get_autoconsole(context)
            Console = code.InteractiveConsole(locals=b_console.locals if b_console else None)
        
        # If the preference is set to auto-import, import any modules on the
        # current line
        if context.scene.auto_import:
            module_importer(context, Console)
        
        # Analyze any code that's not on the current line
        analyze_code(context, Console)
        
        # Expand the current line using intellisense
        result = intellisense.expand(line, cursor, Console.locals, private=context.scene.show_private)
    except AttributeError:
        # If there's an AttributeError, return None
        return None
    
    return result


def ShowMessageBox(message = "", title = "Sendc Console Message", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

def module_importer(context , console: code.InteractiveConsole , im_libs = []):
    lines = context.space_data.text.lines
    for line in lines:
        if not line == context.space_data.text.current_line and line.body.startswith("import ") and not line.body in im_libs:
            try: 
                console.runcode(line.body)
            except ModuleNotFoundError:
                pass
            finally:
                im_libs.append(line.body)
                
def analyze_code(context, console: code.InteractiveConsole) -> None:
    """Analyze each line of code in the text editor and execute it if it is a valid statement."""
    excluded_statements = [
        "import ",
        "from ",
        "as ",
        "def ",
        "class ",
        "if ",
        "elif ",
        "else ",
        "for ",
        "while ",
        "in ",
        "return ",
        "yield ",
    ]

    for line in context.space_data.text.lines:
        if line == context.space_data.text.current_line:
            continue

        if any(line.body.startswith(statement) for statement in excluded_statements):
            continue

        console.runcode(line.body)
        
def get_autoconsole(context):
    for area in context.screen.areas:
        if area.type == "CONSOLE":
            region = area.regions[1]
            break
    else:
        return None
    return get_console(hash(region))[0]
