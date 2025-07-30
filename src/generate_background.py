"""Generate AI-enhanced images for each image in the output directory."""
import torch
from diffusers import AutoPipelineForInpainting
from PIL import Image, ImageFilter
import os
import json
import argparse

def initalize_diffuser(device: str) -> AutoPipelineForInpainting:
    """Initialize the diffusion model.

    Args:
        device: cpu or cuda (if available).
    
    Returns:
        The diffusion model.
    """
    if device == "cuda":
        pipe = AutoPipelineForInpainting.from_pretrained(
            "diffusers/stable-diffusion-xl-1.0-inpainting-0.1", 
            torch_dtype=torch.float16, variant="fp16"
        ).to(device)
    else:
        pipe = AutoPipelineForInpainting.from_pretrained(
            "diffusers/stable-diffusion-xl-1.0-inpainting-0.1"
        ).to(device)
    return pipe

def generate_background(image_file: str, 
                    mask_file: str, 
                    output_path: str, 
                    prompt: str, 
                    negative_prompt: str,
                    device: str, 
                    pipe: AutoPipelineForInpainting,
                    object_names: tuple[str, str] = None) -> None:
    """ Generate and save an enhanced image using a diffusion model for a given image and mask.
    
    Args:
        image_file: The path to the image file.
        mask_file: The path to the mask file corresponding to the image.
        output_path: The path to save the enhanced image.
        prompt: The prompt to generate the enhanced image.
        negative_prompt: The negative prompt to avoid certain features in the generated image.
        device: cpu or cuda (if available).
        pipe: The diffusion model.
        object_names: Optional tuple of (object1, object2) names to add to the prompt.
    """
    # Enhance prompt with object information if provided
    if object_names:
        object1, object2 = object_names
        prompt = f"{prompt}. Do not modify the main objects in the scene: {object1} and {object2}."
    # Open both image and mask
    image = Image.open(image_file).convert("RGB")
    mask = Image.open(mask_file).convert("L")
    mask = mask.filter(ImageFilter.GaussianBlur(radius=2))
    mask = mask.point(lambda x: 0 if x < 200 else 255)
    # Use a generator
    generator = torch.Generator(device=device).manual_seed(42)
    # Perform inpainting
    output_image = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        image=image,
        mask_image=mask,
        guidance_scale=5,
        num_inference_steps=20,
        strength=0.9,
        generator=generator
    ).images[0]
    filename = os.path.basename(image_file)
    output_image.save(os.path.join(output_path, filename))

def main(prompt: str, negative_prompt: str, device: str) -> None:
    """Generate enhanced images for each image in the output directory.
    
    Args: 
        prompt: The prompt to generate the enhanced image.
        negative_prompt: The negative prompt to avoid certain features in the generated image.
        device: cpu or cuda (if available).
    """
    pipe = initalize_diffuser(device)
    # Load config information
    with open('config.json', 'r') as f:
        config = json.load(f)
    output_dir = config['output_image_dir']
    masks_dir = config['masks_dir']
    enhanced_image_dir = config['enhanced_image_dir']
    scene_dir = config['output_scene_dir']
    if not os.path.exists(enhanced_image_dir):
        os.makedirs(enhanced_image_dir)
    # Check if there are files directly in the output directory, if so, only process those files
    direct_files = [f for f in os.listdir(output_dir) if os.path.isfile(os.path.join(output_dir, f))]
    if direct_files:
        for filename in direct_files:
            image_file = os.path.join(output_dir, filename)
            relative_path = "."  # Direct files have no relative path
            mask_file = os.path.join(masks_dir, filename)
            # Extract object names from scene data
            scene_file = os.path.join(scene_dir, filename.replace('.png', '.json'))
            with open(scene_file, 'r') as f:
                scene_data = json.load(f)
            ground_name = scene_data.get('ground_object', {}).get('name')
            figure_name = scene_data.get('figure_object', {}).get('name')
            enhanced_path_dir = enhanced_image_dir
            if not os.path.exists(enhanced_path_dir):
                os.makedirs(enhanced_path_dir)
            generate_background(image_file, mask_file, enhanced_path_dir, prompt, negative_prompt, device, pipe, (ground_name, figure_name))
    else:
        for root, _, files in os.walk(output_dir):
            for filename in files:
                image_file = os.path.join(root, filename)
                relative_path = os.path.relpath(root, output_dir)
                mask_file = os.path.join(masks_dir, filename)
                # Extract object names from scene data
                scene_file = os.path.join(scene_dir, relative_path, filename.replace('.png', '.json'))
                with open(scene_file, 'r') as f:
                    scene_data = json.load(f)
                ground_name = scene_data.get('ground_object', {}).get('name')
                figure_name = scene_data.get('figure_object', {}).get('name')
                enhanced_path_dir = os.path.join(enhanced_image_dir, relative_path)
                if not os.path.exists(enhanced_path_dir):
                    os.makedirs(enhanced_path_dir)
                generate_background(image_file, mask_file, enhanced_path_dir, prompt, negative_prompt, device, pipe, (ground_name, figure_name))

if __name__ == '__main__':
    # Set up argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--prompt', 
                       type=str, 
                       required=True,
                       help='The prompt to generate the enhanced image')
    parser.add_argument('--negative_prompt', 
                       type=str, 
                       default="",
                       help='The negative prompt to avoid certain features in the generated image')
    parser.add_argument('--device', 
                       type=str, 
                       choices=['cpu', 'cuda', 'auto'],
                       default='auto',
                       help='Device to use for inference (cpu, cuda, or auto)')
    args = parser.parse_args()
    # Determine device
    if args.device == 'auto':
        if torch.cuda.is_available():
            device = "cuda"
            print("CUDA is available. Using GPU.")
        else:
            print("CUDA is not available. Using CPU.")
            device = "cpu"
    else:
        device = args.device
    # Run main function with parsed arguments
    main(args.prompt, args.negative_prompt, device)
    