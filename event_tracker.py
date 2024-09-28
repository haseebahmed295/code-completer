
import bpy
class EventTracker:
    def __init__(self, draw_ui) -> None:
        self.draw = draw_ui
        self._mouse_pos = (0, 0)
        self.keys_items = [34,35,67,66]

    def disable_keys(self):
        for i in self.keys_items:
            bpy.data.window_managers['WinMan'].keyconfigs['Blender user'].keymaps['Text'].keymap_items[i].active = False
        
    def enable_keys(self):
        for i in self.keys_items:
            bpy.data.window_managers['WinMan'].keyconfigs['Blender user'].keymaps['Text'].keymap_items[i].active = True

    def update_mouse(self):
        for i, vertices in enumerate(self.draw.ver_divisions):
            # print(f"mouse pos:({self.mouse_pos}) in rectangle {self.draw.ver_divisions[i]} is in {self.is_point_inside_rectangle(vertices, self.mouse_pos)}")
            if self.is_point_inside_rectangle(vertices, self.mouse_pos):
                self.draw.active_mouse_index = i
                self.redraw()
                break
        else:
            self.draw.active_mouse_index = -1
            self.redraw()
            
    def increment_text(self , up = True):
        if up:
            self.draw.active_index = self.draw.active_index - 1
        else:  
            self.draw.active_index = self.draw.active_index + 1
        self.redraw()
    def scroll(self, event , mouse_pos):
        if self.is_point_inside_rectangle(self.draw.vertices, mouse_pos):
            if event.type == 'WHEELUPMOUSE':
                self.draw.increment_text_up()
            elif event.type == 'WHEELDOWNMOUSE':
                self.draw.incremet_text_down()
            self.redraw()
            return False
        else:
            return True
    @property
    def mouse_pos(self):
        return self._mouse_pos

    @mouse_pos.setter
    def mouse_pos(self, value):
        self._mouse_pos = value
        self.update_mouse()

    @staticmethod
    def redraw():
        for area in bpy.context.screen.areas:
            if area.type == 'TEXT_EDITOR':
                area.tag_redraw()
        

    @staticmethod
    def is_point_inside_rectangle(vertices, point):
        """
        Check if a point is inside a rectangle defined by four vertices.

        :param point: A tuple (x, y) representing the point to check.
        :param vertices: A tuple containing four vertices of the rectangle 
                        in the format ((x1, y1), (x2, y2), (x3, y3), (x4, y4)).
        :return: True if the point is inside the rectangle, False otherwise.
        """
        x, y = point
        # Unpack the vertices
        (x1, y1), (x2, y2), (x3, y3), (x4, y4) = vertices
        
        # Calculate the bounds of the rectangle
        min_x = min(x1, x2, x3, x4)
        max_x = max(x1, x2, x3, x4)
        min_y = min(y1, y2, y3, y4)
        max_y = max(y1, y2, y3, y4)

        # Check if the point is within the bounds
        return min_x <= x <= max_x and min_y <= y <= max_y
