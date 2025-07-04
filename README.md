# TSSCI Project

<p align="center">
  <img src="readme\Title.png" alt="screenshot">
</p>

#### OpenPose

OpenPose is a real-time system that can detect and analyze human body movements by identifying key points on the human body, face, hands, and feet from images and videos. Developed by the Carnegie Mellon Perceptual Computing Lab, OpenPose uses deep learning to extract 2D and 3D pose information, capturing the spatial coordinates of key joints and body parts. This technology is widely used in fields like computer vision, motion analysis, gesture recognition, and augmented reality, enabling precise tracking of human motion for various applications.

<img src="readme/Logo_main_black.png" alt="Logo" width="100"/>

## TSSCI Tool
This Tool developed in order to create and disply TSSCI images. In the tool there are two tabs - "TSSCI creator" and "TSSCI Player".

### TSSCI Creator
The Time Series to Single Composite Image (TSSCI) Tool is designed to transform human motion captured in videos into a single composite image. This image representation condenses the spatial-temporal information of motion into a compact format, making it suitable for analysis using established computer vision techniques. Each TSSCI image is composed of pixel lines, with each line representing a frame from the video. The pixels encode the x and y coordinates of key points detected by OpenPose, along with their confidence levels.

This tool is particularly useful in applications such as motion classification, quality assessment, and synthesis of new motion sequences. The TSSCI format facilitates the efficient processing of motion data by converting the temporal evolution of movements into a static image, enabling deep learning models pre-trained on image data to analyze human motion.

### TSSCI Player
The TSSCI Player is a specialized media player designed to visualize TSSCI images. It can take a TSSCI image and plot graphs that represent the facial key points detected in the video. This feature allows for detailed exploration of facial expressions and movements encoded in the TSSCI format. By visualizing the spatial-temporal dynamics of facial motion, the player aids in analyzing and interpreting human expressions in a compact and efficient manner.

Both the TSSCI Creator and Player are designed to simplify and enhance the analysis of human motion, bridging the gap between temporal data and image-based deep learning techniques.

## Instructions

### Requirments
Installing OpenPose using this guide - [Open Pose Github](https://cmu-perceptual-computing-lab.github.io/openpose/web/html/doc/md_doc_installation_0_index.html). 

Python 3.7 or higher

### Installing instructions

Download all the scripts.
Make sure all the script are in the same videos folder (The same folder the will be chosen in next phase).

### running instructions
Open TSSCI_Tool.py using command line:

    python .\TSSCI_Tool.py
  
On the first Tab (TSSCI creator) - choose video path than method (using right hand or not) and click submit button.

On the second Tab (TSSCI player) - choose TSSCI images folder than click open player button.
