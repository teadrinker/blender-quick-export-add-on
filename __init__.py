# teadrinker quick export
#
# * Export using short key CRTL-SHIFT-E to predefined directory
# * One-click export with "Export"-button in 3D window header
# * Settings and choosen directory is saved in a config file next to the blend file
# * Objects marked as "Disable Selection" will not be exported
#
# More info: https://github.com/teadrinker/blender-quick-export-add-on
#
# License: GPL
# https://www.gnu.org/licenses/gpl-3.0.html


bl_info = {
    "name": "teadrinker quick export",
    "version": (1, 2, 0),
    "blender": (4, 0, 0),
    "description": "Export using CRTL-SHIFT-E, settings are saved in a file next to .blend",
    "location": "View3D > Header",
    "doc_url": "https://github.com/teadrinker/blender-quick-export-add-on",
    "category": "Import-Export",
}

import os
import bpy
import re
import json

def load_cfg(path):
    with open(path) as f:
        data = json.load(f)
        return data
    return None
    
def save_cfg(path, dict):
    with open(path, 'w') as fp:
        json.dump(dict, fp,  indent=4)

def replace_caseinsensitive(old, new, str):
    return re.sub(re.escape(old), new, str, flags=re.IGNORECASE)

tea_quick_export_print_context = None
def console_print(*args, **kwargs):
    for a in tea_quick_export_print_context.screen.areas:
        if a.type == 'CONSOLE':
            c = {}
            c['area'] = a
            c['space_data'] = a.spaces.active
            c['region'] = a.regions[-1]
            c['window'] = tea_quick_export_print_context.window
            c['screen'] = tea_quick_export_print_context.screen
            s = " ".join([str(arg) for arg in args])
            for line in s.split("\n"):
                bpy.ops.console.scrollback_append(c, text=line)

