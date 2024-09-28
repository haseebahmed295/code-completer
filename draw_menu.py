import gpu
from gpu_extras.batch import batch_for_shader
import blf
import bpy

from .utils import get_cursor_location ,debug

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
        self.area = context.area
        self.cursor_x, self.cursor_y = get_cursor_location(text_editor)
        self.preferences = bpy.context.preferences.addons[__package__].preferences
        self.Text_handle = None
        self.UI_handles = []
        
        self.is_ui_ready = True

        if self.preferences.items > len(options):
            self.parts = len(options)
        else:
            self.parts = self.preferences.items

        self.ver_divisions = self.calculate_vertices(self.parts)

        self.active_index = 0
        self.choice_text = ''
        self.options = options
        self.text_index = 0
        self.active_mouse_index = -1  # Start with no active mouse index
        self.vertical_divisions: list[tuple[tuple[float, float], tuple[float, float]]] | None = None
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
            self.incremet_text_down()
        else:
            self._active_index = value
    def get_mouse_choice(self) -> str:
        """Get the choice of the UI that is currently under the mouse."""
        return self.options[self.text_index:self.text_index + self.parts][self.active_mouse_index]

    def increment_text_up(self) -> None:
        """Increment the text index up."""
        if self.text_index > 0:
            self.text_index -= 1

    def incremet_text_down(self):
        current_text_index  = self.text_index+self.parts
        if current_text_index < len(self.options):
            self.text_index =self.text_index+1

    def get_max_y(self) -> float:
        """Get the maximum y value from the vertices."""
        return max(y for _, y in self.vertices)
    
    def calculate_vertices(self, divisions: int) -> list:
        """Divide the vertices into the given number of divisions and return the list of vertices."""
        
        self.vertices = (
            (self.cursor_x, self.cursor_y),
            (self.cursor_x + self.preferences.ui_width, self.cursor_y),
            (self.cursor_x, self.cursor_y - (self.preferences.ui_hight*divisions)),
            (self.cursor_x + self.preferences.ui_width, self.cursor_y - (self.preferences.ui_hight*divisions)),
        )

        vertices_list = []
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

            vertices_list.append(
                (
                    (v1[0], bottom_y),
                    (v2[0], bottom_y),
                    (v3[0], top_y),
                    (v4[0], top_y)
                )
            )
        return vertices_list
    
    def ui_callback(self, index, vertices):
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

    def text_callback(self, _, context):
        if not self.area == bpy.context.area:
            return
        x_offset = self.preferences.x_offset
        vertices = self.ver_divisions
        x_pos = vertices[0][0][0] + x_offset 
        visible_text = self.options[self.text_index:self.text_index+self.parts]
        for i, text in enumerate(visible_text):
            y_pos = vertices[i][0][1] + self.preferences.y_offset
            font_id = 0
            blf.position(font_id, x_pos, y_pos, 0)
            blf.size(font_id, self.preferences.font_size)
            blf.draw(font_id, text.strip())
            if i == self.active_index:
                self.choise_text = text

    def draw(self,draw_fun: callable, args=(None, None)):
        return bpy.types.SpaceTextEditor.draw_handler_add(
            draw_fun,
            args,
            'WINDOW',
            'POST_PIXEL' # ('POST_PIXEL', 'POST_VIEW', 'PRE_VIEW', 'BACKDROP')
        )

    def erase(self):
        bpy.types.SpaceTextEditor.draw_handler_remove(self.Text_handle, 'WINDOW')
        for handle in self.UI_handles:
            bpy.types.SpaceTextEditor.draw_handler_remove(handle, 'WINDOW')


    def show(self):
        """Creates separate draw handlers for each rectangle."""
        for i, vertices in enumerate(self.ver_divisions):
            self.UI_handles.append(self.draw(self.ui_callback, (i, vertices)))
        self.Text_handle = self.draw(self.text_callback)

    def get_rectangle_color(self, index):
        """Gets the correct color for the rectangle based on its state."""
        if index == self.active_index:
            return bpy.context.preferences.addons[__package__].preferences.active_color
        elif index == self.active_mouse_index:
            return bpy.context.preferences.addons[__package__].preferences.mouse_highlight_color
        else:
            return bpy.context.preferences.addons[__package__].preferences.background_color
