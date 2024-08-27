"""
Title:        CreateTSSCI
Description:  This is the main script of TSSCI creation
Author:       Haim Fellner Cohen and Gal Zohar
Date:         2024-06-22
Version:      1.0
"""
# ----------------notes-------------------

# Add missing points ( need to determine that points with C 0.3 or lower are missing) -
# we took [x,y,z] from the left dot. if missing from the beginning we did nothing (?)
# We should consider to take from the left only in the same clique, like nose and eye.

# Convert keypoints by right hand method - skipped it for now

# ----------------Create TSSCI image from all skeletons-------------------

import glob
import json
import time
import numpy as np
from ImageToKeyPoints import faceToKP as fTkp
from videoToFrames import extract_frames as VTF
from PIL import Image
from TSSCI_MediaPlayer import loadImage as LI
import os
from pathlib import Path
import shutil

np.set_printoptions(suppress=True, precision=6)
# Get the current working directory
current_directory = Path.cwd()


def createFrames(videoName):
    frames_folder = os.path.join(current_directory, "frames")
    video_name_without_ext = os.path.splitext(videoName)[0]
    videoPath = os.path.join(current_directory, "videos", videoName)
    outputFolder = os.path.join(frames_folder, video_name_without_ext)
    VTF(videoPath, outputFolder)


def getJsons(videoFile_noExt):
    counter = 0
    # Create skeleton for all frames in the frames folder
    files = glob.glob(os.path.join(current_directory, "frames", videoFile_noExt, '*'))
    file_names = [os.path.basename(file_path) for file_path in files]
    # Process each file
    for file in file_names:
        fTkp(file, counter, videoFile_noExt)
        counter = counter + 1


def saveCopy(videoFile_noExt):
    # Define the current directory
    current_directory = os.getcwd()

    # Construct the source and destination paths
    src_path = os.path.join(current_directory, "jsons", videoFile_noExt)
    dest_path = os.path.join(current_directory, "jsons_copy", videoFile_noExt)

    # Check if the source directory exists
    if not os.path.exists(src_path):
        print(f"Source directory '{src_path}' does not exist.")
        return

    # Create the destination directory if it does not exist
    if not os.path.exists(dest_path):
        os.makedirs(dest_path)

    # Walk through the source directory
    for item in os.listdir(src_path):
        src_item = os.path.join(src_path, item)
        dest_item = os.path.join(dest_path, item)

        # If the item is a directory, recursively copy it
        if os.path.isdir(src_item):
            if not os.path.exists(dest_item):
                shutil.copytree(src_item, dest_item)
            else:
                # Recursively call saveCopy with new subdirectory name
                saveCopy(os.path.join(videoFile_noExt, item))
        else:
            # If the item is a file, copy it
            shutil.copy2(src_item, dest_item)


def getMaxXandY(videoFile_noExt):
    directory = os.path.join(current_directory, "jsons", videoFile_noExt)

    maxXval = float('-inf')
    maxYval = float('-inf')
    minXval = float('inf')
    minYval = float('inf')

    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            filepath = os.path.join(directory, filename)

            # Read the JSON file
            with open(filepath, 'r') as file:
                data = json.load(file)
                for person in data.get('people', []):
                    face_keypoints = person.get('face_keypoints_2d', [])
                    if face_keypoints:
                        # Convert the face keypoints to a NumPy array (reshaping to N x 3)
                        keypoints_array = np.array(face_keypoints).reshape(-1, 3).astype(float)

                        # Find and print max and min values
                        maxXval = max(maxXval, np.max(keypoints_array[:, 0]))
                        minXval = min(minXval, np.min(keypoints_array[:, 0]))
                        maxYval = max(maxYval, np.max(keypoints_array[:, 1]))
                        minYval = min(minYval, np.min(keypoints_array[:, 1]))

    return maxXval - minXval, maxYval - minYval, minXval, minYval


def normalaizeAllJsons(meanX, meanY, minXval, minYval, videoFile_noExt):
    json_folder = os.path.join(current_directory, "jsons", videoFile_noExt)
    # List all JSON files in the folder
    json_files = [pos_json for pos_json in os.listdir(json_folder) if pos_json.endswith('.json')]

    for file_name in json_files:
        file_path = os.path.join(json_folder, file_name)
        with open(file_path, 'r') as file:
            data = json.load(file)

        # Extract face keypoints
        if 'people' in data and len(data['people']) > 0:
            face_keypoints_2d = data['people'][0].get('face_keypoints_2d', [])

            # Normalize the face keypoints
            normalized_face_keypoints_2d = []
            for i in range(0, len(face_keypoints_2d), 3):
                xi = face_keypoints_2d[i]
                yi = face_keypoints_2d[i + 1]
                c = face_keypoints_2d[i + 2]

                # Avoid division by zero
                normalized_x = (xi - minXval) / meanX if meanX != 0 else 0
                normalized_y = (yi - minYval) / meanY if meanY != 0 else 0

                normalized_face_keypoints_2d.extend([normalized_x, normalized_y, c])

            # Update the data with normalized values
            data['people'][0]['face_keypoints_2d'] = normalized_face_keypoints_2d

            # Save the modified JSON back to the file
            with open(file_path, 'w') as file:
                json.dump(data, file, indent=4)


