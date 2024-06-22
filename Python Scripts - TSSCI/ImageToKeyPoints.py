"""
Title:        imageToKeyPoints
Description:  This script make JSON key point file from frame image.
              this is the second phase of createTSSCI project
Author:       Haim Fellner Cohen and Gal Zohar
Date:         2024-06-22
Version:      1.0
"""

import sys
import cv2
import os
from sys import platform
import argparse
from pathlib import Path

# Get the current working directory
current_directory = Path.cwd()


def faceToKP(fileName, counter, videoFile_noExt):
    try:
        openpose_dir = r"C:\Users\HaimT\openpose"  # Replace with the path to your OpenPose directory
        openpose_python_dir = os.path.join(openpose_dir, "buildNew/python")
        openpose_models_dir = os.path.join(openpose_dir, "models")
        try:
            if platform == "win32":
                # Set the paths for Windows
                sys.path.append(os.path.join(openpose_python_dir, "openpose/Release"))
                os.environ['PATH'] = os.environ['PATH'] + ';' + os.path.join(openpose_dir,
                                                                             "buildNew/x64/Release") + ';' + os.path.join(
                    openpose_dir, "buildNew/bin")
                import pyopenpose as op
            else:
                # Set the paths for Linux/OSX
                sys.path.append(openpose_python_dir)
                from openpose import pyopenpose as op
        except ImportError as e:
            print(
                'Error: OpenPose library could not be found. Did you enable `BUILD_PYTHON` in CMake and have this Python script in the right folder?')
            raise e

        # Flags
        parser = argparse.ArgumentParser()
        frame_folder = os.path.join(current_directory, "frames")
        parser.add_argument("--image_path",
                            default=os.path.join(frame_folder, videoFile_noExt, fileName),
                            help="Process an image. Read all standard formats (jpg, png, bmp, etc.).")
        args = parser.parse_known_args()

        father_folder = os.path.join(current_directory, "jsons")
        target_folder = os.path.join(father_folder, videoFile_noExt)
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)
        unique_folder = os.path.join(target_folder, "temp_jsons")
        if not os.path.exists(unique_folder):
            os.makedirs(unique_folder)

        # Custom Params (refer to include/openpose/flags.hpp for more parameters)
        params = dict()
        params["model_folder"] = openpose_models_dir
        params["face"] = True
        params["face_detector"] = 0
        params["body"] = 1
        params["write_json"] = unique_folder

        # Starting OpenPose
        opWrapper = op.WrapperPython()
        opWrapper.configure(params)
        opWrapper.start()

        # Read image and face rectangle locations
        imageToProcess = cv2.imread(args[0].image_path)

        # Create new datum
        datum = op.Datum()
        datum.cvInputData = imageToProcess
        # datum.faceRectangles = faceRectangles
        # Process and display image
        opWrapper.emplaceAndPop(op.VectorDatum([datum]))

        # Move JSON file to output directory with incremented filename
        json_file = os.path.join(unique_folder, '0_keypoints.json')
        target_file = os.path.join(target_folder, f"{counter}_keypoints.json")

        # Ensure unique filename
        while os.path.exists(target_file):
            newCounter = counter + 1
            target_file = os.path.join(target_folder, f"{newCounter}_keypoints.json")

        # Move the JSON file
        os.rename(json_file, target_file)

    except Exception as e:
        print(e)
        sys.exit(-1)
