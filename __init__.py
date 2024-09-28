bl_info = {
    "name": "Code Completer",
    "description": " code-completion is an addon allows autocompletion of code in text editor",
    "author": "haseebahmad295",
    "version": (0, 1, 0),
    "blender": (3, 6, 0),
    "location": "Text",
    "category": "Object" }
    
import bpy
from bpy.types import (
    Panel,
    Operator,
)
from .auto_complete import complete , execute_code
from .draw_menu import  UIDraw
from .event_tracker import EventTracker
from .utils import debug , draw_keymap_items
class Search_Text(Operator):
    '''Options'''
    bl_idname = "text.search_text"
    bl_label = "Search Text"

    com: bpy.props.StringProperty(name="Completion Command")
    @classmethod
    def poll(cls, context):
        return not len(bpy.data.texts) == 0 and context.scene.code_suggest
    def invoke(self, context, event):
        bpy.ops.text.insert(text=event.ascii)

        sc = context.space_data
        text = sc.text
        if text and text.current_character > 0:
            left_body_line = text.current_line.body[:text.current_character]
            options = None            
            result = complete(context)
            # debug(result)
            if result:                
                if result[0] == left_body_line:
                    if result[2] == "":
                        return {'CANCELLED'}
                    else:
                        options = result[2].split("\n")
                else:
                    if left_body_line in result[0]:
                        options = [result[0].replace(left_body_line, "")]
                
                if options:
                    self.draw_ui = UIDraw(context,options ,sc)
                    self.draw_ui.show()
                    self.start_Tracker(context)
                    # self._tracker = context.window_manager.event_timer_add(1, window=context.window)
                    context.window_manager.modal_handler_add(self)
                return {'RUNNING_MODAL'}
        return {'FINISHED'}
    
    def start_Tracker(self, context):
        self.mouse_tracker = EventTracker(self.draw_ui)
        self.mouse_tracker.disable_keys()

    def stop_tracker(self, context):
        self.mouse_tracker.enable_keys()
        self.draw_ui.erase()
        self.mouse_tracker.redraw()

        del self.mouse_tracker
        del self.draw_ui

    def modal(self, context, event):
        """Modal handler for the text completion operator."""

        # Handle mouse selection.
        if event.type == 'LEFTMOUSE':
            if self.draw_ui.active_mouse_index != -1:
                self.com = self.draw_ui.get_mouse_choice()
                self.stop_tracker(context)
                self.execute(context)
                return {'FINISHED'}
            else:
                self.stop_tracker(context)
                return {'CANCELLED'}
        # Handle scrolling.
        if event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            if not self.mouse_tracker.scroll(event, (event.mouse_region_x, event.mouse_region_y)):
                return {'PASS_THROUGH'}
            else:
                self.stop_tracker(context)
                return {'CANCELLED'}
        # Handle mouse movement.
        if event.type == 'MOUSEMOVE':
            self.mouse_tracker.mouse_pos = (event.mouse_region_x, event.mouse_region_y)
            return {'PASS_THROUGH'}
     
        # Handle key presses.
        if event.value == 'PRESS':
            if event.type in {'UP_ARROW', 'DOWN_ARROW'}:
                self.mouse_tracker.increment_text(event.type == 'UP_ARROW')
                return {'PASS_THROUGH'}
            elif event.type == 'RET':
                self.com = self.draw_ui.choise_text
                self.stop_tracker(context)
                self.execute(context)
                return {'FINISHED'}
            elif event.type == 'BACK_SPACE':
                bpy.ops.text.delete(type='PREVIOUS_CHARACTER')
                self.stop_tracker(context)
                return {'FINISHED'}
            elif event.type == 'ESC':
                self.stop_tracker(context)
                return {'CANCELLED'}
            else:
                # debug(event.type)
                bpy.ops.text.insert(text=event.ascii)
                self.stop_tracker(context)
                bpy.ops.text.search_text("INVOKE_DEFAULT")
                return {'CANCELLED'}

        return {'PASS_THROUGH'}
    def execute(self, context):
        bpy.ops.ed.undo_push()
        sc = context.space_data
        text = sc.text

        comp = self.com
        line = text.current_line.body

        lline = len(line)
        lcomp = len(comp)

        intersect = [-1, -1]

        for i in range(lcomp):
            val1 = comp[0:i + 1]

            for j in range(lline):
                val2 = line[lline - j - 1::]

                if val1 == val2:
                    intersect = [i, j]
                    break

        comp = comp.strip()
        if intersect[0] > -1:
            newline = line[:text.current_character] + comp + line[text.current_character:]
        else:
            newline = line[:text.current_character] + comp + line[text.current_character:]
        text.current_line.body = newline

        for textcount in range(len(comp)):
            bpy.ops.text.move(type='NEXT_CHARACTER')
        return {'FINISHED'}

class Code_PT_Complete_panel(Panel):
    bl_idname = "Code_PT_Complete_panel"
    bl_label = "Auto Complete"
    bl_space_type = "TEXT_EDITOR"
    bl_region_type = 'WINDOW'
    bl_ui_units_x = 5

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.scene, "auto_import")

