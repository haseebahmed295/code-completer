import ast
import code
import bpy
from bl_console_utils.autocomplete import intellisense
from typing import Optional, Tuple
from .utils import get_autoconsole , debug
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
            Console = code.InteractiveConsole(
                locals=b_console.locals if b_console else None)

        # If the preference is set to auto-import, import any modules on the
        # current line
        if context.scene.auto_import:
            module_importer(context, Console)
            
        update_console_state(context, Console)
         
        # Expand the current line using intellisense
        result = intellisense.expand(
            line, cursor, Console.locals, private=context.scene.show_private)
    except AttributeError:
        # If there's an AttributeError, return None
        return None

    return result


executed_lines = []


def update_console_state(context: bpy.types.Context, console: code.InteractiveConsole):
    """
    Parses all lines before the current one to safely update the console's state
    for autocompletion without executing potentially harmful code.
    """
    global executed_lines
    text = context.space_data.text

    if len(text.lines) < len(executed_lines):
        executed_lines.clear()
        console.resetbuffer()
        b_console = get_autoconsole(context)
        if b_console:
            console.locals.update(b_console.locals)

    # Find the current line's index by iterating
    current_line_index = 0
    for i, line in enumerate(text.lines):
        if line == text.current_line:
            current_line_index = i
            break


    for i in range(current_line_index):
        line_body = text.lines[i].body
        if not line_body or i < len(executed_lines):
            continue

        try:
            tree = ast.parse(line_body)
            node = tree.body[0]

            if isinstance(node, ast.Assign):
                var_name = node.targets[0].id
                value = eval(ast.get_source_segment(
                    line_body, node.value), console.locals)
                console.locals[var_name] = value

            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                console.runcode(line_body)

        except Exception:
            # Ignore lines that are not valid or cause errors
            pass
        finally:
            executed_lines.append(line_body)

def ShowMessageBox(message="", title="Sendc Console Message", icon='INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


def module_importer(context, console: code.InteractiveConsole, im_libs=[]):
    lines = context.space_data.text.lines
    for line in lines:
        if not line == context.space_data.text.current_line and line.body.startswith("import ") and not line.body in im_libs:
            try:
                console.runcode(line.body)
            except ModuleNotFoundError:
                pass
            finally:
                im_libs.append(line.body)