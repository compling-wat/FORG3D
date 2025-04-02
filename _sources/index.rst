FORG3D Rendering Tool Documentation
===================================

Welcome to the **FORG3D** (Flexible Object Rendering for Generation of 3D Vision-Language Spatial Reasoning Datasets) documentation.

.. toctree::
   :maxdepth: 2

   modules

Overview
--------

FORG3D is a 3D rendering tool that places two Blender objects in a customizable scene, allowing control over object positions, orientations, and camera configurations. It supports both single and batch image generation for research in spatial reasoning and AI vision tasks.

.. tip::

   Here is an example rendered scene, and the same scene with different camera configurations, different object rotations, and different relative positions:

.. raw:: html

   <div style="display: flex; justify-content: center; gap: 2%; flex-wrap: wrap;">
     <img src="_static/4.png" style="width: 22%;">
     <img src="_static/2.png" style="width: 22%;">
     <img src="_static/3.png" style="width: 22%;">
     <img src="_static/6.png" style="width: 22%;">
   </div>

.. tip::

   Here are some examples rendered scenes with various objects of various size groups:

.. raw:: html

   <div style="display: flex; justify-content: center; gap: 2%; flex-wrap: wrap;">
     <img src="_static/1.png" style="width: 22%;">
     <img src="_static/8.png" style="width: 22%;">
     <img src="_static/9.png" style="width: 22%;">
     <img src="_static/10.png" style="width: 22%;">
   </div>

Setup
-----

Clone the Repository
^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   git clone https://github.com/compling-wat/FORG3D.git
   cd FORG3D

Install Blender 4.3
^^^^^^^^^^^^^^^^^^^

Download and install `Blender 4.3 <https://www.blender.org/download/>`_ for your system.

Set Up the Environment
^^^^^^^^^^^^^^^^^^^^^^

1. Locate your Blender installation:

   .. code-block:: bash

      which blender   # or 'where blender' on Windows

2. Navigate into Blender's site-packages directory:

   .. code-block:: bash

      cd /path/to/blender/site-packages/

3. Create a `.pth` file named ``FORG3D.pth``:

   .. code-block:: bash

      echo "/path/to/FORG3D/src" > /path/to/blender/site-packages/FORG3D.pth

   .. note::
      On Windows, ensure the file is saved with **UTF-8 with BOM** encoding.

Load Preset Objects
^^^^^^^^^^^^^^^^^^^

Use the provided script to download and load 21 preset objects:

.. code-block:: bash

   cd data
   ./load_objects.sh

To add your own objects, place `.blend` files in ``data/objaverse/shapes/`` and register them in ``properties.json``.

Usage
-----

Scripts are located in the ``scripts`` folder. First navigate there:

.. code-block:: bash

   cd scripts

Camera Settings
^^^^^^^^^^^^^^^

You can set specific camera parameters in the rendering script:

.. code-block:: bash

   --camera-tilt X                # Tilt angle in degrees
   --camera-pan X                 # Pan angle in degrees
   --camera-height X              # Camera height in meters
   --camera-focal-length X        # Focal length in mm

Rendering Multiple Images
^^^^^^^^^^^^^^^^^^^^^^^^^

Use ``--render-random`` to generate multiple image combinations.

Each pair of objects will be rendered with the following directional subdirectories:

- ``[object1]_[object2]_left``
- ``[object1]_[object2]_right``
- ``[object1]_[object2]_front``
- ``[object1]_[object2]_behind``

Each image has an associated JSON metadata file describing camera settings and object configuration.

Additional flags:

.. code-block:: bash

   --objects [list]               # Specific objects to use
   --distance-between-objects X  # Distance in meters (default: 3)
   --max-images N                # Max images per subdirectory
   --max-camera-configs N        # Max camera configurations per image

.. note::
   If ``--objects`` is not specified, all objects in ``data/`` are used.
   If ``--max-camera-configs`` is not specified, a fixed camera config is required.

Rendering a Single Image
^^^^^^^^^^^^^^^^^^^^^^^^

Use ``render_single.sh`` for generating a controlled single image:

.. code-block:: bash

   --direction [left|right|behind|front]   # Position of object 2 relative to object 1
   --object1-rotation X                    # Rotation of object 1 (degrees clockwise)
   --object2-rotation X                    # Rotation of object 2 (degrees clockwise)

Camera settings and ``--direction`` must be provided.

This is ideal for debugging placements and testing scene composition.

Adding AI-generated Backgrounds (Experimental)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To enhance image realism, use ``generate_backgrounds.sh`` to add AI-generated backgrounds via the Stable Diffusion XL inpainting model:

Customize the background generation with the ``PROMPT`` variable.

.. tip::
   
   Here is an example of applying AI-generated backgrounds to a rendered scene:

.. raw:: html

   <div style="display: flex; justify-content: center; gap: 4%; flex-wrap: wrap;">
     <img src="_static/5.png" style="width: 22%;">
     <img src="_static/7.png" style="width: 22%;">
   </div>

.. note::
   This feature is experimental and intended for testing dataset robustness to background variation.

Configuration
-------------

General parameters such as output directories, resolution, and scene options are configured in ``src/config.json``.

License
-------

This project is licensed under the MIT License.