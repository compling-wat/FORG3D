"""Generate AI-enhanced images for each image in the output directory."""
import torch
from diffusers import AutoPipelineForInpainting
from PIL import Image
import os
import json
import sys

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
                    device: str, 
                    pipe: AutoPipelineForInpainting) -> None:
    """ Generate and save an enhanced image using a diffusion model for a given image and mask.
    
    Args:
        image_file: The path to the image file.
        mask_file: The path to the mask file corresponding to the image.
        output_path: The path to save the enhanced image.
        prompt: The prompt to generate the enhanced image.
        device: cpu or cuda (if available).
        pipe: The diffusion model.
    """
    # Open both image and mask
    image = Image.open(image_file).convert("RGB")
    mask = Image.open(mask_file).convert("L")
    mask = mask.point(lambda x: 0 if x < 254 else 255)
    # Use a generator
    generator = torch.Generator(device=device).manual_seed(42)
    # Perform inpainting
    output_image = pipe(
        prompt=prompt,
        image=image,
        mask_image=mask,
        guidance_scale=5,
        num_inference_steps=20,
        strength=0.9,
        generator=generator
    ).images[0]
    filename = os.path.basename(image_file)
    output_image.save(os.path.join(output_path, filename))

def main(prompt: str, device: str) -> None:
    """Generate enhanced images for each image in the output directory.
    
    Args: 
        prompt: The prompt to generate the enhanced image.
        device: cpu or cuda (if available).
    """
    pipe = initalize_diffuser(device)
    # Load config information
    with open('config.json', 'r') as f:
        config = json.load(f)
    output_dir = config['output_image_dir']
    masks_dir = config['masks_dir']
    enhanced_image_dir = config['enhanced_image_dir']
    if not os.path.exists(enhanced_image_dir):
        os.makedirs(enhanced_image_dir)
    # Generate enhanced images for each image in the output directory
    for root, _, files in os.walk(output_dir):
        for filename in files:
            image_file = os.path.join(root, filename)
            relative_path = os.path.relpath(root, output_dir)
            mask_file = os.path.join(masks_dir, filename)
            enhanced_path_dir = os.path.join(enhanced_image_dir, relative_path)
            if not os.path.exists(enhanced_path_dir):
                os.makedirs(enhanced_path_dir)
            generate_background(image_file, mask_file, enhanced_path_dir, prompt, device, pipe)

if __name__ == '__main__':
    # Check if CUDA is available
    if torch.cuda.is_available():
        device = "cuda"
    else:
        print("CUDA is not available. Using CPU.")
        device = "cpu"
    # Extract prompt
    prompt = sys.argv[-1] 
    main(prompt, device)
    