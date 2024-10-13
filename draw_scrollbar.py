from .draw_menu import UIDraw
import gpu
from gpu_extras.batch import batch_for_shader
class ScrollBar:
    def __init__(self, draw_ui: UIDraw):
        self.draw_ui = draw_ui
        self.position = 0
        self.is_scrollbar_active = False
        self.is_scrollcol_active = False
        
    def create_scrollbar(self) -> None:
        """
        Create a scrollbar for the UI based on the menu dimensions and item count.
        """
        x = self.draw_ui.cursor_x + self.draw_ui.pref.ui_width
        y = self.draw_ui.cursor_y

        scroll_width = 20
        total_height = self.draw_ui.pref.ui_hight * self.draw_ui.parts
        scrollbar_height = self.calculate_scrollbar_dimensions(
            total_height, total_items=len(self.draw_ui.options), items_shown=self.draw_ui.parts
        )
        self.scroll_increment = self.draw_ui.pref.ui_hight * self.draw_ui.parts / len(self.draw_ui.options)
        self.scrollcol_vertices = [ 
            (x + scroll_width, y),
            (x, y),
            (x + scroll_width, y - (self.draw_ui.pref.ui_hight*self.draw_ui.parts)),
            (x, y - (self.draw_ui.pref.ui_hight*self.draw_ui.parts)),
        ]
        self.scrollbar_vertices = [
            (x + scroll_width, y),
            (x, y),
            (x + scroll_width, y - scrollbar_height),
            (x, y - scrollbar_height),
        ]

    def move_scrollbar(self, up: bool = False) -> None:
        """Move the scrollbar up or down by one item's height."""
        for i in range(len(self.scrollbar_vertices)):
            self.scrollbar_vertices[i] = (
                self.scrollbar_vertices[i][0],
                self.scrollbar_vertices[i][1] + self.scroll_increment if up else self.scrollbar_vertices[i][1] - self.scroll_increment
            )
        self.position += 1 if up else -1

    def update_scroll(self, current_mouse_y: int) -> None:
        """Update the scrollbar position based on mouse movement."""
        middle_pos = (self.scrollbar_vertices[0][1]+self.scrollbar_vertices[2][1])/2
        delta = middle_pos-current_mouse_y
        scroll_amount_in_items = int(delta / self.scroll_increment)
        for _ in range(abs(scroll_amount_in_items)):
            if scroll_amount_in_items > 0:
                self.draw_ui.increment_text_down()
            else:
                self.draw_ui.increment_text_up()

    def calculate_scrollbar_dimensions(self,menu_height, total_items, items_shown):
        """
        Calculate the width and height of a scrollbar based on menu dimensions and item count.
        
        Args:
            menu_height (int): Height of the menu in pixels.
            total_items (int): Total number of items.
            items_shown (int): Number of items shown at a time.
        
        Returns:
            tuple: (scrollbar_width, scrollbar_height)
        """
        # Calculate total height required for all items
        item_height = menu_height / items_shown
        total_content_height = item_height * total_items

        # Determine visible area height (same as menu height)
        visible_area_height = menu_height

        # Calculate scrollbar height
        if total_content_height <= visible_area_height:
            # If all content fits, set scrollbar height to 0
            scrollbar_height = 0
        else:
            # Calculate proportional height based on visible area
            scrollbar_height = visible_area_height * (visible_area_height / total_content_height)

        return scrollbar_height

    def get_scroll_color(self, is_scrollbar = False):
        if is_scrollbar:
            if self.is_scrollbar_active:
                return self.draw_ui.pref.scrollbar_active_color
            return self.draw_ui.pref.scrollbar_color
        else:
            return self.draw_ui.pref.scrollcol_color

    def scroll_col_callback(self, _, context):
        gpu.state.blend_set('ALPHA')  # Enable alpha blending
        indices = ((0, 1, 2), (2, 1, 3))
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {"pos": self.scrollcol_vertices}, indices=indices)
        shader.uniform_float("color", self.get_scroll_color())
        batch.draw(shader)

    def scroll_bar_callback(self, _, context):
        gpu.state.blend_set('ALPHA')  # Enable alpha blending
        indices = ((0, 1, 2), (2, 1, 3))
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {"pos": self.scrollbar_vertices}, indices=indices)
        shader.uniform_float("color", self.get_scroll_color(True))
        batch.draw(shader)

