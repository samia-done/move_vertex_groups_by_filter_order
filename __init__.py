# Copyright (c) 2020 Samia
import bpy
from .operator import OBJECT_OT_vertex_groups_move_by_filter_order, DATA_PT_sort_vertex_groups_list, \
    MESH_UL_sort_vertex_groups_list, MVGBF_ToolSettings, FilterItems

bl_info = {
    "name": "Move Vertex Groups by Filter Order",
    "author": "Samia",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "Properties > Data",
    "description": "Add a panel to move the list of vertex groups.",
    "warning": "Trying to sort dozens of vertex groups can take a long time and render Blender busy.",
    "support": "TESTING",
    "wiki_url": "",
    "tracker_url": "",
    "category": "User Interface"
}

classes = (
    # コレクションクラスのインポートの順番に注意
    FilterItems,
    MVGBF_ToolSettings,
    OBJECT_OT_vertex_groups_move_by_filter_order,
    DATA_PT_sort_vertex_groups_list,
    MESH_UL_sort_vertex_groups_list,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.MVGBF_tool_settings = bpy.props.PointerProperty(type=MVGBF_ToolSettings)


def unregister():
    del bpy.types.Scene.MVGBF_tool_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