class Code_Execute(Operator):
    bl_idname = "text.execute"
    bl_label = "Execute"

    def execute(self, context):
        sc = context.space_data
        text = sc.text
        execute_code(context , text.current_line)
        self.report({'INFO'}, "Code Executed")
        return {'FINISHED'}

class Auto_Properties(bpy.types.AddonPreferences):
    bl_idname = __package__
    y_offset : bpy.props.IntProperty(name="Text Y Offset", default=10 , subtype="PIXEL")
    ui_hight : bpy.props.IntProperty(name="Ui Hight", default=30 ,  subtype="PIXEL")
    ui_width : bpy.props.IntProperty(name="Ui Width", default=500 , subtype="PIXEL")
    x_offset : bpy.props.IntProperty(name="Text X Offset", default=10 ,  subtype="PIXEL")
    items : bpy.props.IntProperty(name="Max Options Displayed", default=12)

    background_color : bpy.props.FloatVectorProperty(
        name="Background Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(0.14510 , 0.14510 , 0.14902, .9)
    )
    active_color : bpy.props.FloatVectorProperty(
        name="Active Selection Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(0.01569 , 0.22353 , 0.36863, 1)
    )
    mouse_highlight_color : bpy.props.FloatVectorProperty(
        name="Mouse Hover Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(0.63137 , 0.66667 , 0.6666, 1)
    )
    font_size: bpy.props.IntProperty(name="Font Size", default=12)
    type_menu: bpy.props.EnumProperty(
        name="Type",
        items=[
            ('UI', "Interface", "Interface Elements"),
            ('KEYS', "KeyMaps", "Shortcuts Keys"),
        ],
        default='UI'
    )

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.prop(self, "type_menu" , expand=True)

        if self.type_menu == 'UI':
            main_row = layout.row()         

            ui_col = main_row.box().column()
            ui_col.label(text="UI: ")
            row = ui_col.row(align=True)
            row.prop(self, "ui_hight" , text="Cell Height")
            row = ui_col.row(align=True)
            row.prop(self, "ui_width" , text="Cell Width")
            row = ui_col.row(align=True)
            row.prop(self, "items" , text="Max Options" )

            text_col = main_row.box().column()
            text_col.label(text="Text: ")
            row = text_col.row(align=True)
            row.prop(self, "x_offset")
            row = text_col.row(align=True)
            row.prop(self, "y_offset")
            row = text_col.row(align=True)
            row.prop(self, "font_size" , expand=True)

            col = layout.column(align=True)
            col.prop(self, "background_color")
            col.prop(self, "active_color")
            col.prop(self, "mouse_highlight_color")

        elif self.type_menu == 'KEYS':
            draw_keymap_items(self, context , code_keymaps)

def code_suggest_menu(self, context: bpy.types.Context) -> None:
    """Draw the code suggest menu in the Text header.

    Parameters
    ----------
    context : bpy.types.Context
        The current context.
    """
    layout = self.layout

    row = layout.row(align=True)
    row.prop(context.scene, "code_suggest", text="", icon="VIEWZOOM")
    row.popover(Code_PT_Complete_panel.bl_idname, text="")

code_keymaps = []

classes = [
    Code_Execute,
    Code_PT_Complete_panel,
    Search_Text,
    Auto_Properties,
]

def register_keymaps() -> None:
    """
    Register keymaps for the add-on.
    """
    keymaps = bpy.context.window_manager.keyconfigs.addon.keymaps
    if keymaps:
        keymap = keymaps.new(name="Text", space_type="TEXT_EDITOR")

        keymap_item = keymap.keymap_items.new(
            Code_Execute.bl_idname, type="R", value="PRESS" , ctrl = True)

        code_keymaps.append((keymap, keymap_item))
        
        keymap = keymaps.new(name="Text", space_type="TEXT_EDITOR")

        keymap_item = keymap.keymap_items.new(
            Search_Text.bl_idname, type="TEXTINPUT", value="PRESS")

        code_keymaps.append((keymap, keymap_item))
        
def unregister_keymaps() -> None:
    """
    Unregister keymaps for the add-on.
    """
    window_manager = bpy.context.window_manager
    keyconfig = window_manager.keyconfigs.addon
    if keyconfig:
        for keymap, keymap_item in code_keymaps:
            keymap.keymap_items.remove(keymap_item)
    code_keymaps.clear()

def register() -> None:
    """
    Register the classes and keymaps for the add-on.
    """
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.code_suggest = bpy.props.BoolProperty(
        name="Suggest Code Completion",
        description="Suggest Code Completion",
        default=True,
    )
    bpy.types.Scene.auto_import = bpy.props.BoolProperty(
        name="Auto Import",
        description="Automatically import modules for completion",
        default=True,
    )

    bpy.types.TEXT_HT_header.append(code_suggest_menu)
    register_keymaps()
def unregister() -> None:
    """
    Unregister the classes, keymaps, and property for the add-on.
    """
    unregister_keymaps()
    bpy.types.TEXT_HT_header.remove(code_suggest_menu)
    del bpy.types.Scene.code_suggest
    del bpy.types.Scene.auto_import
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()