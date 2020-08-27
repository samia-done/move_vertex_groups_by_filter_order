# Copyright (c) 2020 Samia
import re
import bpy
from bpy.types import Operator
from bpy.types import Panel, UIList

from .utils.bl_version_helpers import has_bl_major_version, get_bl_minor_version
from .utils.bl_context_wrappers import get_engine
from .utils.bl_str_wrappers import get_icon, get_menu


def make_annotations(cls):
    if has_bl_major_version(2) and get_bl_minor_version() < 80:
        return cls

    props = {k: v for k, v in cls.__dict__.items() if isinstance(v, tuple)}
    if props:
        if '__annotations__' not in cls.__dict__:
            setattr(cls, '__annotations__', {})
        annotations = cls.__dict__['__annotations__']
        for k, v in props.items():
            annotations[k] = v
            delattr(cls, k)
    return cls


@make_annotations
class MVGBF_ToolSettings(bpy.types.PropertyGroup):
    use_regex = bpy.props.BoolProperty(
        name="Enable Regular Expressions",
        description="Enable Regular Expressions.",
        default=False,
        options={'HIDDEN'},
    )


@make_annotations
class FilterItems(bpy.types.PropertyGroup):
    flt_flags = []
    flt_neworder = []


@make_annotations
class OBJECT_OT_vertex_groups_move_by_filter_order(Operator):
    bl_idname = "object.vertex_groups_move_by_filter_order"
    bl_label = "Move Vertex Groups by Filter Order"
    bl_description = "Moves the filtered list of vertex groups to the position of the active vertex group."
    bl_options = {'REGISTER', 'UNDO'}

    filter_items = bpy.props.PointerProperty(
        type=FilterItems,
        options={'HIDDEN'}
    )

    bitflag_filter_item = bpy.props.IntProperty(
        default=0,
        options={'HIDDEN'},
    )
    use_filter_sort_alpha = bpy.props.BoolProperty(
        default=False,
        options={'HIDDEN'},
    )
    use_filter_sort_reverse = bpy.props.BoolProperty(
        default=False,
        options={'HIDDEN'},
    )
    use_filter_invert = bpy.props.BoolProperty(
        default=False,
        options={'HIDDEN'},
    )

    # def __init__(self):
    #     pass

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type in {'MESH', 'LATTICE'} and context.object.vertex_groups

    # def invoke(self, context, event):
    #     return self.execute(context)

    def execute(self, context):
        if not len(self.filter_items.flt_flags) == 0:
            v_list = []
            bitflag = 0 if self.use_filter_invert else self.bitflag_filter_item

            for i, item in enumerate(self.filter_items.flt_flags):
                if item == bitflag:
                    if len(self.filter_items.flt_neworder) == 0:
                        v_list.append([i, context.object.vertex_groups.keys()[i], i])
                    else:
                        v_list.append([i, context.object.vertex_groups.keys()[i], self.filter_items.flt_neworder[i]])

            v_list.sort(key=lambda x: x[2], reverse=self.use_filter_sort_reverse)

            toIndex = context.object.vertex_groups.active_index

            for i, list_item in enumerate(v_list):
                context.object.vertex_groups.active_index = context.object.vertex_groups[list_item[1]].index
                nowIndex = context.object.vertex_groups.active_index

                if not toIndex - nowIndex == 0:
                    rangeCount = 0
                    if toIndex < nowIndex:
                        rangeCount = nowIndex - toIndex if i == 0 else nowIndex - toIndex - 1
                        direction = 'UP'
                    elif toIndex > nowIndex:
                        rangeCount = toIndex - nowIndex
                        direction = 'DOWN'
                    for j in range(rangeCount):
                        bpy.ops.object.vertex_group_move(direction=direction)
                toIndex = context.object.vertex_groups.active_index
        return {'FINISHED'}


