# import bpy

# for area in bpy.context.screen.areas:
#     if area.type == 'TEXT_EDITOR':
#         # Get the active space data for the Dope Sheet Editor
#         test = area.spaces
#         print("Found Dope Sheet Editor")
#         break
# else:
#     print("No Dope Sheet Editor found")

# # You can add similar logic for other editor types like TIMELINE, ACTION, etc.

# def get_widget_unit(context):
#     system = context.preferences.system
#     p = system.pixel_size
#     pd = p * system.dpi
#     return int((pd * 20 + 36) / 72 + (2 * (p - pd // 72)))

# wunits = get_widget_unit(context)
# line_height_dpi = (wunits * st.font_size) / 20
# line_height = int(line_height_dpi + 0.3 * line_height_dpi)
# print(line_height_dpi , line_height)


# def get_cw(st, lines):
#     for idx, line in enumerate(lines):
#         if len(line.body) > 1:
#             return st.region_location_from_cursor(idx, 1)[0] - st.region_location_from_cursor(0,0)




# x_offset = cw = get_cw(st ,  lines)
# if st.show_line_numbers:
#     x_offset += cw * (len(repr(len(lines))) + 2)
