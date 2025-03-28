"""Render a scene with two objects in Blender."""
import argparse
import json
import math
import os
import numpy as np
from typing import Any, Dict, List
import bpy
import bpy_extras
from mathutils import Vector

def extract_masks_3drf(output_path: str, output_file: str) -> None:
    """Render a masked image from the current scene and save it to disk.

    Args:
        output_path: Path to save the masked image.
        output_file: Output file name for the masked image.
    """
    # Set up compositing nodes
    bpy.context.scene.use_nodes = True
    bpy.context.scene.render.film_transparent = True
    tree = bpy.context.scene.node_tree
    # Clear existing nodes
    for node in tree.nodes:
        tree.nodes.remove(node)
    # Add required nodes
    render_layers = tree.nodes.new('CompositorNodeRLayers')
    invert_node = tree.nodes.new('CompositorNodeInvert')
    composite = tree.nodes.new('CompositorNodeComposite')
    # Exclude plane from render layer
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.name.startswith('Plane'):
            obj.hide_render = True
    # Link nodes to invert alpha
    tree.links.new(render_layers.outputs['Alpha'], invert_node.inputs['Color'])
    tree.links.new(invert_node.outputs['Color'], composite.inputs['Image'])
    # Render and save
    render_args = bpy.context.scene.render
    render_args.filepath = os.path.join(output_path, output_file)
    bpy.ops.render.render(write_still=True)

def check_overlap(obj1: bpy.types.Object, obj2: bpy.types.Object, camera: bpy.types.Object, width: int, height: int, direction: str) -> bool:
    """Determine if two objects overlap in the rendered image by analyzing their intersecting pixels.

    Args:
        obj1: The first object in the scene.
        obj2: The second object in the scene.
        camera: The camera object used for rendering the scene.
        width: The width of the rendered image in pixels.
        height: The height of the rendered image in pixels.
        direction: The relative direction of the second object with respect to the first object.

    Returns:
        True if the two objects overlap, False otherwise.
        Note: "Overlap" is defined as follows:
              - If the smaller object is behind the bigger one and the intersecting pixels exceed 75% of the smaller object's pixels.
              - If the objects are side by side and there are any shared pixels between the objects. 
        This function is used to skip scenes where one object is blocked by the other or if they are too close to each other.
    """
    # Get all meshes in the scene
    bboxes = []
    obj_areas = []
    for obj in [obj1, obj2]:
        # project all bounding box corners into camera views
        coords_2d = [
            bpy_extras.object_utils.world_to_camera_view(bpy.context.scene, camera, obj.matrix_world @ Vector(corner))
            for corner in obj.bound_box
        ]
        us = [co.x for co in coords_2d]
        vs = [co.y for co in coords_2d]
        min_u, max_u = min(us), max(us)
        min_v, max_v = min(vs), max(vs)
        # convert normalized coordinates into pixel coordinates
        x_min = min_u * width
        x_max = max_u * width
        y_min = min_v * height
        y_max = max_v * height
        area = max(0, x_max - x_min) * max(0, y_max - y_min)
        bboxes.append((x_min, x_max, y_min, y_max, area))
        obj_areas.append(area)
    # calculate the intersection area
    x_min1, x_max1, y_min1, y_max1, _ = bboxes[0]
    x_min2, x_max2, y_min2, y_max2, _ = bboxes[1]
    inter_x = max(0, min(x_max1, x_max2) - max(x_min1, x_min2))
    inter_y = max(0, min(y_max1, y_max2) - max(y_min1, y_min2))
    intersection_area = inter_x * inter_y
    # check if the intersection area is non-zero for side-by-side cases
    if direction in ['left', 'right']:
        return intersection_area > 0
    # check if the intersection area is larger than 75% of the smaller object for front/behind cases
    if intersection_area >= 0.75 * min(obj_areas):
        return (obj_areas[0] < obj_areas[1] and direction == 'front') or (obj_areas[0] >= obj_areas[1] and direction == 'behind')
    return False

