bl_info = {
    "name": "Code Completer",
    "description": " code-completion is an addon allows autocompletion of code in text editor",
    "author": "haseebahmad295",
    "url": "https://github.com/haseebahmed295/code-completer",
    "version": (1, 2, 0),
    "blender": (3, 6, 0),
    "location": "Text",
    "category": "Development" }
import bpy
from bpy.types import (
    Panel,
    Operator,
)
from .auto_complete import complete
from .draw_menu import  UIDraw
from .event_tracker import EventTracker
from .utils import debug , draw_keymap_items, get_text_editor_context
from .func_insperter import InfoUi

class MousePositionTimer(bpy.types.Operator):
    bl_idname = "custom.mouse_position_timer"
    bl_label = "Mouse Position Timer"
    context = None

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        """Invoke the operator to show the code completion menu."""
        mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        if InfoUi.mouse_tracker == mouse_pos:
            return {'FINISHED'}
        InfoUi.mouse_tracker = mouse_pos
        InfoUi(context, mouse_pos)
        return {'FINISHED'}

    @classmethod
    def analyser(cls):
        EventTracker.redraw()
        if not cls.context:
            context = get_text_editor_context()
        if context:
            with bpy.context.temp_override(**context):
                bpy.ops.custom.mouse_position_timer("INVOKE_DEFAULT")
        return .001

# Still Worling on it
bpy.app.timers.register(MousePositionTimer.analyser)


class Search_Text(Operator):
    '''Options'''
    bl_idname = "text.search_text"
    bl_label = "Search Text"

    com: bpy.props.StringProperty(name="Completion Command")
    lmb = False
    @classmethod
    def poll(cls, context):
        return not len(bpy.data.texts) == 0 and context.scene.code_suggest
    def invoke(self, context, event):
        bpy.ops.text.insert(text=event.ascii)

        text_editor = context.space_data
        text = text_editor.text
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
                    self.draw_ui = UIDraw(context,options ,text_editor)
                    self.draw_ui.show()
                    self.start_Tracker(event)
                    # self._tracker = context.window_manager.event_timer_add(1, window=context.window)
                    context.window_manager.modal_handler_add(self)
                return {'RUNNING_MODAL'}
        return {'FINISHED'}
    
    def start_Tracker(self, event):
        self.mouse_tracker = EventTracker(self.draw_ui)
        self.mouse_tracker.mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        self.mouse_pos_y = self.draw_ui.cursor_y

    def stop_tracker(self, context):
        self.draw_ui.erase()
        self.mouse_tracker.redraw()

        del self.mouse_tracker
        del self.draw_ui

    def modal(self, context, event):
        # debug(event.type , event.value)
        """Modal handler for the text completion operator."""
        # Handle mouse selection.
        if self.mouse_tracker.lmb:
            if event.value == 'RELEASE':
                self.mouse_tracker.lmb = None
                return {'RUNNING_MODAL'}


        if event.type == 'LEFTMOUSE':
            # Check if mouse on the scroll bar
                if self.draw_ui.active_mouse_index != -1:
                    self.com = self.draw_ui.get_mouse_choice()
                    self.stop_tracker(context)
                    self.execute(context)
                    return {'FINISHED'}
                elif self.mouse_tracker.is_scrollcol_active():
                    self.mouse_tracker.lmb = event.value == 'PRESS'
                    return {'RUNNING_MODAL'} # For handling scroll bar
                else:
                    self.stop_tracker(context)
                    return {'CANCELLED'}
        # Handle mouse movement.
        if event.type == 'MOUSEMOVE':
            if self.mouse_tracker.lmb:
                self.draw_ui.scroll_bar.update_scroll(event.mouse_region_y)
            self.mouse_tracker.mouse_pos = (event.mouse_region_x, event.mouse_region_y)
            return {'PASS_THROUGH'}
            
        # Handle scrolling.
        if event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            if self.mouse_tracker.scroll(event, (event.mouse_region_x, event.mouse_region_y)):
                return {'RUNNING_MODAL'}
            else:
                self.stop_tracker(context)
                return {'CANCELLED'}
     
        # Handle key presses.
        if event.value == 'PRESS':
            if event.type in {'UP_ARROW', 'DOWN_ARROW'}:
                self.mouse_tracker.increment_text(event.type == 'UP_ARROW')
                return {'RUNNING_MODAL'}
            elif event.type == 'RET':
                self.com = self.draw_ui.choice_text
                self.stop_tracker(context)
                self.execute(context)
                return {'FINISHED'}
            elif event.type == 'BACK_SPACE':
                bpy.ops.text.delete(type='PREVIOUS_CHARACTER')
                self.stop_tracker(context)
                return {'FINISHED'}
            elif event.type in {'ESC', 'RIGHTMOUSE'}:
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