def runThroughJSONs(videoFile_noExt, method):
    directory = os.path.join(current_directory, "jsons", videoFile_noExt)

    # Process each JSON file in the directory
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            filepath = os.path.join(directory, filename)

            with open(filepath, 'r') as file:
                data = json.load(file)
                for person in data['people']:
                    if 'face_keypoints_2d' in person:
                        if method == 1:
                            person['face_keypoints_2d'] = compFromTheLeft(person['face_keypoints_2d'])
                        elif method == 2:
                            person['face_keypoints_2d'] = maze_right_hand_rule(person['face_keypoints_2d'])
            # Save the processed data back to the JSON file
            with open(filepath, 'w') as file:
                json.dump(data, file, indent=4)


def compFromTheLeft(keypoints, threshold=0.3):
    processed_keypoints = []
    last_valid_point = None

    for i in range(0, len(keypoints), 3):
        x, y, c = keypoints[i:i + 3]

        if c < threshold:
            if last_valid_point:
                processed_keypoints.extend(last_valid_point)
            else:
                processed_keypoints.extend([x, y, c])
        else:
            processed_keypoints.extend([x, y, c])
            last_valid_point = [x, y, c]

    return processed_keypoints


def maze_right_hand_rule(face_keypoints):
    processed_keypoints = []
    NEW_KEYPOINT_ORDER = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6,
                          5, 4, 3, 2, 1, 0, 17, 18, 19, 20, 21, 20, 19, 18, 17, 22, 23, 24, 25, 26, 25, 24, 23, 22, 27,
                          28, 29, 30, 29, 28, 27, 31, 32, 33, 34, 35, 34, 33, 32, 31, 36, 37, 38, 39, 40, 41, 42, 43,
                          44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66,
                          67, 68, 69]
    for i in NEW_KEYPOINT_ORDER:
        processed_keypoints.extend(face_keypoints[i * 3:i * 3 + 3])
    return processed_keypoints


def crt_TSSCI_from_jsons(videoFile_noExt):
    # Path to the folder containing JSON files
    folder_path = os.path.join(current_directory, "jsons", videoFile_noExt)

    # List to store the converted data
    data = []

    # Get list of JSON files containing keypoints and sort them numerically
    filenames = os.listdir(folder_path)
    keypoint_files = [f for f in filenames if f.endswith('_keypoints.json')]
    sorted_filenames = sorted(keypoint_files, key=lambda x: int(x.split('_')[0]))

    for file_name in sorted_filenames:
        file_path = os.path.join(folder_path, file_name)

        with open(file_path, 'r') as file:
            json_data = json.load(file)
            keypoints = json_data['people'][0].get('face_keypoints_2d', [])

            # Ensure the keypoints are in (x, y, c) triplets
            keypoints = [keypoints[i:i + 3] for i in range(0, len(keypoints), 3)]

            # Convert (x, y, c) values to RGB and store them in the list
            rgb_values = [(x * 255, y * 255, c * 255) for x, y, c in keypoints]
            data.append(rgb_values)

    # Determine the dimensions of the image
    height = len(data)
    width = len(data[0]) if data else 0  # Ensure width is defined even if data is empty

    # Create an empty image
    image = Image.new('RGB', (width, height), 0x000000)

    # Populate the image with the data
    for y, row in enumerate(data):
        for x, (x_val, y_val, c_val) in enumerate(row):
            # Original keypoints
            r, g, b = int(round(x_val)), int(round(y_val)), int(round(c_val))
            image.putpixel((x, y), (r, g, b))

    # Save the image
    image.save(os.path.join(current_directory, "TSSCI", videoFile_noExt + "TSSCI.png"))


# Function to read the processed videos from a config file
def read_processed_videos(config_path):
    if not os.path.exists(config_path):
        return set()
    with open(config_path, 'r') as file:
        return set(json.load(file))


# Function to write the processed videos to a config file
def write_processed_videos(config_path, processed_videos):
    with open(config_path, 'w') as file:
        json.dump(list(processed_videos), file)


def main():
    # Path to the directory containing videos
    jsons_directory = os.path.join(current_directory, "jsons")
    config_path = 'processed_videos.json'

    # Read the list of processed videos
    processed_videos = read_processed_videos(config_path)

    for subfolder in os.listdir(jsons_directory):
        subfolder_path = os.path.join(jsons_directory, subfolder)
        if not os.path.isdir(subfolder_path):
            continue
        if subfolder in processed_videos:
            print(f"Skipping already processed JSON file: {subfolder}")
            continue

        print(f"Starting processing of json: {subfolder}")


        # createFrames(video_file)  # create frames from video
        # getJsons(videoFile_noExt)  # json file for each frame of the video
        # saveCopy(videoFile_noExt)
        meanX, meanY, minXval, minYval = getMaxXandY(subfolder)  # max values from jsons file of the video
        normalaizeAllJsons(meanX, meanY, minXval, minYval, subfolder)  # normalize using max and min values
        runThroughJSONs(subfolder, 1)  # complementing from the left
        runThroughJSONs(subfolder, 2)  # right hand rule
        crt_TSSCI_from_jsons(subfolder)  # create TSSCI from the normalized jsons

        processed_videos.add(subfolder)
        write_processed_videos(config_path, processed_videos)

        print(f"Finished processing of video: {subfolder}")
        # time.sleep(20)
# LI()  # open the media player


if __name__ == "__main__":
    main()
