"""
Title:        CreateTSSCI
Description:  This is the main script of  TSSCI creation
Author:       Haim Fellner Cohen and Gal Zohar
Date:         2024-06-22
Version:      1.0
"""
# ----------------notes-------------------

# Add missing points ( need to determine that points with C 0.3 or lower are missing) -
# we took [x,y,z] from the left dot. if missing from the beggining we did nothing (?)
# We should consider to take from the left only in the same clique, like nose and eye.

# Convert keypoints by right hand method - skipped it for now

# ----------------Create TSSCI image from all skeletons-------------------

import glob
import json
import numpy as np
from ImageToKeyPoints import faceToKP as fTkp
from videoToFrames import extract_frames as VTF
from PIL import Image
from TSSCI_MediaPlayer import loadImage as LI
import os
from pathlib import Path
import time
from multiprocessing import Process
from datetime import datetime

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


def runThroughJSONs(videoFile_noExt):
    directory = os.path.join(current_directory, "jsons", videoFile_noExt)

    # Process each JSON file in the directory
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            filepath = os.path.join(directory, filename)

            with open(filepath, 'r') as file:
                data = json.load(file)
                for person in data['people']:
                    if 'face_keypoints_2d' in person:
                        person['face_keypoints_2d'] = compFromTheLeft(person['face_keypoints_2d'])

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


# Timer function to run in a separate process
def timer():
    start_time = time.time()
    while True:
        elapsed_time = time.time() - start_time
        print(f"Elapsed Time: {elapsed_time:.2f} seconds", end="\r")
        time.sleep(1)


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
    video_directory = os.path.join(current_directory, "videos")
    config_path = 'processed_videos.json'

    # Read the list of processed videos
    processed_videos = read_processed_videos(config_path)

    # Start the timer process
    timer_process = Process(target=timer)
    timer_process.start()

    for video_file in os.listdir(video_directory):
        if video_file.endswith('.mp4'):
            if video_file in processed_videos:
                print(f"Skipping already processed video: {video_file}")
                continue
            print(f"Starting processing of video: {video_file}")
            videoFile_noExt = os.path.splitext(video_file)[0]

            createFrames(video_file)  # create frames from video
            getJsons(videoFile_noExt)  # json file for each frame of the video
            meanX, meanY, minXval, minYval = getMaxXandY(videoFile_noExt)  # max values from jsons file of the video
            normalaizeAllJsons(meanX, meanY, minXval, minYval, videoFile_noExt)  # normalize using max and min values
            runThroughJSONs(videoFile_noExt)   # complementing from the left
            crt_TSSCI_from_jsons(videoFile_noExt)  # create TSSCI from the normalized jsons

            processed_videos.add(video_file)
            write_processed_videos(config_path, processed_videos)

            print(f"Finished processing of video: {video_file}")
    LI()  # open the media player
    # Terminate the timer process
    timer_process.terminate()


if __name__ == "__main__":
    main()