class teadrinker_quick_export(bpy.types.Operator):
    """teadrinker quick export add-on"""
    bl_idname = "teadrinker.quick_export"
    bl_label = "teadrinker quick export"
    bl_options = {'REGISTER', 'UNDO'}

    out_format:        bpy.props.EnumProperty  (name='Format', items=[('obj', 'OBJ', ''), ('fbx', 'FBX', ''),('glb', 'glTF Binary (.glb)', ''),('gltf', 'glTF Separate (.gltf + .bin + textures)', '')], default = 'obj')
    out_dir:           bpy.props.StringProperty(name = "Output Directory", subtype = 'DIR_PATH',               default = '<PLEASE SET DIR!>')
    override_filename: bpy.props.StringProperty(name = "Override Filename", subtype = 'FILE_NAME',             default = '')
    name_from_selection:bpy.props.BoolProperty (name = "Filename from selection",                              default = False)
    selected_only:     bpy.props.BoolProperty  (name = "Export Selected Only",                                 default = False)
    obj_mat_names:     bpy.props.BoolProperty  (name = "Append Material Names (obj)",                          default = False)
    obj_merge_by_mat:  bpy.props.BoolProperty  (name = "Merge Objects (obj)",                                  default = False)
    obj_triangulate:   bpy.props.BoolProperty  (name = "Triangulate (obj)",                                    default = True)
    scale:             bpy.props.FloatProperty (name = "Scale (only obj/fbx)",                                 default = 1.0)
 
    def get_selected_object_name():
        if bpy.context.selected_objects:
            return bpy.context.selected_objects[0].name
        else:
            return "no selection"

    def execute(self, context):

        global tea_quick_export_print_context
        tea_quick_export_print_context = context

        blend_dir = bpy.path.abspath("//")
        blend_filename = bpy.path.basename(bpy.context.blend_data.filepath)

        if os.path.exists(blend_dir) and os.path.exists(os.path.join(blend_dir, blend_filename)):
            settings_fullpath = os.path.join(blend_dir, replace_caseinsensitive(".blend", " export settings.txt", blend_filename))

            if self.out_dir == '<PLEASE SET DIR!>' or self.out_dir == '' or self.out_dir == None:
                try:
                    cfg = load_cfg(settings_fullpath)
                    if cfg != None:
                        export_dir = cfg['dir']
                        export_dir_relative = cfg['relative']
                        if export_dir_relative:
                            export_dir = os.path.join(blend_dir, export_dir)
                        self.out_dir = os.path.abspath(export_dir)
                        self.out_format = cfg['out_format']
                        self.override_filename = cfg['override_filename']
                        self.name_from_selection = cfg['name_from_selection']
                        self.selected_only = cfg['selected_only']
                        self.obj_mat_names = cfg['obj_mat_names']
                        self.obj_merge_by_mat = cfg['obj_merge_by_mat']
                        self.obj_triangulate = cfg['obj_triangulate']
                        self.scale = cfg['scale']
                except: pass
            else:
                export_dir = self.out_dir
                export_dir_relative = False
                try:
                    export_dir = os.path.relpath(self.out_dir, blend_dir) # this fails on windows if .blend path and export path are on different drive letters
                    export_dir_relative = True
                except: pass

                save_cfg(settings_fullpath, { 'out_format' : self.out_format, 'scale' : self.scale, 'override_filename' : self.override_filename, 'name_from_selection' : self.name_from_selection, 'selected_only' : self.selected_only, 'obj_mat_names' : self.obj_mat_names, 'obj_merge_by_mat' : self.obj_merge_by_mat ,'obj_triangulate' : self.obj_triangulate ,'dir' : export_dir, 'relative' : export_dir_relative })
        else:
            console_print('teadrinker quick export: Warning, settings will not be saved')

            
        if self.out_dir == '<PLEASE SET DIR!>' or self.out_dir == '' or self.out_dir == None:
            self.out_dir = '<PLEASE SET DIR!>' 
            console_print('teadrinker quick export: Please set output dir')
            return {'FINISHED'}

        export_filename = self.override_filename if self.override_filename != '' else replace_caseinsensitive('.blend', '', blend_filename)
        if self.name_from_selection:
            sel_name = teadrinker_quick_export.get_selected_object_name()
            if sel_name != "no selection":
                export_filename = replace_caseinsensitive('.blend', '', sel_name)                
            else:
                console_print('teadrinker quick export: Warning, settings will not be saved')

        export_fullpath = os.path.join(self.out_dir, export_filename + "." + self.out_format)

        #console_print('blend_dir ' + blend_dir)
        #console_print('blend_filename ' + blend_filename)
        #console_print('out_dir ' + self.out_dir)
        #console_print('export_fullpath ' + export_fullpath)

        #with context.temp_override(**context.copy()):

        # if not self.name_from_selection:
        #     bpy.ops.object.select_all(action='SELECT') # this dont actually work?

        if self.out_format == 'obj':
            console_print('teadrinker quick export: Writing obj: ' + export_fullpath)
            bpy.ops.wm.obj_export(filepath=export_fullpath, global_scale=self.scale, check_existing=False, export_selected_objects=self.selected_only, export_triangulated_mesh=self.obj_triangulate, export_material_groups=(not self.obj_merge_by_mat) and self.obj_mat_names, export_object_groups=(not self.obj_merge_by_mat) and (not self.obj_mat_names)) # export_material_groups is same as old API group_by_material param? 
        elif self.out_format == 'fbx':
            console_print('teadrinker quick export: Writing fbx: ' + export_fullpath)
            bpy.ops.export_scene.fbx(filepath=export_fullpath, global_scale=self.scale, check_existing=False, use_selection=self.selected_only)
        elif self.out_format == 'glb':
            console_print('teadrinker quick export: Writing glb: ' + export_fullpath)
            bpy.ops.export_scene.gltf(filepath=export_fullpath,                         check_existing=False, use_selection=self.selected_only, export_format='GLB', export_apply=False) # WARNING: export_apply prevents exporting shape keys 
        elif self.out_format == 'gltf':
            console_print('teadrinker quick export: Writing gltf: ' + export_fullpath)
            bpy.ops.export_scene.gltf(filepath=export_fullpath,                         check_existing=False, use_selection=self.selected_only, export_format='GLTF_SEPARATE', export_apply=False) # WARNING: export_apply prevents exporting shape keys 
            # bpy.ops.export_scene.gltf(filepath=export_fullpath, export_format='GLTF_SEPARATE') 
        else:
            raise Exception('teadrinker quick export, no such format ' + self.out_format)

        # if not self.name_from_selection:
        #     bpy.ops.object.select_all(action='DESELECT')



        #obj options

        #check_existing=True, 
        #axis_forward='-Z', 
        #axis_up='Y', 
        #filter_glob="*.obj;*.mtl", 
        #use_selection=False, 
        #use_animation=False, 
        #use_mesh_modifiers=True, 
        #use_edges=True, 
        #use_smooth_groups=False, 
        #use_smooth_groups_bitflags=False, 
        #use_normals=True, use_uvs=True, 
        #use_materials=True, 
        #use_triangles=False, 
        #use_nurbs=False, 
        #use_vertex_groups=False, 
        #use_blen_objects=True, 
        #group_by_object=False, 
        #group_by_material=False, 
        #keep_vertex_order=False, 
        #global_scale=1, 
        #path_mode='AUTO')

        return {'FINISHED'}


# store keymaps here to access after registration
addon_keymaps = []


#VIEW3D_MT_object
#def menu_func(self, context):
#    self.layout.operator(teadrinker_quick_export.bl_idname)

def menu_func(self, context):
    self.layout.operator(teadrinker_quick_export.bl_idname, text='Export')

def register():
    bpy.utils.register_class(teadrinker_quick_export)
    #bpy.types.VIEW3D_MT_object.append(menu_func)
    bpy.types.VIEW3D_MT_editor_menus.append(menu_func)

    # handle the keymap
    wm = bpy.context.window_manager
    # Note that in background mode (no GUI available), keyconfigs are not available either,
    # so we have to check this to avoid nasty errors in background case.
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')
        #kmi = km.keymap_items.new(teadrinker_quick_export.bl_idname, 'S', 'PRESS', ctrl=True, alt=True) # now used for save incremental
        kmi = km.keymap_items.new(teadrinker_quick_export.bl_idname, 'E', 'PRESS', ctrl=True, shift=True) 
        #kmi.properties.total = 4
        kmi.properties.out_dir = '<PLEASE SET DIR!>'
        kmi.properties.out_format = 'obj'
        kmi.properties.override_filename = ''
        kmi.properties.scale = 1
        addon_keymaps.append((km, kmi))

def unregister():
    # Note: when unregistering, it's usually good practice to do it in reverse order you registered.
    # Can avoid strange issues like keymap still referring to operators already unregistered...
    # handle the keymap
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    bpy.utils.unregister_class(teadrinker_quick_export)
    #bpy.types.VIEW3D_MT_object.remove(menu_func)
    bpy.types.VIEW3D_MT_editor_menus.remove(menu_func)


if __name__ == "__main__":
    register()
