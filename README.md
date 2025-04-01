# FORG3D Rendering Tool

**FORG3D** _(Flexible Object Rendering for Generation of 3D Vision-Language Spatial Reasoning Datasets)_ is a **3D rendering tool** that takes any 2 Blender objects and renders them on a plane with customizable orientations, positions, distances, and camera angles.

## Setup

### Step 1: Clone the Repository

Clone this repository to your local machine:

```bash
git clone https://github.com/compling-wat/FORG3D.git
cd FORG3D
```

### Step 2: Install Blender 4.3

Download and install **[Blender 4.3](https://www.blender.org/download/)**.

### Step 3: Set Up the Environment

1. Locate where Blender 4.3 is installed:
   ```bash
   which/where blender
   ```
2. Open a terminal and navigate into the Blender installation directory (path varies by operating system):
    ```bash
   cd /path/to/blender/site-packages/
   ```
3. Create a `.pth` file named `FORG3D.pth` and add the absolute path to the `src` directory of the cloned repository:
   ```bash
   echo "/path/to/FORG3D/src" > /path/to/blender/site-packages/FORG3D.pth
   ```
    - _Note: if you encounter errors on Windows, ensure the file encoding is **UTF-8 with BOM**._
  
### Step 4: Load Preset Objects or Add Your Own

- We have created 21 preset objects available in [this repository](https://github.com/compling-wat/FORG3D-object-data). You can load them into your `data` directory by:
```bash
cd data
./load_objects.sh
```

- Alternatively, you can add your own objects by placing `.blend` files inside the `data/objaverse/shapes` folder and specifying their properties in `properties.json`.


## Usage

The repository contains a `scripts` folder with example shell scripts for using this tool. First **cd** into this directory. 

### **Camera Settings**

To set the camera configurations for the rendered images, you can add the following parameters to your script: 
  ```bash
  --camera-tilt X                             # Set camera tilt in degrees
  --camera-pan X                              # Set camera pan in degrees
  --camera-height X                           # Set camera height in meters
  --camera-focal-length X                     # Set focal length in millimeters
  ```

### **Rendering Multiple Images** 

To render all possible combinations of 2 objects under the `data` directory, use the `--render-random` parameter as shown in the `render_multiple.sh` script.
- The generates images into a **main directory** for each combination of 2 objects within into the **specified image output folder**, along with **4 subdirectories** within the **main directory**:

  - `[object1]_[object2]_left` (object2 to the left of object1)
  - `[object1]_[object2]_right` (object2 to the right of object1)
  - `[object1]_[object2]_front` (object2 to the front of object1)
  - `[object1]_[object2]_behind` (object2 to the back of object1)
 
- For each image, it also generates a corresponding `json` file with detailed information on the camera settings, and positions, rotations, orientations, and relative perspectives of the objects in the **specified scene output folder**.

- You can specify the following constraints:
  ```bash
  --objects [list of objects]    # Select specific objects to render
  --distance-between-objects X   # Set object distance in meters (default: 3)
  --max-images N                 # Set max images (orientations combinations) per subdirectory (default: 1)
  --max-camera-configs N         # Set max number of camera configurations per image (default: 1)
  ```

- If you do not specify `--objects`, the list of objects will be set to all objects in the `data` folder.
- If you do not specify `--max-camera-configs`, you must fix a specific camera configuration for all images in the script.

_This script can be used for generating an extensive **spatial reasoning dataset** for **vision-language models**._

### **Rendering a Single Image**

For controlled rendering of 2 selected objects, navigate to the `render_single.sh` script for an example usage. 

- Unlike rendering multiple

- Now, since you are only generating 1 image, you have the following additional customizations:
  ```bash
  --direction [left, right, behind, front]    # Set object 2’s position relative to object1
  --object1-rotation X                        # Set object 1's rotation to X degrees clockwise (default: 0)
  --object2-rotation X                        # Set object 2's rotation to X degrees clockwise (default: 0)
  ```

- In this case, you must specify a camera setting as well as the `--direction` parameter.
  
_This script is useful for **testing and fine-tuning** object placements before batch rendering._

### **Adding AI-generated Backgrounds (EXTRA)**

All the images rendered are just 2 objects on a white surface with a light grey "sky". If you would like to add a custom (more realistic) background to each image in your image output folder, you can navigate to the `generate_backgrounds.sh` script. Note: this feature is still under experimentation.

- Here, you can customize the `PROMPT` argument to guide the background generation process.

- The process utilizes the [**Stable Diffusion XL inpainting model**](https://huggingface.co/diffusers/stable-diffusion-xl-1.0-inpainting-0.1) to modify specific regions of images with custom backgrounds.

_The goal is to enable comparisons between a fine-tuned spatial reasoning model’s performance on the original dataset versus a version with more realistic backgrounds._

## Configuration

The tool's general settings, such as **output directories, image resolution, and other scene configurations**, can be customized in `config.json` under the `src` directory.