class MESH_UL_sort_vertex_groups_list(UIList):
    @staticmethod
    def filter_items_by_regex(pattern, bitflag, items, propname='name', flags=None, reverse=False):
        # flags = flags if flags else [bitflag] * len(items)
        flags = flags if flags else [0] * len(items)

        try:
            compile = re.compile(pattern)
        except Exception as e:
            # 文字の入力途中や、正規表現の書式のエラーはすべてスルーする
            # print(e)
            return flags

        for i, item in enumerate(items):
            flags[i] = bitflag if re.search(compile, getattr(item, propname)) else 0
        return flags.reverse() if reverse else flags

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        vgroup = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.alignment = 'CENTER'
            layout.label(text=str(index))
            layout.alignment = 'EXPAND'
            layout.prop(vgroup, "name", text="", emboss=False, icon_value=icon)
            icon = 'LOCKED' if vgroup.lock_weight else 'UNLOCKED'
            layout.prop(vgroup, "lock_weight", text="", icon=get_icon(icon), emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=get_icon(icon))

    def draw_filter(self, context, layout):
        layout.separator()
        col = layout.column(align=True)
        row = col.row(align=True)
        row.alignment = 'EXPAND'
        row.prop(self, 'filter_name', text='')
        row.alignment = 'RIGHT'
        row.prop(context.scene.MVGBF_tool_settings, 'use_regex', text='.*', toggle=True)

        row.alignment = 'EXPAND'
        icon = 'ZOOM_OUT' if self.use_filter_invert else 'ZOOM_IN'
        row.prop(self, 'use_filter_invert', text='', icon=get_icon(icon))
        row.separator()
        icon = 'SORTALPHA'
        row.prop(self, "use_filter_sort_alpha", text="", icon=get_icon(icon))
        icon = 'TRIA_UP' if self.use_filter_sort_reverse else 'TRIA_DOWN'
        row.prop(self, "use_filter_sort_reverse", text="", icon=get_icon(icon))

        col = layout.column(align=True)
        row = col.row(align=True)

        row.prop(context.object.vertex_groups, "active_index")
        op = row.operator(OBJECT_OT_vertex_groups_move_by_filter_order.bl_idname, text="Move")  # type: OBJECT_OT_vertex_groups_move_by_filter_order
        op.bitflag_filter_item = self.bitflag_filter_item
        op.use_filter_sort_reverse = self.use_filter_sort_reverse
        op.use_filter_invert = self.use_filter_invert
        op.use_filter_sort_alpha = self.use_filter_sort_alpha
        op.filter_items.flt_flags[:], op.filter_items.flt_neworder[:] = self.filter_items(context, context.active_object, "vertex_groups")

    def filter_items(self, context, data, propname):
        flt_flags = []
        flt_neworder = []
        vgroups = getattr(data, propname)

        if self.filter_name:
            if context.scene.MVGBF_tool_settings.use_regex:
                # Filtering by Regular Expressions
                flt_flags = MESH_UL_sort_vertex_groups_list.filter_items_by_regex(self.filter_name,
                                                                                  self.bitflag_filter_item, vgroups,
                                                                                  "name")
            else:
                # Filtering by name
                flt_flags = bpy.types.UI_UL_list.filter_items_by_name(self.filter_name, self.bitflag_filter_item, vgroups,
                                                              "name")

        if not flt_flags:
            flt_flags = [self.bitflag_filter_item] * len(vgroups)

        # Reorder by name
        if self.use_filter_sort_alpha:
            flt_neworder = bpy.types.UI_UL_list.sort_items_by_name(vgroups, "name")

        return flt_flags, flt_neworder


class DATA_PT_sort_vertex_groups_list(Panel):
    bl_label = "Move Vertex Groups by Filter Order"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    # COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_GAME'}
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_GAME', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}

    @classmethod
    def poll(cls, context):
        engine = get_engine(context)
        obj = context.object
        return obj and obj.type in {'MESH', 'LATTICE'} and (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        ob = context.object
        group = ob.vertex_groups.active

        rows = 3
        if group:
            rows = 5

        row = layout.row()
        row.template_list("MESH_UL_sort_vertex_groups_list", "", ob, "vertex_groups", ob.vertex_groups, "active_index",
                          rows=rows)

        col = row.column(align=True)
        icon = get_icon('ZOOMIN')
        col.operator("object.vertex_group_add", icon=icon, text="")
        icon = get_icon('ZOOMOUT')
        props = col.operator("object.vertex_group_remove", icon=icon, text="")
        props.all_unlocked = props.all = False

        col.separator()

        icon = get_icon('DOWNARROW_HLT')
        col.menu(get_menu("MESH_MT_vertex_group_specials"), icon=icon, text="")
        if group:
            col.separator()
            col.operator("object.vertex_group_move", icon='TRIA_UP', text="").direction = 'UP'
            col.operator("object.vertex_group_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

        if ob.vertex_groups and (ob.mode == 'EDIT' or (
                ob.mode == 'WEIGHT_PAINT' and ob.type == 'MESH' and ob.data.use_paint_mask_vertex)):
            row = layout.row()

            sub = row.row(align=True)
            sub.operator("object.vertex_group_assign", text="Assign")
            sub.operator("object.vertex_group_remove_from", text="Remove")

            sub = row.row(align=True)
            sub.operator("object.vertex_group_select", text="Select")
            sub.operator("object.vertex_group_deselect", text="Deselect")

            layout.prop(context.tool_settings, "vertex_group_weight", text="Weight")