def add_objects_3drf(objects: List[Dict[str, Any]], config: Dict[str, Any], properties: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Add random objects to the current blender scene.

    Args:
        objects: Objects to add to the scene.
        config: Config file for the scene.
        properties: JSON data containing object properties.
    """
    # only support adding two objects for now
    assert len(objects) == 2
    # Scale up if objects are small or medium
    scale_factor = 1.0
    if properties[objects[0]['name']]['group'] == 'small':
        if properties[objects[1]['name']]['group'] == 'small':
            scale_factor = 3
        elif properties[objects[1]['name']]['group'] == 'medium':
            scale_factor = 1.8
    elif properties[objects[0]['name']]['group'] == 'medium':
        if properties[objects[1]['name']]['group'] == 'small':
            scale_factor = 1.8
        elif properties[objects[1]['name']]['group'] == 'medium':
            scale_factor = 1.3
    # Load the objects
    for obj in objects:
        object_name = obj['name']
        object_dir = os.path.join(config['shape_dir'], properties[object_name]['file'])
        # append the object to the scene
        bpy.ops.wm.append(directory=os.path.join(object_dir, 'Object'), filename=object_name)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        # ensure the object's center of rotation is correct
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='BOUNDS')
        # select object
        selected_obj = bpy.data.objects[object_name]
        # Deselect all objects and select the current one
        bpy.ops.object.select_all(action='DESELECT')
        selected_obj.select_set(True)
        bpy.context.view_layer.objects.active = selected_obj
        # set object position to the origin
        selected_obj.location = (0, 0, 0)
        # reshape
        scale = obj['scale'] * scale_factor
        bpy.ops.transform.resize(value=(scale, scale, scale))
        # align with base
        x, y = obj['position']
        bbox = []
        for corner in selected_obj.bound_box:
            world_corner = selected_obj.matrix_world @ Vector(corner)
            bbox.append(world_corner)
        min_z = min(v.z for v in bbox)
        bpy.ops.transform.translate(value=(x, y, -min_z))
        selected_obj.rotation_mode = 'XYZ'
        selected_obj.rotation_euler = [0, 0, obj['rotation']]
        # de-select all objects
        bpy.ops.object.select_all(action='DESELECT')

def render_scene_3drf(args: argparse.Namespace,
                    config: Dict[str, Any],
                    camera_settings: Dict[str, Any],
                    properties: Dict[str, Any],
                    index: int,
                    output_image: str,
                    output_scene: str,
                    objects: List[Dict[str, Any]],
                    direction: str) -> None:
    """Render a scene and save it to disk.

    Args:
        args: Global parsed arguments.
        config: Config file for the scene.
        camera_settings: Camera settings for the scene.
        properties: JSON data containing object properties.
        index: Index of the scene.
        output_image: Output image file path.
        output_scene: Output scene file path.
        objects: Configs for objects to add to the scene.
        direction: Direction of the second object to the first object (in relative frame).
    """
    intrinsic_directions = config['intrinsic_directions']
    caption_templates = config['caption_templates']
    # load the main blendfile and materials
    bpy.ops.wm.open_mainfile(filepath=config['base_scene_blendfile'])
    # use BLENDER_RENDER to render
    render_args = bpy.context.scene.render
    render_args.engine = 'CYCLES'
    render_args.filepath = output_image
    render_args.resolution_x = config['width']
    render_args.resolution_y = config['height']
    render_args.resolution_percentage = 100
    bpy.context.scene.cycles.tile_x = config['render_tile_size']
    bpy.context.scene.cycles.tile_y = config['render_tile_size']
    if config['use_gpu']:
        bpy.context.scene.cycles.device = 'GPU'
    # define scene structure
    scene_struct = {
        'image_index': index,
        'image_filename': os.path.basename(output_image)
    }
    # get ground and figure objects
    ground, figure = objects
    # put a helper plane on the ground for easier calculation of the directions
    bpy.ops.mesh.primitive_plane_add(size=5)
    plane = bpy.context.object
    # set up camera
    camera = bpy.data.objects['Camera']
    camera.rotation_euler = (math.radians(camera_settings['tilt']), 0, math.radians(camera_settings['pan']))
    camera.location[2] = camera_settings['height']
    camera.data.lens = camera_settings['focal_length']
    scene_struct['camera'] = camera_settings
    # calculate the directions in the scene
    plane_normal = plane.data.vertices[0].normal
    cam_behind = camera.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    cam_left = camera.matrix_world.to_quaternion() @ Vector((-1, 0, 0))
    plane_behind = (cam_behind - cam_behind.project(plane_normal)).normalized()
    plane_left = (cam_left - cam_left.project(plane_normal)).normalized()
    # delete the helper plane
    bpy.ops.object.delete()
    # All axis-aligned directions in the scene
    scene_directions = {
        'behind': tuple(plane_behind),
        'front': tuple(-plane_behind),
        'left': tuple(plane_left),
        'right': tuple(-plane_left),
    }
    # Calculate positions and add objects
    direction_vector = np.array(scene_directions[direction])[:2]
    normalized_direction = direction_vector / np.linalg.norm(direction_vector)
    ground['position'] = (-normalized_direction * (args.distance_between_objects / 2)).tolist()
    figure['position'] = (normalized_direction * (args.distance_between_objects / 2)).tolist()
    add_objects_3drf(objects, config, properties)
    # Set background color to light grey
    bpy.context.scene.world.use_nodes = True
    bg_node = bpy.context.scene.world.node_tree.nodes['Background']
    bg_node.inputs['Color'].default_value = (0.5, 0.5, 0.5, 1)
    # render the scene and dump the scene data structure
    while True:
        try:
            bpy.ops.render.render(write_still=True)
            break
        except Exception as e:
            print(e)
    # If overlap exists, remove the rendered image, and skip
    if check_overlap(bpy.data.objects[ground['name']], bpy.data.objects[figure['name']], camera, config['width'], config['height'], direction):
        print('\nOverlap detected, skipping...\n')
        os.remove(output_image)
        return
    # extract the masks
    extract_masks_3drf(config['masks_dir'] , os.path.basename(output_image))
    # save the scene data structure
    scene_struct['ground_object'] = {
        'name': ground['name'],
        'orientation': ground['orientation'],
        'rotation': ground['rotation'],
        'position': ground['position']
    }
    scene_struct['figure_object'] = {
        'name': figure['name'],
        'orientation': figure['orientation'],
        'rotation': figure['rotation'],
        'position': figure['position']
    }
    # generate the captions
    reversed_direction = {
        'behind': 'front',
        'front': 'behind',
        'left': 'right',
        'right': 'left',
    }
    scene_struct['translational_relation_caption'] = caption_templates['3d_translation'][direction].format(figure['name'], ground['name'])
    scene_struct['reflectional_relation_caption'] = caption_templates['3d_reflection'][direction].format(figure['name'], ground['name'])
    if ground['orientation']:
        scene_struct['ground_object']['intrinsic_relation'] = intrinsic_directions[ground['orientation']][direction]
        scene_struct['ground_object']['intrinsic_caption'] = caption_templates['3d_intrinsic'][scene_struct['ground_object']['intrinsic_relation']].format(ground['name'], figure['name'])
    if figure['orientation']:
        scene_struct['figure_object']['intrinsic_relation'] = intrinsic_directions[figure['orientation']][reversed_direction[direction]]
        scene_struct['figure_object']['intrinsic_caption'] = caption_templates['3d_intrinsic'][scene_struct['figure_object']['intrinsic_relation']].format(figure['name'], ground['name'])
    with open(output_scene, 'w') as f:
        json.dump(scene_struct, f, indent=2)
