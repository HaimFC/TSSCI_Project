"""
Title:        videoToFrmes
Description:  This script make frames from video.
              this is the first phase of createTSSCI project
Author:       Haim Fellner Cohen and Gal Zohar
Date:         2024-06-22
Version:      1.0
"""

import cv2
import os

# Function to extract frames
def extract_frames(video_path, output_folder):
    # Check if output folder exists, create if it doesn't
    if not os.path.exists(output_folder):
        os.makedirs(output_folder, mode=0o777, exist_ok=True)
    # Capture the video
    vidcap = cv2.VideoCapture(video_path)
    success, image = vidcap.read()
    count = 0

    while success:
        # Save frame as JPEG file
        frame_path = os.path.join(output_folder, f"frame_{count:04d}.jpg")
        cv2.imwrite(frame_path, image)
        success, image = vidcap.read()
        count += 1
    if count != 0:
        print(f"Extracted {count} frames from the video.")


# current_directory = Path.cwd()
# videoPath = os.path.join(current_directory, "video", 'firstOne.mp4')
# outputFolder = os.path.join(current_directory, "frames")
# extract_frames(videoPath, outputFolder)
