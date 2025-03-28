"""Render scenes with Blender."""
import argparse
import copy
import json
import math
import random
import os
import sys
from typing import Any, Dict, List, Mapping
from render_objaverse import render_scene_3drf

INSIDE_BLENDER = True
try:
    import bpy
    from mathutils import Vector
except ImportError as e:
    print('''WARNING: Not running inside Blender.
          Some functionality may not be available.''', e)
    INSIDE_BLENDER = False
if INSIDE_BLENDER:
    try:
        import utils
    except ImportError as e:
        print(
            '''ERROR: Running render_images.py from Blender and cannot import utils.py.
            You may need to add a .pth file to the site-packages of Blender's bundled python with a command like this:
            echo $PWD >> $BLENDER/$VERSION/python/lib/python3.5/site-packages/psy3dr.pth
            Where $BLENDER is the directory where Blender is installed, and $VERSION is your Blender version (such as 2.78).''',
            e
        )
        sys.exit(1)
DIR = os.path.dirname(os.path.realpath(__file__))

# List of directions
directions = ['front', 'right', 'behind', 'left']

def parse_args(argv: str = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument string to parse.

    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser()
    # objects settings
    parser.add_argument('--objects', type=str, nargs='+', default=None,
                        help='List of object names to render. If not specified, all available objects will be used.')
    parser.add_argument('--render-random', action='store_true', default=False,
                        help='If set, render scenes with random rotations and positions.')
    parser.add_argument('--max-images', type=int, default=1, 
                        help='Maximum number of images to render for each object pair and direction.')
    parser.add_argument('--distance-between-objects', type=float, default=3, 
                        help='Distance between objects (in meters) between the objects centers.')
    parser.add_argument('--object1-rotation', type=float, default=0,
                        help='Rotation angle (in degrees) for the first object in the scene.')
    parser.add_argument('--object2-rotation', type=float, default=0,
                        help='Rotation angle (in degrees) for the second object in the scene.')
    parser.add_argument('--direction', default='front', choices=['left', 'right', 'behind', 'front'],
                        help='Relative direction of the second object with respect to the first object.')
    # camera settings
    parser.add_argument('--max-camera-configs', type=int, default=1,
                        help='Maximum number of camera configurations to render.')
    parser.add_argument('--camera-tilt', type=float, default=None,
                        help='Tilt (vertical) angle (in degrees) for the camera.')
    parser.add_argument('--camera-pan', type=float, default=None,
                        help='Pan (horizontal) angle (in degrees) for the camera.')
    parser.add_argument('--camera-height', type=float, default=None,
                        help='Height (in meters) of the camera in the scene.')
    parser.add_argument('--camera-focal-length', type=float, default=None,
                        help='Focal length (in millimeters) of the camera lens.')
    # return parsed arguments
    return parser.parse_args(argv)

def generate_camera_configs(max_configs: int) -> List[Dict[str, Any]]:
    """Generate a list of camera configurations.

    Args:
        args: Parsed arguments.

    Returns:
        A list of dictionaries with camera configurations.
    """
    camera_configs = []
    for tilt in [85, 90, 95]:
        for pan in [40, 45, 50]:
            for height in [0.5, 1, 1.5]:
                for focal_length in [50, 60, 70]:
                    camera_configs.append({
                        'tilt': tilt,
                        'pan': pan,
                        'height': height,
                        'focal_length': focal_length
                    })
    random.seed(42)
    random.shuffle(camera_configs)
    return camera_configs[:max_configs]

def candidate_objects_with_rotations(obj: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    """Generate candidate objects with rotations.

    Args:
        obj: Object to generate candidates for.

    Returns:
        List of object configurations with rotations.
    """
    default_orientation = obj['default_orientation']
    if default_orientation:
        ret_objs = list()
        for i, rotate_direction in enumerate([0, math.pi / 2, math.pi, 3 * math.pi / 2]):
            ret_obj = copy.deepcopy(obj)
            ret_obj['rotation'] = rotate_direction
            ret_obj['orientation'] = directions[(directions.index(default_orientation) + i) % 4]
            ret_objs.append(ret_obj)
        return ret_objs
    else:
        ret_obj = copy.deepcopy(obj)
        ret_obj['rotation'] = 0
        ret_obj['orientation'] = None
        return [ret_obj]
    
def render_random_scenes(args: argparse.Namespace, 
                        obj_names: List[str], 
                        properties: Mapping[str, Any], 
                        camera_configs: List[Dict[str, Any]], 
                        config: Dict[str, Any], 
                        max_images: int, 
                        prefix: str) -> None:
    """
    Renders a variety of random scenes given objects and saving the scenes to files.

    Args:
        args: Parsed arguments.
        obj_names: List of object names to be used in the scenes.
        properties: Dictionary mapping object names to their properties.
        camera_configs: List of camera configurations to render.
        config: Config file for the scenes.
        img_template: Template string for image file paths.
        scene_template: Template string for scene file paths.

    Returns:
        None
    """
    # Generate all possible combinations of objects
    object_combinations = []
    for i, obj_i in enumerate(obj_names):
        for j, obj_j in enumerate(obj_names):
            if i < j:
                obj_i_with_rotation = candidate_objects_with_rotations(properties[obj_i])
                obj_j_with_rotation = candidate_objects_with_rotations(properties[obj_j]) 
                scene_combinations = []
                # Create a shuffled list of direction combinations
                for direction in directions:
                    for obj_i_r in obj_i_with_rotation:
                        for obj_j_r in obj_j_with_rotation:
                            scene_combinations.append((obj_i_r, obj_j_r, direction))
                scenes_by_directions = {}
                for scene in scene_combinations:
                    if scene[2] not in scenes_by_directions:
                        scenes_by_directions[scene[2]] = []
                    if len(scenes_by_directions[scene[2]]) < max_images:
                        scenes_by_directions[scene[2]].append(scene)
                filtered_scenes = []
                for direction in directions:
                    for scene in scenes_by_directions[direction]:
                        for camera_config in camera_configs:
                            filtered_scenes.append((*scene, camera_config))
                object_combinations.append((obj_i, obj_j, filtered_scenes))
    # Render scenes for each combination
    image_count = 0
    for obj_i, obj_j, scene_combinations in object_combinations:
        # Create a top-level directory for this object pair
        overall_combination_prefix = f"{obj_i}_{obj_j}"
        overall_combination_images = os.path.join(config['output_image_dir'], overall_combination_prefix)
        overall_combination_scenes = os.path.join(config['output_scene_dir'], overall_combination_prefix)
        if not os.path.isdir(overall_combination_images):
            os.makedirs(overall_combination_images)
        if not os.path.isdir(overall_combination_scenes):
            os.makedirs(overall_combination_scenes)
        for obj_i_r, obj_j_r, direction, camera_config in scene_combinations:
            # Create a subdirectory for each direction inside the main combination directory
            direction_dir_images = os.path.join(overall_combination_images, f"{obj_i}_{obj_j}_{direction}")
            direction_dir_scenes = os.path.join(overall_combination_scenes, f"{obj_i}_{obj_j}_{direction}")
            if not os.path.isdir(direction_dir_images):
                os.makedirs(direction_dir_images)
            if not os.path.isdir(direction_dir_scenes):
                os.makedirs(direction_dir_scenes)
            img_template_comb = os.path.join(direction_dir_images, prefix + '%06d.png')
            scene_template_comb = os.path.join(direction_dir_scenes, prefix + '%06d.json')
            img_path = img_template_comb % image_count
            scene_path = scene_template_comb % image_count
            print(f"{obj_i_r}\n{obj_j_r}\n{direction}")
            # Generate a random camera setting for each image
            if all([args.camera_tilt, args.camera_pan, args.camera_height, args.camera_focal_length]):
                camera_settings = {
                    'tilt': args.camera_tilt,
                    'pan': args.camera_pan,
                    'height': args.camera_height,
                    'focal_length': args.camera_focal_length
                }
            else:
                camera_settings = camera_config
            render_scene_3drf(args, config, camera_settings, properties, image_count, img_path, scene_path, (obj_i_r, obj_j_r), direction)
            image_count += 1

def main(args: argparse.Namespace) -> None:
    """
    Render scenes based on the provided arguments and configurations.
    
    Args:
        args: Command-line arguments for rendering scenes.
    """

    # load the config file
    with open(os.path.join(DIR, 'config.json'), 'r') as file:
        config = json.load(file)
    prefix = config['filename_prefix'] + '_'
    img_template = prefix + '%06d.png'
    scene_template = prefix + '%06d.json'
    img_template = os.path.join(config['output_image_dir'], img_template)
    scene_template = os.path.join(config['output_scene_dir'], scene_template)
    config['output_image_dir'] = os.path.abspath(os.path.join(DIR, config['output_image_dir']))
    config['output_scene_dir'] = os.path.abspath(os.path.join(DIR, config['output_scene_dir']))
    config['masks_dir'] = os.path.abspath(os.path.join(DIR, config['masks_dir']))
    if not os.path.isdir(config['output_image_dir']):
        os.makedirs(config['output_image_dir'])
    if not os.path.isdir(config['output_scene_dir']):
        os.makedirs(config['output_scene_dir'])
    if not os.path.isdir(config['masks_dir']):
        os.makedirs(config['masks_dir'])
    with open(config['properties_json'], 'r') as f:
        properties = json.load(f)
    if args.objects is None:
        obj_names = list(sorted(properties.keys()))
    else:
        obj_names = args.objects
    if args.render_random:
        camera_configs = generate_camera_configs(args.max_camera_configs)
        render_random_scenes(args, obj_names, properties, camera_configs, config, args.max_images, prefix)
    else:
        img_path = os.path.join(config['output_image_dir'], prefix + '.png')
        scene_path = os.path.join(config['output_scene_dir'], prefix + '.json')
        directions = ["front", "right", "behind", "left"]
        assert len(obj_names) == 2
        ground_name, figure_name = obj_names
        ground = properties[ground_name]
        figure = properties[figure_name]
        ground['rotation'] = math.radians(args.object1_rotation if args.object1_rotation is not None else 0)
        figure['rotation'] = math.radians(args.object2_rotation if args.object2_rotation is not None else 0)
        if ground['default_orientation']:
            ground['orientation'] = directions[(directions.index(properties[ground_name]['default_orientation']) + round(args.object1_rotation / 90)) % 4]
        else:
            ground['orientation'] = None
        if figure['default_orientation']:
            figure['orientation'] = directions[(directions.index(properties[figure_name]['default_orientation']) + round(args.object2_rotation / 90)) % 4]
        else:
            figure['orientation'] = None
        direction = args.direction
        camera_settings = {
            'tilt': args.camera_tilt,
            'pan': args.camera_pan,
            'height': args.camera_height,
            'focal_length': args.camera_focal_length
        }
        render_scene_3drf(args, config, camera_settings, properties, 0, img_path, scene_path, (ground, figure), direction)

if __name__ == '__main__':
    if INSIDE_BLENDER:
        # Run normally
        argv = utils.extract_args()
        args = parse_args(argv)
        main(args)
    elif '--help' in sys.argv or '-h' in sys.argv:
        parse_args('--help')
    else:
        print(
            '''ERROR: This script is intended to be run from Blender like this:
            blender --background --python render_scene.py -- [args]
            You can also run as a standalone python script to view all arguments like this:
            python render_scene.py --help'''
        )
        