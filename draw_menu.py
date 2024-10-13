import gpu
from gpu_extras.batch import batch_for_shader
import blf
import bpy

from .utils import get_cursor_location ,debug, get_pref, shorten_with_prefix

class UIDraw:
    def __init__(self,context,options: list[str], text_editor: bpy.types.SpaceTextEditor) -> None:
        """
        Initialize the UIDraw object.

        Parameters
        ----------
        options : list[str]
            The list of options to be displayed in the UI.
        text_editor : bpy.types.SpaceTextEditor
            The SpaceTextEditor containing the text.

        Returns
        -------
        None
        """
        self.callback_handles = set()
        self.area = context.area
        self.cursor_x, self.cursor_y , self.char_w = get_cursor_location(text_editor)
        self.pref = get_pref(context)
        self.Text_handle = None
        self.UI_handles = []
        self.scroll_bar = None
        self.is_ui_ready = True
        self.options = options

        # Determine number of visible parts and handle scrollbar if needed
        self.parts = min(len(options), self.pref.items)
        if len(options) > self.pref.items:
            from .draw_scrollbar import ScrollBar
            self.scroll_bar = ScrollBar(self)

        self._calculate_vertices(self.parts)

        self._active_index = 0
        self.choice_text = ''
        self.text_index = 0
        self.active_mouse_index = -1  # Start with no active mouse index
        self.vertical_divisions: list[tuple[tuple[float, float], tuple[float, float]]] | None = None

    def _calculate_vertices(self, divisions: int) -> None:
        """Divide the vertices into the given number of divisions and return the list of vertices."""
        
        self.vertices = (
            (self.cursor_x, self.cursor_y),
            (self.cursor_x + self.pref.ui_width, self.cursor_y),
            (self.cursor_x, self.cursor_y - (self.pref.ui_hight*divisions)),
            (self.cursor_x + self.pref.ui_width, self.cursor_y - (self.pref.ui_hight*divisions)),
        )
        self.vertices_divisions = []
        y_max = max(y for _, y in self.vertices)
        y_min = min(y for _, y in self.vertices)
        y_divided = (y_max - y_min) / divisions

        for i in range(divisions):
            v1 = self.vertices[0]
            v2 = self.vertices[1]
            v3 = self.vertices[2]
            v4 = self.vertices[3]

            top_y = y_max - (i * y_divided)
            bottom_y = top_y - y_divided

            self.vertices_divisions.append(
                (
                    (v1[0], bottom_y),
                    (v2[0], bottom_y),
                    (v3[0], top_y),
                    (v4[0], top_y)
                )
            )
    @property
    def active_index(self) -> int:
        """Get the active index of the UI."""
        return self._active_index
    
    @active_index.setter
    def active_index(self, value):
        """Update text options when the active index changes."""
        if value < 0:
            self._active_index = 0
            self.increment_text_up()
        elif value > self.parts-1:
            self._active_index = self.parts-1
            self.increment_text_down()
        else:
            self._active_index = value
        
    def increment_text_up(self) -> None:
        """Increment the text index up."""
        if self.text_index > 0:
            self.text_index -= 1
            self.scroll_bar.move_scrollbar(up=True)

    def increment_text_down(self) -> None:
        """Increment the text index down."""
        current_index = self.text_index + self.parts
        if current_index < len(self.options):
            self.text_index += 1
            self.scroll_bar.move_scrollbar()

    
    def get_mouse_choice(self) -> str:
        """
        Get the choice of the UI that is currently under the mouse.
        Never Called unless the mouse is over the UI.
        """
        return self.options[self.text_index:self.text_index + self.parts][self.active_mouse_index]

    
    def erase(self):
        for handle in self.callback_handles:
            bpy.types.SpaceTextEditor.draw_handler_remove(handle, 'WINDOW')

    def show(self):
        """
        Creates draw handlers for each rectangle.

        This function adds a draw handler for each rectangle in the menu and
        a draw handler for the text in the menu. If a scrollbar is present, it
        also adds a draw handler for the scrollbar.
        """
        def ui_callback(index, vertices):
            if not self.area == bpy.context.area:
                return
            """Draws the specific rectangle by index."""
            gpu.state.blend_set('ALPHA')  # Enable alpha blending
            color = self.get_rectangle_color(index)
            indices = ((0, 1, 2), (2, 1, 3))
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
            batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)
            shader.uniform_float("color", color)
            batch.draw(shader)

        def text_callback(_, context):
            """
            Draw the text of the UI.

            This function draws the text of the UI by iterating over the visible
            options and drawing each one in the correct position. The text is
            shortened if it is too long to fit in the UI.
            """
            if self.area != bpy.context.area:
                return

            vertices = self.vertices_divisions
            x_pos = vertices[0][0][0] + self.pref.x_offset
            y_offset = self.pref.y_offset
            font_size = self.pref.font_size
            font_id = self.pref.font_id
            text_col = self.pref.text_color

            visible_text = self.options[self.text_index:self.text_index + self.parts]
            for i, text in enumerate(visible_text):
                y_pos = vertices[i][0][1] + y_offset

                # Shorten the text if it is too long to fit in the UI
                text_ = shorten_with_prefix(text.strip(), width=int((self.pref.ui_width/font_size)*2))
                # Set the position of the text
                blf.position(font_id, x_pos, y_pos, 0)

                # Set the size of the text
                blf.size(font_id, font_size)
                blf.color(font_id,*text_col)

                # Draw the text
                blf.draw(font_id, text_)

                # If this is the active option, store the text in self.choice_text
                if i == self.active_index:
                    self.choice_text = text

        def draw(draw_fun: callable, args=(None, None)):
            return bpy.types.SpaceTextEditor.draw_handler_add(
                draw_fun,
                args,
                'WINDOW',
                'POST_PIXEL' # ('POST_PIXEL', 'POST_VIEW', 'PRE_VIEW', 'BACKDROP')
            )
        
        # Add a draw handler for each rectangle in the menu
        for i, vertices in enumerate(self.vertices_divisions):
            self.callback_handles.add(draw(ui_callback, (i, vertices)))
        
        # Add a draw handler for the text in the menu
        self.callback_handles.add(draw(text_callback))
        
        # If a scrollbar is present, add a draw handler for it
        if self.scroll_bar:
            self.scroll_bar.create_scrollbar()
            self.callback_handles.add(draw(self.scroll_bar.scroll_col_callback))
            self.callback_handles.add(draw(self.scroll_bar.scroll_bar_callback))
        
    def get_rectangle_color(self, index):
        prefs = self.pref
        if index == self.active_index:
            return prefs.active_color
        elif index == self.active_mouse_index:
            return prefs.mouse_highlight_color
        return prefs.background_color
