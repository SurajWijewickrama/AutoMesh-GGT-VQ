import bpy
import bmesh
import json
import os
import glob
import math
import base64

def clear_scene():
    """Deletes all objects in the Blender scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def import_glb(filepath):
    """Imports a GLB file into Blender."""
    bpy.ops.import_scene.gltf(filepath=filepath)

def merge_all_meshes():
    """Merges all mesh objects in the scene into a single mesh."""
    bpy.ops.object.select_all(action='DESELECT')
    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    if not mesh_objects:
        print("No mesh objects to merge.")
        return None
    bpy.context.view_layer.objects.active = mesh_objects[0]
    for obj in mesh_objects:
        obj.select_set(True)
    bpy.ops.object.join()
    return bpy.context.view_layer.objects.active

def reduce_vertices(obj, target_vertex_count):
    """
    Reduces the number of vertices in the mesh object to the target count by merging vertices.
    """
    if obj.type != 'MESH':
        raise TypeError("The provided object is not a mesh.")
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type="VERT")
    bpy.ops.mesh.select_all(action='DESELECT')
    
    bm = bmesh.from_edit_mesh(obj.data)
    initial_vertex_count = len(bm.verts)
    
    if initial_vertex_count <= target_vertex_count:
        print(f"Vertex count ({initial_vertex_count}) is within target ({target_vertex_count}).")
        bpy.ops.object.mode_set(mode='OBJECT')
        return
    
    decimate_ratio = target_vertex_count / initial_vertex_count
    bpy.ops.object.mode_set(mode='OBJECT')
    
    decimate_mod = obj.modifiers.new(name="Decimate", type='DECIMATE')
    decimate_mod.ratio = decimate_ratio
    decimate_mod.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=decimate_mod.name)
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.0001)
    
    bm = bmesh.from_edit_mesh(obj.data)
    final_vertex_count = len(bm.verts)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    print(f"Reduced vertices from {initial_vertex_count} to {final_vertex_count}.")

def remove_textures(obj):
    """
    Removes image texture nodes from the object's materials.
    """
    if obj.data.materials:
        for mat in obj.data.materials:
            if mat.use_nodes and mat.node_tree:
                nodes = mat.node_tree.nodes
                for node in list(nodes):
                    if node.type == 'TEX_IMAGE':
                        nodes.remove(node)
                if hasattr(mat, 'diffuse_color'):
                    mat.diffuse_color = (1, 1, 1, 1)
    else:
        print("No materials found to process.")

def add_plane_and_light():
    """
    Adds a ground plane and a light source to the scene.
    """
    scene = bpy.context.scene
    
    # Add a ground plane (positioned slightly below the object)
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, -10, 0))
    plane = bpy.context.active_object
    plane.name = "Ground_Plane"
    mat = bpy.data.materials.new(name="Plane_Mat")
    # For a black background in the plane, set diffuse_color accordingly:
    mat.diffuse_color = (0, 0, 0, 1)  
    plane.data.materials.append(mat)
    
    # Add a sun light
    light_data = bpy.data.lights.new(name="Sun", type='SUN')
    light_obj = bpy.data.objects.new(name="Sun", object_data=light_data)
    bpy.context.collection.objects.link(light_obj)
    light_obj.location = (5, 5, 10)
    
    # Set a target for the light (optional)
    constraint = light_obj.constraints.new(type="TRACK_TO")
    empty_target = bpy.data.objects.new("LightTarget", None)
    empty_target.location = (0, 0, 0)
    bpy.context.collection.objects.link(empty_target)
    constraint.target = empty_target
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'
    
    return plane, light_obj

def setup_camera(location):
    """
    Sets up a camera at the given location and points it toward the origin.
    Returns the camera and its target.
    """
    cam_data = bpy.data.cameras.new(name="Camera")
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    cam_obj.location = location
    
    target = bpy.data.objects.new("Target", None)
    target.location = (0, 0, 0)
    bpy.context.collection.objects.link(target)
    
    constraint = cam_obj.constraints.new(type="TRACK_TO")
    constraint.target = target
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'
    
    return cam_obj, target

def render_image(output_dir, base_name, angle, distance=5, height=2):
    """
    Renders an image from a specific angle and saves it to output_dir.
    """
    scene = bpy.context.scene
    original_filepath = scene.render.filepath
    
    rad = math.radians(angle)
    x = distance * math.cos(rad)
    y = distance * math.sin(rad)
    z = height
    location = (x, y, z)
    
    cam_obj, target = setup_camera(location)
    scene.camera = cam_obj
    bpy.context.view_layer.update()
    
    image_path = os.path.join(output_dir, f"{base_name}_{angle}.png")
    scene.render.filepath = image_path
    bpy.ops.render.render(write_still=True)
    
    bpy.data.objects.remove(cam_obj, do_unlink=True)
    bpy.data.objects.remove(target, do_unlink=True)
    
    scene.render.filepath = original_filepath
    print(f"Rendered image saved as {image_path}")

def export_to_json(obj, output_filepath):
    """
    Exports the mesh data of the object to a JSON file.
    """
    mesh = obj.data
    mesh.calc_loop_triangles()
    
    data = {
        "n": "airplane",  # hard-coded 'name'
        "l": [round(obj.location.x, 4), round(obj.location.y, 4), round(obj.location.z, 4)],
        "r": [round(obj.rotation_euler.x, 4), round(obj.rotation_euler.y, 4), round(obj.rotation_euler.z, 4)],
        "s": [round(obj.scale.x, 4), round(obj.scale.y, 4), round(obj.scale.z, 4)],
        "v": [],
        "e": [],
        "f": [],
    }
    
    obj_matrix_world = obj.matrix_world
    for vert in obj.data.vertices:
        world_coord = obj_matrix_world @ vert.co
        data["v"].append([round(world_coord.x, 4), round(world_coord.y, 4), round(world_coord.z, 4)])
    
    for edge in obj.data.edges:
        data["e"].append([edge.vertices[0], edge.vertices[1]])
    
    for face in obj.data.polygons:
        data["f"].append(list(face.vertices))
    
    with open(output_filepath, 'w') as f:
        json.dump(data, f, indent=4)
    
    print(f"Exported mesh JSON to {output_filepath}")

def process_glb_files(input_folder, output_folder, target_vertex_count, render_angle=45):
    
    os.makedirs(output_folder, exist_ok=True)
    glb_files = glob.glob(os.path.join(input_folder, "*.glb"))
    
    if not glb_files:
        print("No GLB files found in the specified folder.")
        return
    
    for glb_file in glb_files:
        print(f"Processing {glb_file}...")
        clear_scene()
        import_glb(glb_file)
        
        merged_obj = merge_all_meshes()
        if not merged_obj:
            print(f"No meshes found in {glb_file}, skipping...")
            continue
        
        reduce_vertices(merged_obj, target_vertex_count)
        remove_textures(merged_obj)
        add_plane_and_light() # adding a plane and light in the scene so the features are more visible for captioning 
        
        base_name = os.path.splitext(os.path.basename(glb_file))[0]
        # Create a dedicated folder for this models img and json text
        model_folder = os.path.join(output_folder, base_name)
        os.makedirs(model_folder, exist_ok=True)
        
        # Render an image from a specified angle (author can add more angles if multiple images are neededS needed)
        render_image(model_folder, base_name, render_angle)
        
        # Export mesh data as JSON
        json_path = os.path.join(model_folder, f"{base_name}.json")
        export_to_json(merged_obj, json_path)

input_folder = "D://Studies//FinalYear//FYP//3D datasets//shapenet-sample"  # Folder containing GLB files
output_folder = "D://Studies//FinalYear//FYP//3D datasets//processed_models"       # Folder to save model outputs
target_vertices = 2000  # Target vertex count
render_angle = 45       # Angle for rendering the image

process_glb_files(input_folder, output_folder, target_vertices, render_angle)