class Code_PT_AutoComplete(Panel):
    bl_idname = "CODE_PT_AutoComplete"
    bl_label = "Auto Complete"
    bl_space_type = "TEXT_EDITOR"
    bl_region_type = 'WINDOW'
    bl_ui_units_x = 5

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.scene, "auto_import")
        col.prop(context.scene, "show_private", text="Show Internal")

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
        default=(0.4 , 0.4 , 0.4, 0.4)
    )
    font_size: bpy.props.IntProperty(name="Font Size", default=12)
    font_id: bpy.props.IntProperty(name="Font ID", default=0)
    text_color: bpy.props.FloatVectorProperty(
        name="Text Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1 , 1 , 1, 1)
    )
    scrollbar_color: bpy.props.FloatVectorProperty(
        name="Scrollbar Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(0.5 , 0.5 , 0.5, 0.5)
    )
    scrollbar_active_color: bpy.props.FloatVectorProperty(
        name="Scrollbar Active Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(0.6 , 0.6 , 0.6, 0.6)
    )
    scrollcol_color: bpy.props.FloatVectorProperty(
        name="ScrollCol Color",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(0.14510 , 0.14510 , 0.14902, 1)
    )
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
            main_row = layout.grid_flow(row_major=False, columns=0, even_columns=True, even_rows=False, align=False)      

            ui_col = main_row.box().column()
            ui_col.label(text="UI: ")
            row = ui_col.row(align=True)
            row.prop(self, "ui_hight" , text="Cell Height")
            row = ui_col.row(align=True)
            row.prop(self, "ui_width" , text="Cell Width")
            row = ui_col.row(align=True)
            row.prop(self, "items" , text="Max Options" )
            row = ui_col.row(align=True)

            text_col = main_row.box().column()
            text_col.label(text="Text: ")
            row = text_col.row(align=True)
            row.prop(self, "x_offset")
            row = text_col.row(align=True)
            row.prop(self, "y_offset")
            row = text_col.row(align=True)
            row.prop(self, "font_size" , expand=True)
            row = text_col.row(align=True)
            row.prop(self, "font_id" , expand=True)
            row = text_col.row(align=True)
            
            col = layout.column(align=True)
            col.prop(self, "text_color")
            col.prop(self, "background_color")
            col.prop(self, "active_color")
            col.prop(self, "mouse_highlight_color")
            col.prop(self, "scrollbar_color")
            col.prop(self, "scrollbar_active_color")
            col.prop(self, "scrollcol_color")



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
    row.popover(Code_PT_AutoComplete.bl_idname, text="")
    

code_keymaps = []

classes = [
    Code_PT_AutoComplete,
    Search_Text,
    Auto_Properties,
    MousePositionTimer
]

def register_keymaps() -> None:
    """
    Register keymaps for the add-on.
    """
    keymaps = bpy.context.window_manager.keyconfigs.addon.keymaps
    if keymaps:

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
    bpy.types.Scene.show_private = bpy.props.BoolProperty(
        name="Show Internal Attributes",
        description="Toggle to show internal attributes",
        default=False,
    )
    bpy.types.TEXT_HT_header.append(code_suggest_menu)

    register_keymaps()
def unregister() -> None:
    """
    Unregister the classes, keymaps, and property for the add-on.
    """
    try:
        bpy.app.timers.unregister(MousePositionTimer.analyser)
    except:
        pass
    unregister_keymaps()
    bpy.types.TEXT_HT_header.remove(code_suggest_menu)
    del bpy.types.Scene.code_suggest
    del bpy.types.Scene.auto_import
    del bpy.types.Scene.show_private
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()